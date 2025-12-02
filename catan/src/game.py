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
        self.log = ["Game created."]
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
        self.log.append(f"{self.current_player.name} rolled a {roll}.")

        if roll == 7:
            self.log.append("A 7 was rolled! The robber is activated.")
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
        gains = defaultdict(lambda: defaultdict(int))
        for i, tile in enumerate(self.board.tiles):
            if i == self.board.robber_location or tile.resource is None or tile.number != roll:
                continue

            for player in self.players:
                vertices_on_tile = self.board.tile_to_vertices.get(i, [])
                for settlement_loc in player.settlements:
                    if settlement_loc in vertices_on_tile:
                        gains[player.name][tile.resource] += 1

                for city_loc in player.cities:
                    if city_loc in vertices_on_tile:
                        gains[player.name][tile.resource] += 2

        if not gains:
            self.log.append("No resources were distributed.")
            return

        for player in self.players:
            if player.name in gains:
                log_parts = []
                for resource, amount in gains[player.name].items():
                    if amount > 0:
                        player.resources[resource] += amount
                        log_parts.append(f"{amount} {resource.name}")
                if log_parts:
                    self.log.append(f"{player.name} received {', '.join(log_parts)}.")

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

        offered_str = ', '.join([f'{v} {k.name}' for k, v in offered_resources.items()])
        requested_str = ', '.join([f'{v} {k.name}' for k, v in requested_resources.items()])
        self.log.append(f"{offering_player.name} traded {offered_str} to {receiving_player.name} for {requested_str}.")

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
        self.log.append(f"{player.name} performed a maritime trade, giving {trade_ratio} {resource_to_give.name} for 1 {resource_to_get.name}.")
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
        self.log.append(f"{player.name} built a road.")
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
        self.log.append(f"{player.name} built a settlement at vertex {location}.")

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
        self.log.append(f"{player.name} built a city at vertex {location}.")
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
        self.log.append(f"{player.name} bought a development card.")
        return True

    def play_development_card(self, player, card, **kwargs):
        if card not in player.development_cards:
            return False # Player doesn't have this card

        self.log.append(f"{player.name} played a {card.name} card.")
        if isinstance(card, KnightCard):
            player.knights += 1
            self.move_robber(player, kwargs['new_location'], kwargs.get('target_player'))
            self._update_largest_army(player)
        elif isinstance(card, VictoryPointCard):
            # This is a passive card, the VP is calculated automatically.
            # No specific action to log here other than the card was played.
            pass
        elif isinstance(card, MonopolyCard):
            resource = kwargs['resource']
            total_stolen = 0
            for p in self.players:
                if p != player:
                    amount = p.resources[resource]
                    if amount > 0:
                        p.resources[resource] = 0
                        total_stolen += amount
            player.resources[resource] += total_stolen
            self.log.append(f"{player.name} monopolized {resource.name}, taking {total_stolen} from other players.")
        elif isinstance(card, RoadBuildingCard):
            self.build_road(player, kwargs['road1_loc'], is_setup=True)
            self.build_road(player, kwargs['road2_loc'], is_setup=True)
            self.log.append(f"{player.name} built two free roads.")
        elif isinstance(card, YearOfPlentyCard):
            res1 = kwargs['resource1']
            res2 = kwargs['resource2']
            player.resources[res1] += 1
            player.resources[res2] += 1
            self.log.append(f"{player.name} took 1 {res1.name} and 1 {res2.name} from the bank.")

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

    def to_dict(self):
        return {
            'currentPlayer': self.current_player.name,
            'current_player_index': self.current_player_index,
            'turn': self.turn,
            'players': {
                p.name: {
                    'resources': {res.name: count for res, count in p.resources.items()},
                    'settlements': p.settlements,
                    'cities': p.cities,
                    'roads': p.roads,
                    'color': p.color,
                    'victory_points': p.victory_points,
                    'knights': p.knights,
                    'development_cards_count': len(p.development_cards),
                    'has_longest_road': p.has_longest_road,
                    'has_largest_army': p.has_largest_army
                } for p in self.players
            },
            'board': {
                'tiles': [
                    {
                        'resource': tile.resource.name if tile.resource else 'DESERT',
                        'number': tile.number
                    } for tile in self.board.tiles
                ],
                'robber_location': self.board.robber_location,
                'tile_to_vertices': {str(k): v for k, v in self.board.tile_to_vertices.items()}, # Convert keys to string for JSON
            },
            'log': self.log
        }
