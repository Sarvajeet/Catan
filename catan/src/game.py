from collections import defaultdict
import random
from catan.src.board import Board
from catan.src.player import Player
from catan.src.components import (
    Resource,
    KnightCard,
    VictoryPointCard,
    MonopolyCard,
    RoadBuildingCard,
    YearOfPlentyCard,
)

class Game:
    def __init__(self, player_names):
        self.board = Board()
        self.players = [Player(name, color) for name, color in zip(player_names, ["red", "blue", "green", "yellow"])]
        self.current_player_index = 0
        self.turn = 0
        self.longest_road_player = None
        self.largest_army_player = None
        self._create_development_card_deck()

    @property
    def current_player(self):
        return self.players[self.current_player_index]

    def start_game(self, initial_placements):
        # Initial setup phase
        # First round of placements
        for i in range(len(self.players)):
            player = self.players[i]
            settlement_loc = initial_placements[i]["settlement"]
            road_loc = initial_placements[i]["road"]
            self.build_settlement(player, settlement_loc, is_setup=True)
            self.build_road(player, road_loc, is_setup=True)

        # Second round of placements (in reverse order)
        for i in range(len(self.players) - 1, -1, -1):
            player = self.players[i]
            settlement_loc = initial_placements[len(self.players) + i]["settlement"]
            road_loc = initial_placements[len(self.players) + i]["road"]
            self.build_settlement(player, settlement_loc, is_setup=True)
            self.build_road(player, road_loc, is_setup=True)
            # Distribute resources for the second settlement
            tiles = self.board.get_tiles_for_settlement(settlement_loc)
            for tile in tiles:
                if tile.resource:
                    player.resources[tile.resource] += 1

        self.turn = 1

    def roll_dice(self):
        if self.turn == 0:
            return  # Can't roll dice before the game has started

        die1 = random.randint(1, 6)
        die2 = random.randint(1, 6)
        roll = die1 + die2

        if roll == 7:
            # Handle robber logic
            self.handle_robber()
        else:
            self.distribute_resources(roll)

        return roll

    def handle_robber(self):
        # This is a placeholder for the full robber logic, which will require
        # player input. For now, it just moves the robber randomly.
        # Players with more than 7 cards must discard half
        for player in self.players:
            if sum(player.resources.values()) > 7:
                self.force_discard(player)

        # The current player moves the robber. This part will need to be
        # integrated with the UI to get player input.
        # For now, let's say the robber is moved to a random tile.
        new_robber_location = random.randint(0, len(self.board.tiles) - 1)
        while new_robber_location == self.board.robber_location:
            new_robber_location = random.randint(0, len(self.board.tiles) - 1)

        self.move_robber(self.current_player, new_robber_location)


    def move_robber(self, player, new_location, target_player=None):
        if new_location == self.board.robber_location:
            return False  # Must move the robber to a new tile
        self.board.robber_location = new_location

        if target_player:
            # Check if the target player is adjacent to the new location
            adjacent_players = self.get_players_on_tile(new_location)
            if target_player in adjacent_players:
                self.steal_resource(player, target_player)
            else:
                return False
        return True

    def force_discard(self, player):
        # This is a simplified version. In a real game, the player would choose
        # which cards to discard.
        num_to_discard = sum(player.resources.values()) // 2
        discarded_resources = []
        for resource, count in player.resources.items():
            for _ in range(count):
                discarded_resources.append(resource)

        for _ in range(num_to_discard):
            if not discarded_resources:
                break
            resource_to_discard = random.choice(discarded_resources)
            player.resources[resource_to_discard] -= 1
            discarded_resources.remove(resource_to_discard)


    def steal_resource(self, stealer, target):
        # This is a simplified version. The stealer would randomly take one card.
        available_resources = [r for r, c in target.resources.items() if c > 0]
        if available_resources:
            resource_to_steal = random.choice(available_resources)
            target.resources[resource_to_steal] -= 1
            stealer.resources[resource_to_steal] += 1

    def get_players_on_tile(self, tile_index):
        players_on_tile = []
        vertices = self.board.tile_to_vertices.get(tile_index, [])
        for player in self.players:
            for settlement_loc in player.settlements + player.cities:
                if settlement_loc in vertices and player not in players_on_tile:
                    players_on_tile.append(player)
        return players_on_tile

    def distribute_resources(self, roll):
        for i, tile in enumerate(self.board.tiles):
            if i == self.board.robber_location:
                continue  # No resources from the tile with the robber

            if tile.number == roll:
                for player in self.players:
                    for settlement in player.settlements:
                        # Check if the settlement is adjacent to the tile
                        if tile in self.board.get_tiles_for_settlement(settlement):
                            player.resources[tile.resource] += 1
                    for city in player.cities:
                        # Check if the city is adjacent to the tile
                        if tile in self.board.get_tiles_for_settlement(city):
                            player.resources[tile.resource] += 2

    def next_turn(self):
        # Move new development cards to the player's hand
        self.current_player.development_cards.extend(self.current_player.new_development_cards)
        self.current_player.new_development_cards = []

        self.check_for_winner()

        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        self.turn += 1

    def trade(self, offering_player, receiving_player, offered_resources, requested_resources):
        # Check if the offering player has the resources to trade
        for resource, amount in offered_resources.items():
            if offering_player.resources[resource] < amount:
                return False

        # Check if the receiving player has the resources to trade
        for resource, amount in requested_resources.items():
            if receiving_player.resources[resource] < amount:
                return False

        # Perform the trade
        for resource, amount in offered_resources.items():
            offering_player.resources[resource] -= amount
            receiving_player.resources[resource] += amount

        for resource, amount in requested_resources.items():
            receiving_player.resources[resource] -= amount
            offering_player.resources[resource] += amount

        return True

    def _is_valid_settlement_location(self, player, location):
        # Check if the location is already occupied
        for p in self.players:
            if location in p.settlements or location in p.cities:
                return False

        # Check the distance rule
        for p in self.players:
            for settlement_loc in p.settlements + p.cities:
                # Check for adjacent vertices
                if location in self.board.graph.getVertex(settlement_loc).getConnections():
                    return False
        return True

    def build_road(self, player, location, is_setup=False):
        if not is_setup:
            # Check for resources (1 brick, 1 lumber)
            if player.resources[Resource.BRICK] < 1 or player.resources[Resource.LUMBER] < 1:
                return False
            player.resources[Resource.BRICK] -= 1
            player.resources[Resource.LUMBER] -= 1

        # Check for valid road placement
        v1, v2 = location
        if not (v1 in player.settlements or v2 in player.settlements or
                any(v1 in r for r in player.roads) or any(v2 in r for r in player.roads)):
            return False

        player.roads.append(location)
        self._update_longest_road(player)
        return True

    def build_settlement(self, player, location, is_setup=False):
        if not self._is_valid_settlement_location(player, location):
            return False

        if not is_setup:
            # Check for resources (1 brick, 1 lumber, 1 wool, 1 grain)
            if (player.resources[Resource.BRICK] < 1 or player.resources[Resource.LUMBER] < 1 or
                    player.resources[Resource.WOOL] < 1 or player.resources[Resource.GRAIN] < 1):
                return False
            player.resources[Resource.BRICK] -= 1
            player.resources[Resource.LUMBER] -= 1
            player.resources[Resource.WOOL] -= 1
            player.resources[Resource.GRAIN] -= 1

        player.settlements.append(location)

        # Check for harbors
        for harbor in self.board.harbors:
            if location in harbor.location:
                player.harbors.append(harbor)

        return True

    def build_city(self, player, location):
        if location not in player.settlements:
            return False  # Must build on an existing settlement

        # Check for resources (2 wheat, 3 ore)
        if player.resources[Resource.GRAIN] < 2 or player.resources[Resource.ORE] < 3:
            return False
        player.resources[Resource.GRAIN] -= 2
        player.resources[Resource.ORE] -= 3

        player.settlements.remove(location)
        player.cities.append(location)
        return True

    def maritime_trade(self, player, resource_to_give, resource_to_get):
        # Check for the best trade ratio for the resource to give
        trade_ratio = 4  # Default ratio
        for harbor in player.harbors:
            if harbor.resource is None:  # 3:1 harbor
                trade_ratio = min(trade_ratio, 3)
            elif harbor.resource == resource_to_give:  # 2:1 harbor
                trade_ratio = min(trade_ratio, 2)

        if player.resources[resource_to_give] < trade_ratio:
            return False

        player.resources[resource_to_give] -= trade_ratio
        player.resources[resource_to_get] += 1
        return True

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
        random.shuffle(self.development_card_deck)

    def buy_development_card(self, player):
        # Check for resources (1 ore, 1 wool, 1 grain)
        if (player.resources[Resource.ORE] < 1 or
                player.resources[Resource.WOOL] < 1 or
                player.resources[Resource.GRAIN] < 1):
            return False

        if not self.development_card_deck:
            return False # No more cards left

        player.resources[Resource.ORE] -= 1
        player.resources[Resource.WOOL] -= 1
        player.resources[Resource.GRAIN] -= 1

        card = self.development_card_deck.pop()
        player.new_development_cards.append(card)
        return True

    def play_development_card(self, player, card, **kwargs):
        if card not in player.development_cards:
            return False # Player doesn't have this card

        if isinstance(card, KnightCard):
            player.knights += 1
            self.move_robber(player, kwargs['new_location'], kwargs.get('target_player'))
            self._update_largest_army(player)
        elif isinstance(card, VictoryPointCard):
            # Victory points are hidden until the end of the game
            # We will handle this in the game end condition
            pass
        elif isinstance(card, MonopolyCard):
            resource = kwargs['resource']
            total_stolen = 0
            for p in self.players:
                if p != player:
                    amount = p.resources[resource]
                    p.resources[resource] = 0
                    total_stolen += amount
            player.resources[resource] += total_stolen
        elif isinstance(card, RoadBuildingCard):
            self.build_road(player, kwargs['road1_loc'], is_setup=True)
            self.build_road(player, kwargs['road2_loc'], is_setup=True)
        elif isinstance(card, YearOfPlentyCard):
            player.resources[kwargs['resource1']] += 1
            player.resources[kwargs['resource2']] += 1

        player.development_cards.remove(card)
        return True

    def next_turn(self):
        # Move new development cards to the player's hand
        self.current_player.development_cards.extend(self.current_player.new_development_cards)
        self.current_player.new_development_cards = []

        self.check_for_winner()

        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        self.turn += 1

    def trade(self, offering_player, receiving_player, offered_resources, requested_resources):
        # Check if the offering player has the resources to trade
        for resource, amount in offered_resources.items():
            if offering_player.resources[resource] < amount:
                return False

        # Check if the receiving player has the resources to trade
        for resource, amount in requested_resources.items():
            if receiving_player.resources[resource] < amount:
                return False

        # Perform the trade
        for resource, amount in offered_resources.items():
            offering_player.resources[resource] -= amount
            receiving_player.resources[resource] += amount

        for resource, amount in requested_resources.items():
            receiving_player.resources[resource] -= amount
            offering_player.resources[resource] += amount

        return True

    def _calculate_longest_road(self, player):
        if not player.roads:
            return 0

        adj = defaultdict(list)
        for r1, r2 in player.roads:
            adj[r1].append(r2)
            adj[r2].append(r1)

        max_len = 0

        for start_node in adj:
            # Only start DFS from endpoints of road segments to be efficient
            if len(adj[start_node]) == 1:
                visited = set()

                def dfs(node, length):
                    nonlocal max_len
                    visited.add(node)
                    max_len = max(max_len, length)
                    for neighbor in adj[node]:
                        if neighbor not in visited:
                            dfs(neighbor, length + 1)

                dfs(start_node, 1)

        # The above DFS calculates nodes, but road length is edges.
        # If there are nodes, there's at least one road segment.
        return max_len -1 if max_len > 0 else 0


    def _update_longest_road(self, player):
        road_length = self._calculate_longest_road(player)

        if road_length >= 5:
            if self.longest_road_player is None:
                self.longest_road_player = player
                player.has_longest_road = True
            elif player == self.longest_road_player:
                # No change if current player already has the award
                return
            elif road_length > self._calculate_longest_road(self.longest_road_player):
                self.longest_road_player.has_longest_road = False
                self.longest_road_player = player
                player.has_longest_road = True

    def _update_largest_army(self, player):
        if player.knights >= 3:
            if self.largest_army_player is None:
                self.largest_army_player = player
                player.has_largest_army = True
            elif player.knights > self.largest_army_player.knights:
                self.largest_army_player.has_largest_army = False
                self.largest_army_player = player
                player.has_largest_army = True

    def check_for_winner(self):
        for player in self.players:
            if player.victory_points >= 10:
                return player
        return None
