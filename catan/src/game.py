"""Authoritative Catan game engine.

All rule enforcement happens here. The server layer (Flask-SocketIO) should
never mutate game state directly - it only calls these methods, which return
``(ok, message)`` tuples and drive the ``TurnPhase`` state machine forward.
"""

from __future__ import annotations

import random
from collections import defaultdict
from typing import Optional

from catan.src.board import Board
from catan.src.components import (
    KnightCard,
    MonopolyCard,
    Resource,
    RoadBuildingCard,
    VictoryPointCard,
    YearOfPlentyCard,
)
from catan.src.phase import SETUP_PHASES, TurnPhase
from catan.src.player import Player

PLAYER_COLORS = ["red", "blue", "green", "orange"]
VICTORY_POINT_TARGET = 10


class Game:
    def __init__(self, player_names, is_bot_flags=None, seed=None):
        self._rng = random.Random(seed) if seed is not None else random
        self.board = Board(seed=seed)
        is_bot_flags = is_bot_flags or [False] * len(player_names)
        self.players = [
            Player(name, PLAYER_COLORS[i], is_bot=is_bot_flags[i])
            for i, name in enumerate(player_names)
        ]
        self.current_player_index = 0
        self.turn = 0
        self.phase = TurnPhase.SETUP_1
        self.log: list[str] = ["Game created."]
        self.dice_roll: Optional[int] = None
        self.longest_road_player: Optional[Player] = None
        self.largest_army_player: Optional[Player] = None
        self.winner: Optional[Player] = None
        # Setup tracking
        self._setup_order: list[int] = []  # queue of player indices for setup
        self._setup_phase_step: int = 0  # index into _setup_order
        self._setup_expects_road_for: Optional[int] = None
        self._setup_last_settlement: Optional[int] = None
        # Robber interactive state
        self.pending_discards: dict[str, int] = {}  # player_name -> count to discard
        self.robber_mover: Optional[Player] = None  # who is moving the robber
        self.pending_steal_targets: list[str] = []
        # Pending trade offers: id -> {from, to:[], offer, request, responses}
        self._next_trade_id = 1
        self.pending_trades: dict[int, dict] = {}
        # Development cards bought this turn (whole-player tracking) so we
        # can't buy and play on same turn.
        self._dev_card_played_this_turn = False
        self._create_development_card_deck()
        self._begin_setup()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _begin_setup(self):
        n = len(self.players)
        # Snake order: 0..n-1 then n-1..0
        self._setup_order = list(range(n)) + list(range(n - 1, -1, -1))
        self._setup_phase_step = 0
        self._setup_expects_road_for = None
        self.current_player_index = self._setup_order[0]
        self.phase = TurnPhase.SETUP_1

    @property
    def current_player(self) -> Player:
        return self.players[self.current_player_index]

    def place_setup_settlement(self, player: Player, vertex: int):
        if self.phase not in SETUP_PHASES:
            return False, "Not in setup phase"
        if player is not self.current_player:
            return False, "Not your turn"
        if self._setup_expects_road_for is not None:
            return False, "Place your road first"
        if not self._is_valid_settlement_location(player, vertex):
            return False, "Invalid settlement location"

        player.settlements.append(vertex)
        self._grant_harbor_if_any(player, vertex)
        self.log.append(f"{player.name} placed a settlement at vertex {vertex}.")
        self._setup_expects_road_for = vertex
        self._setup_last_settlement = vertex

        # If this is second setup round, grant resources for the new settlement.
        if self.phase == TurnPhase.SETUP_2:
            for tile in self.board.get_tiles_for_settlement(vertex):
                if tile.resource is not None:
                    player.resources[tile.resource] += 1

        return True, "ok"

    def place_setup_road(self, player: Player, edge):
        if self.phase not in SETUP_PHASES:
            return False, "Not in setup phase"
        if player is not self.current_player:
            return False, "Not your turn"
        if self._setup_expects_road_for is None:
            return False, "Place a settlement first"

        edge = self.board.normalised_edge(edge)
        v1, v2 = edge
        if not self.board.is_edge(edge):
            return False, "Not a valid edge"
        if self._setup_expects_road_for not in (v1, v2):
            return False, "Road must touch your new settlement"
        if self._edge_is_occupied(edge):
            return False, "Edge already has a road"
        if len(player.roads) >= Player.MAX_ROADS:
            return False, "Out of road pieces"

        player.roads.append(edge)
        self.log.append(f"{player.name} placed a road on {edge}.")
        self._update_longest_road(player)
        self._setup_expects_road_for = None
        self._advance_setup()
        return True, "ok"

    def _advance_setup(self):
        self._setup_phase_step += 1
        n = len(self.players)

        if self._setup_phase_step == n:
            # First round done; transition to second round (still starts with same player because snake).
            self.phase = TurnPhase.SETUP_2
        if self._setup_phase_step >= len(self._setup_order):
            # Setup complete
            self.phase = TurnPhase.ROLL
            self.current_player_index = 0
            self.turn = 1
            self.log.append("Setup complete. Game begins!")
            return

        self.current_player_index = self._setup_order[self._setup_phase_step]

    # ------------------------------------------------------------------
    # Turn / dice
    # ------------------------------------------------------------------

    def roll_dice(self, player: Player):
        if self.phase != TurnPhase.ROLL:
            return False, "Not in roll phase"
        if player is not self.current_player:
            return False, "Not your turn"

        die1 = self._rng.randint(1, 6)
        die2 = self._rng.randint(1, 6)
        roll = die1 + die2
        self.dice_roll = roll
        self.log.append(f"{player.name} rolled a {roll}.")

        if roll == 7:
            self._begin_seven_sequence()
        else:
            self.distribute_resources(roll)
            self.phase = TurnPhase.MAIN

        return True, roll

    def distribute_resources(self, roll: int):
        gains: dict[str, dict[Resource, int]] = defaultdict(lambda: defaultdict(int))
        for i, tile in enumerate(self.board.tiles):
            if i == self.board.robber_location:
                continue
            if tile.resource is None or tile.number != roll:
                continue

            vertices_on_tile = self.board.vertices_on_tile(i)
            for player in self.players:
                for s in player.settlements:
                    if s in vertices_on_tile:
                        gains[player.name][tile.resource] += 1
                for c in player.cities:
                    if c in vertices_on_tile:
                        gains[player.name][tile.resource] += 2

        if not gains:
            self.log.append("No resources produced.")
            return

        for player in self.players:
            if player.name in gains:
                parts = []
                for resource, amount in gains[player.name].items():
                    if amount > 0:
                        player.resources[resource] += amount
                        parts.append(f"{amount} {resource.name.lower()}")
                if parts:
                    self.log.append(f"{player.name} gained {', '.join(parts)}.")

    def end_turn(self, player: Player):
        if self.phase != TurnPhase.MAIN:
            return False, "Cannot end turn now"
        if player is not self.current_player:
            return False, "Not your turn"
        if self.dice_roll is None:
            return False, "You must roll the dice first"

        # Move new dev cards into playable hand
        player.development_cards.extend(player.new_development_cards)
        player.new_development_cards = []
        self._dev_card_played_this_turn = False

        if self._check_winner_and_maybe_end():
            return True, "game_over"

        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        self.turn += 1
        self.dice_roll = None
        self.phase = TurnPhase.ROLL
        return True, "ok"

    # ------------------------------------------------------------------
    # Seven / robber flow
    # ------------------------------------------------------------------

    def _begin_seven_sequence(self):
        self.log.append("A 7 was rolled!")
        self.pending_discards = {}
        for p in self.players:
            if p.total_resources > 7:
                self.pending_discards[p.name] = p.total_resources // 2
        if self.pending_discards:
            self.phase = TurnPhase.DISCARD
            names = ", ".join(
                f"{n} ({c})" for n, c in self.pending_discards.items()
            )
            self.log.append(f"Players must discard: {names}.")
        else:
            self.phase = TurnPhase.MOVE_ROBBER
            self.robber_mover = self.current_player

    def submit_discard(self, player: Player, resources_to_discard: dict[Resource, int]):
        if self.phase != TurnPhase.DISCARD:
            return False, "Not in discard phase"
        required = self.pending_discards.get(player.name)
        if required is None:
            return False, "You don't need to discard"
        if sum(resources_to_discard.values()) != required:
            return False, f"Must discard exactly {required} cards"
        for r, amt in resources_to_discard.items():
            if player.resources[r] < amt:
                return False, "Not enough of that resource"
        for r, amt in resources_to_discard.items():
            player.resources[r] -= amt
        self.log.append(f"{player.name} discarded {required} cards.")
        del self.pending_discards[player.name]
        if not self.pending_discards:
            self.phase = TurnPhase.MOVE_ROBBER
            self.robber_mover = self.current_player
        return True, "ok"

    def move_robber(self, player: Player, new_location: int):
        if self.phase != TurnPhase.MOVE_ROBBER:
            return False, "Not in move-robber phase"
        if self.robber_mover is not player:
            return False, "Not your robber move"
        if new_location == self.board.robber_location:
            return False, "Must move the robber to a different hex"
        if not (0 <= new_location < len(self.board.tiles)):
            return False, "Invalid hex"

        self.board.robber_location = new_location
        self.log.append(f"{player.name} moved the robber to hex {new_location}.")

        # Figure out which opponents have settlements/cities on that hex.
        vertices = set(self.board.vertices_on_tile(new_location))
        targets: list[str] = []
        for p in self.players:
            if p is player:
                continue
            if p.total_resources == 0:
                continue
            if any(v in vertices for v in p.settlements + p.cities):
                targets.append(p.name)
        self.pending_steal_targets = targets

        if not targets:
            self.log.append("No one to steal from.")
            self.phase = TurnPhase.MAIN
            self.robber_mover = None
        elif len(targets) == 1:
            self._perform_steal(player, targets[0])
            self.phase = TurnPhase.MAIN
            self.robber_mover = None
        else:
            self.phase = TurnPhase.ROBBER_STEAL
        return True, "ok"

    def steal_from(self, player: Player, target_name: str):
        if self.phase != TurnPhase.ROBBER_STEAL:
            return False, "Not in steal phase"
        if self.robber_mover is not player:
            return False, "Not your steal"
        if target_name not in self.pending_steal_targets:
            return False, "Invalid steal target"
        self._perform_steal(player, target_name)
        self.phase = TurnPhase.MAIN
        self.robber_mover = None
        self.pending_steal_targets = []
        return True, "ok"

    def _perform_steal(self, stealer: Player, target_name: str):
        target = self.get_player(target_name)
        if target is None:
            return
        available = [r for r, c in target.resources.items() if c > 0]
        if not available:
            self.log.append(f"{target.name} had nothing to steal.")
            return
        resource = self._rng.choice(available)
        target.resources[resource] -= 1
        stealer.resources[resource] += 1
        self.log.append(f"{stealer.name} stole a card from {target.name}.")

    # ------------------------------------------------------------------
    # Building
    # ------------------------------------------------------------------

    def _is_valid_settlement_location(self, player, vertex):
        # Must be a known vertex
        if vertex < 0 or vertex >= 54:
            return False
        # Vertex must not be occupied
        for p in self.players:
            if vertex in p.settlements or vertex in p.cities:
                return False
        # Distance rule
        neighbours = self.board.vertex_neighbors(vertex)
        for p in self.players:
            for occ in p.settlements + p.cities:
                if occ in neighbours:
                    return False
        return True

    def _edge_is_occupied(self, edge):
        edge = self.board.normalised_edge(edge)
        for p in self.players:
            for r in p.roads:
                if self.board.normalised_edge(r) == edge:
                    return True
        return False

    def _player_connects_to_edge(self, player: Player, edge):
        """In normal play a road must connect to one of the player's roads or
        buildings, and cannot cross through an opponent's settlement."""
        edge = self.board.normalised_edge(edge)
        v1, v2 = edge

        def opponent_building_at(v):
            for p in self.players:
                if p is player:
                    continue
                if v in p.settlements or v in p.cities:
                    return True
            return False

        touches_own_building = v1 in player.settlements + player.cities or v2 in player.settlements + player.cities
        if touches_own_building:
            return True

        own_edges = {self.board.normalised_edge(r) for r in player.roads}
        for endpoint in (v1, v2):
            if opponent_building_at(endpoint):
                continue
            # If any of our roads ends at this endpoint, we can extend from it.
            for oe in own_edges:
                if endpoint in oe and oe != edge:
                    return True
        return False

    def build_road(self, player: Player, edge, is_setup: bool = False):
        edge = self.board.normalised_edge(edge)
        if not self.board.is_edge(edge):
            return False, "Not a valid edge"
        if self._edge_is_occupied(edge):
            return False, "Edge already has a road"
        if len(player.roads) >= Player.MAX_ROADS:
            return False, "Out of road pieces"

        if not is_setup:
            if self.phase != TurnPhase.MAIN or player is not self.current_player:
                return False, "Cannot build now"
            if not self._player_connects_to_edge(player, edge):
                return False, "Road must connect to your network"
            if player.resources[Resource.BRICK] < 1 or player.resources[Resource.LUMBER] < 1:
                return False, "Not enough resources"
            player.resources[Resource.BRICK] -= 1
            player.resources[Resource.LUMBER] -= 1
        player.roads.append(edge)
        self.log.append(f"{player.name} built a road on {edge}.")
        self._update_longest_road(player)
        return True, "ok"

    def build_settlement(self, player: Player, vertex: int, is_setup: bool = False):
        if not self._is_valid_settlement_location(player, vertex):
            return False, "Invalid settlement location"
        if len(player.settlements) >= Player.MAX_SETTLEMENTS:
            return False, "Out of settlement pieces"

        if not is_setup:
            if self.phase != TurnPhase.MAIN or player is not self.current_player:
                return False, "Cannot build now"
            # Must connect to one of this player's roads
            own_edges = {self.board.normalised_edge(r) for r in player.roads}
            if not any(vertex in e for e in own_edges):
                return False, "Settlement must be on your road network"
            costs = [Resource.BRICK, Resource.LUMBER, Resource.WOOL, Resource.GRAIN]
            for c in costs:
                if player.resources[c] < 1:
                    return False, "Not enough resources"
            for c in costs:
                player.resources[c] -= 1

        player.settlements.append(vertex)
        self._grant_harbor_if_any(player, vertex)
        self.log.append(f"{player.name} built a settlement at {vertex}.")
        # Settlements can break an opponent's longest road.
        for p in self.players:
            self._update_longest_road(p)
        return True, "ok"

    def _grant_harbor_if_any(self, player: Player, vertex: int):
        for harbor in self.board.harbors:
            if harbor.location and vertex in harbor.location:
                if harbor not in player.harbors:
                    player.harbors.append(harbor)

    def build_city(self, player: Player, vertex: int):
        if self.phase != TurnPhase.MAIN or player is not self.current_player:
            return False, "Cannot build now"
        if vertex not in player.settlements:
            return False, "Must upgrade an existing settlement"
        if len(player.cities) >= Player.MAX_CITIES:
            return False, "Out of city pieces"
        if player.resources[Resource.GRAIN] < 2 or player.resources[Resource.ORE] < 3:
            return False, "Not enough resources"

        player.resources[Resource.GRAIN] -= 2
        player.resources[Resource.ORE] -= 3
        player.settlements.remove(vertex)
        player.cities.append(vertex)
        self.log.append(f"{player.name} built a city at {vertex}.")
        return True, "ok"

    # ------------------------------------------------------------------
    # Trading
    # ------------------------------------------------------------------

    def offer_trade(self, from_player: Player, to_player_names: list[str], offer: dict[Resource, int], request: dict[Resource, int]):
        if self.phase != TurnPhase.MAIN or from_player is not self.current_player:
            return False, "Cannot trade now"
        if sum(offer.values()) == 0 or sum(request.values()) == 0:
            return False, "Trade must include offer and request"
        for r, a in offer.items():
            if from_player.resources[r] < a:
                return False, "Not enough resources to offer"
        trade_id = self._next_trade_id
        self._next_trade_id += 1
        self.pending_trades[trade_id] = {
            "id": trade_id,
            "from": from_player.name,
            "to": list(to_player_names),
            "offer": {r.name: a for r, a in offer.items() if a > 0},
            "request": {r.name: a for r, a in request.items() if a > 0},
            "responses": {},
        }
        self.log.append(f"{from_player.name} offered a trade.")
        return True, trade_id

    def respond_trade(self, trade_id: int, responder: Player, accept: bool):
        trade = self.pending_trades.get(trade_id)
        if trade is None:
            return False, "Trade not found"
        if responder.name not in trade["to"]:
            return False, "Not in this trade"
        trade["responses"][responder.name] = accept
        return True, "ok"

    def accept_trade(self, trade_id: int, accepter: Player):
        trade = self.pending_trades.get(trade_id)
        if trade is None:
            return False, "Trade not found"
        if accepter.name not in trade["to"]:
            return False, "Not in this trade"
        from_player = self.get_player(trade["from"])
        if from_player is None:
            return False, "Offering player gone"
        offer = {Resource[r]: a for r, a in trade["offer"].items()}
        request = {Resource[r]: a for r, a in trade["request"].items()}
        for r, a in offer.items():
            if from_player.resources[r] < a:
                return False, "Offerer no longer has resources"
        for r, a in request.items():
            if accepter.resources[r] < a:
                return False, "You lack the requested resources"

        for r, a in offer.items():
            from_player.resources[r] -= a
            accepter.resources[r] += a
        for r, a in request.items():
            accepter.resources[r] -= a
            from_player.resources[r] += a

        self.log.append(f"{from_player.name} traded with {accepter.name}.")
        del self.pending_trades[trade_id]
        return True, "ok"

    def cancel_trade(self, trade_id: int, player: Player):
        trade = self.pending_trades.get(trade_id)
        if trade is None:
            return False, "Trade not found"
        if player.name != trade["from"]:
            return False, "Only offerer can cancel"
        del self.pending_trades[trade_id]
        return True, "ok"

    def maritime_trade(self, player: Player, resource_to_give: Resource, resource_to_get: Resource):
        if self.phase != TurnPhase.MAIN or player is not self.current_player:
            return False, "Cannot trade now"
        if resource_to_give == resource_to_get:
            return False, "Must differ"
        trade_ratio = 4
        for harbor in player.harbors:
            if harbor.resource is None:
                trade_ratio = min(trade_ratio, 3)
            elif harbor.resource == resource_to_give:
                trade_ratio = min(trade_ratio, 2)
        if player.resources[resource_to_give] < trade_ratio:
            return False, f"Need {trade_ratio} to trade"
        player.resources[resource_to_give] -= trade_ratio
        player.resources[resource_to_get] += 1
        self.log.append(
            f"{player.name} maritime-traded {trade_ratio} "
            f"{resource_to_give.name.lower()} for 1 {resource_to_get.name.lower()}."
        )
        return True, trade_ratio

    # ------------------------------------------------------------------
    # Development cards
    # ------------------------------------------------------------------

    def _create_development_card_deck(self):
        self.development_card_deck = []
        for _ in range(14):
            self.development_card_deck.append(KnightCard())
        for _ in range(5):
            self.development_card_deck.append(VictoryPointCard())
        for _ in range(2):
            self.development_card_deck.append(MonopolyCard())
            self.development_card_deck.append(RoadBuildingCard())
            self.development_card_deck.append(YearOfPlentyCard())
        self._rng.shuffle(self.development_card_deck)

    def buy_development_card(self, player: Player):
        if self.phase != TurnPhase.MAIN or player is not self.current_player:
            return False, "Cannot buy now"
        if not self.development_card_deck:
            return False, "No cards left"
        if (
            player.resources[Resource.ORE] < 1
            or player.resources[Resource.WOOL] < 1
            or player.resources[Resource.GRAIN] < 1
        ):
            return False, "Not enough resources"
        player.resources[Resource.ORE] -= 1
        player.resources[Resource.WOOL] -= 1
        player.resources[Resource.GRAIN] -= 1
        card = self.development_card_deck.pop()
        player.new_development_cards.append(card)
        self.log.append(f"{player.name} bought a development card.")
        return True, "ok"

    def play_development_card(self, player: Player, card_kind: str, **kwargs):
        if self.phase != TurnPhase.MAIN or player is not self.current_player:
            return False, "Cannot play now"
        if self._dev_card_played_this_turn and card_kind != "victory_point":
            return False, "Already played a dev card this turn"

        # Find a playable card of this kind (not bought this turn)
        card = next(
            (c for c in player.development_cards if c.kind == card_kind),
            None,
        )
        if card is None:
            return False, "You don't have that card"

        if card_kind == "knight":
            player.development_cards.remove(card)
            player.knights += 1
            self._update_largest_army(player)
            self.log.append(f"{player.name} played a Knight.")
            # Enter robber flow but skip discard (knights don't trigger discard)
            self.phase = TurnPhase.MOVE_ROBBER
            self.robber_mover = player
            self._dev_card_played_this_turn = True
            return True, "ok"

        if card_kind == "monopoly":
            resource_name = kwargs.get("resource")
            try:
                resource = Resource[resource_name]
            except (KeyError, TypeError):
                return False, "Invalid resource"
            total = 0
            for p in self.players:
                if p is player:
                    continue
                total += p.resources[resource]
                p.resources[resource] = 0
            player.resources[resource] += total
            player.development_cards.remove(card)
            self.log.append(
                f"{player.name} played Monopoly on {resource.name.lower()} (+{total})."
            )
            self._dev_card_played_this_turn = True
            return True, "ok"

        if card_kind == "year_of_plenty":
            try:
                r1 = Resource[kwargs["resource1"]]
                r2 = Resource[kwargs["resource2"]]
            except (KeyError, TypeError):
                return False, "Invalid resources"
            player.resources[r1] += 1
            player.resources[r2] += 1
            player.development_cards.remove(card)
            self.log.append(
                f"{player.name} played Year of Plenty ({r1.name.lower()} + {r2.name.lower()})."
            )
            self._dev_card_played_this_turn = True
            return True, "ok"

        if card_kind == "road_building":
            edge1 = kwargs.get("edge1")
            edge2 = kwargs.get("edge2")
            if edge1 is None or edge2 is None:
                return False, "Must specify two edges"
            # Place both as 'setup' (free) roads but run connectivity check manually
            edge1 = self.board.normalised_edge(edge1)
            edge2 = self.board.normalised_edge(edge2)
            if edge1 == edge2:
                return False, "Edges must be different"
            for edge in (edge1, edge2):
                if not self.board.is_edge(edge):
                    return False, "Invalid edge"
                if self._edge_is_occupied(edge):
                    return False, "Edge already has a road"
            # Temporarily place first road so second road's connectivity check can see it.
            if not self._player_connects_to_edge(player, edge1):
                return False, "First road must connect to your network"
            player.roads.append(edge1)
            if not self._player_connects_to_edge(player, edge2):
                player.roads.pop()
                return False, "Second road must connect to your network"
            player.roads.append(edge2)
            self._update_longest_road(player)
            player.development_cards.remove(card)
            self.log.append(f"{player.name} played Road Building.")
            self._dev_card_played_this_turn = True
            return True, "ok"

        if card_kind == "victory_point":
            # Normally kept hidden and only revealed on the winning turn.
            # We let the player reveal it explicitly; it will count toward public VP.
            player.played_victory_point_cards += 1
            player.development_cards.remove(card)
            self.log.append(f"{player.name} revealed a Victory Point card.")
            return True, "ok"

        return False, "Unknown card kind"

    # ------------------------------------------------------------------
    # Longest Road / Largest Army
    # ------------------------------------------------------------------

    def _calculate_longest_road(self, player: Player) -> int:
        if not player.roads:
            return 0
        # Build adjacency restricted to this player's roads, minus any vertex
        # occupied by an opponent settlement/city (which breaks the chain).
        opp_vertices = set()
        for p in self.players:
            if p is player:
                continue
            opp_vertices.update(p.settlements)
            opp_vertices.update(p.cities)

        edges = [self.board.normalised_edge(e) for e in player.roads]
        adj = defaultdict(list)
        for a, b in edges:
            adj[a].append((b, (a, b)))
            adj[b].append((a, (a, b)))

        best = 0

        def dfs(node, used_edges):
            nonlocal best
            best = max(best, len(used_edges))
            if node in opp_vertices and used_edges:
                return  # Can't traverse through opponent building
            for nxt, eid in adj[node]:
                if eid in used_edges:
                    continue
                used_edges.add(eid)
                dfs(nxt, used_edges)
                used_edges.remove(eid)

        for start in list(adj.keys()):
            dfs(start, set())
        return best

    def _update_longest_road(self, player: Player):
        length = self._calculate_longest_road(player)
        if length < 5:
            # Current holder might lose it if their road was broken below 5
            if self.longest_road_player is player:
                self.longest_road_player.has_longest_road = False
                self.longest_road_player = None
            return
        if self.longest_road_player is None:
            self.longest_road_player = player
            player.has_longest_road = True
            self.log.append(f"{player.name} claims Longest Road.")
            return
        current_len = self._calculate_longest_road(self.longest_road_player)
        if length > current_len and player is not self.longest_road_player:
            self.longest_road_player.has_longest_road = False
            self.longest_road_player = player
            player.has_longest_road = True
            self.log.append(f"{player.name} takes Longest Road.")

    def _update_largest_army(self, player: Player):
        if player.knights < 3:
            return
        if self.largest_army_player is None:
            self.largest_army_player = player
            player.has_largest_army = True
            self.log.append(f"{player.name} claims Largest Army.")
            return
        if (
            player is not self.largest_army_player
            and player.knights > self.largest_army_player.knights
        ):
            self.largest_army_player.has_largest_army = False
            self.largest_army_player = player
            player.has_largest_army = True
            self.log.append(f"{player.name} takes Largest Army.")

    # ------------------------------------------------------------------
    # Winner / utility
    # ------------------------------------------------------------------

    def _check_winner_and_maybe_end(self) -> bool:
        for p in self.players:
            if p.victory_points >= VICTORY_POINT_TARGET:
                self.winner = p
                self.phase = TurnPhase.GAME_OVER
                self.log.append(f"{p.name} wins with {p.victory_points} VP!")
                return True
        return False

    def check_for_winner(self):
        for p in self.players:
            if p.victory_points >= VICTORY_POINT_TARGET:
                return p
        return None

    def get_player(self, name: str) -> Optional[Player]:
        return next((p for p in self.players if p.name == name), None)

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self, viewer_name: Optional[str] = None) -> dict:
        """Serialise game for client.

        If ``viewer_name`` is given, only that player's resources/dev cards are
        revealed in full; others show only aggregated counts.
        """
        players_dict = {}
        for p in self.players:
            is_viewer = (viewer_name is not None and p.name == viewer_name)
            entry: dict = {
                "name": p.name,
                "color": p.color,
                "is_bot": p.is_bot,
                "connected": p.connected,
                "settlements": list(p.settlements),
                "cities": list(p.cities),
                "roads": [list(r) for r in p.roads],
                "public_victory_points": p.public_victory_points,
                "knights": p.knights,
                "has_longest_road": p.has_longest_road,
                "has_largest_army": p.has_largest_army,
                "resource_count": p.total_resources,
                "dev_card_count": len(p.development_cards) + len(p.new_development_cards),
                "harbors": [h.to_dict() for h in p.harbors],
            }
            if is_viewer:
                entry["resources"] = {r.name: p.resources[r] for r in Resource}
                entry["development_cards"] = [c.to_dict() for c in p.development_cards]
                entry["new_development_cards"] = [c.to_dict() for c in p.new_development_cards]
                entry["victory_points"] = p.victory_points
            players_dict[p.name] = entry

        return {
            "phase": self.phase.value,
            "turn": self.turn,
            "current_player": self.current_player.name,
            "current_player_index": self.current_player_index,
            "dice_roll": self.dice_roll,
            "winner": self.winner.name if self.winner else None,
            "players": players_dict,
            "player_order": [p.name for p in self.players],
            "board": {
                "tiles": [
                    {
                        "resource": tile.resource.name if tile.resource else "DESERT",
                        "number": tile.number,
                    }
                    for tile in self.board.tiles
                ],
                "robber_location": self.board.robber_location,
                "tile_to_vertices": {str(k): v for k, v in self.board.tile_to_vertices.items()},
                "harbors": [h.to_dict() for h in self.board.harbors],
                "edges": [list(e) for e in sorted(self.board.edges)],
            },
            "setup": {
                "expects_road_for": self._setup_expects_road_for,
                "step": self._setup_phase_step,
                "order": [self.players[i].name for i in self._setup_order],
            }
            if self.phase in SETUP_PHASES
            else None,
            "pending_discards": dict(self.pending_discards),
            "pending_steal_targets": list(self.pending_steal_targets),
            "pending_trades": [
                {
                    "id": t["id"],
                    "from": t["from"],
                    "to": t["to"],
                    "offer": t["offer"],
                    "request": t["request"],
                    "responses": t["responses"],
                }
                for t in self.pending_trades.values()
            ],
            "dev_card_deck_count": len(self.development_card_deck),
            "log": list(self.log),
        }
