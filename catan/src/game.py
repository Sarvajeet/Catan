import random
from catan.src.board import Board
from catan.src.player import Player
from catan.src.components import Resource

class Game:
    def __init__(self, player_names):
        self.board = Board()
        self.players = [Player(name, color) for name, color in zip(player_names, ["red", "blue", "green", "yellow"])]
        self.current_player_index = 0
        self.turn = 0

    @property
    def current_player(self):
        return self.players[self.current_player_index]

    def start_game(self):
        # Initial setup phase (placing first two settlements and roads) will be implemented later
        self.turn = 1

    def roll_dice(self):
        if self.turn == 0:
            return # Can't roll dice before the game has started

        die1 = random.randint(1, 6)
        die2 = random.randint(1, 6)
        roll = die1 + die2
        if roll == 7:
            # Robber logic will be implemented later
            pass
        else:
            self.distribute_resources(roll)
        return roll

    def distribute_resources(self, roll):
        for hex_coord, tile in self.board.tiles.items():
            if tile.number == roll and tile.resource is not None:
                for player in self.players:
                    for settlement_location in player.settlements:
                        if hex_coord in settlement_location:
                            player.resources[tile.resource] += 1
                    for city_location in player.cities:
                        if hex_coord in city_location:
                            player.resources[tile.resource] += 2

    def next_turn(self):
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

    def build_road(self, player, location):
        # location is a frozenset of two vertex identifiers
        if not isinstance(location, frozenset) or len(location) != 2:
            return False  # Invalid road location

        # Check resources
        required_resources = {Resource.BRICK: 1, Resource.LUMBER: 1}
        for resource, amount in required_resources.items():
            if player.resources[resource] < amount:
                return False  # Not enough resources

        # Check if the edge is already occupied
        for p in self.players:
            if location in p.roads:
                return False  # Road already built

        # Check connectivity
        # The road must be connected to one of the player's existing roads, settlements, or cities.
        v1, v2 = tuple(location)
        is_connected = False

        # Check for connection to settlements or cities
        if v1 in player.settlements or v1 in player.cities or v2 in player.settlements or v2 in player.cities:
            is_connected = True

        # Check for connection to other roads
        if not is_connected:
            for road in player.roads:
                if v1 in road or v2 in road:
                    is_connected = True
                    break

        # The setup phase is not fully implemented. This check assumes that a road must be connected
        # to a settlement if it's the first road.
        if not is_connected and len(player.roads) == 0 and len(player.settlements) == 0:
            return False

        if not is_connected:
            return False

        # All checks passed, build the road
        for resource, amount in required_resources.items():
            player.resources[resource] -= amount

        player.roads.append(location)
        return True

    def build_settlement(self, player, location):
        # location is a frozenset of Hex objects
        # Check resources
        required_resources = {Resource.BRICK: 1, Resource.LUMBER: 1, Resource.WOOL: 1, Resource.GRAIN: 1}
        for resource, amount in required_resources.items():
            if player.resources[resource] < amount:
                return False  # Not enough resources

        # Check distance rule
        # Check if location is already occupied
        for p in self.players:
            if location in p.settlements or location in p.cities:
                return False  # Location already occupied

        # Check if adjacent vertices are occupied
        adjacent_vertices = self.board.get_vertices_for_settlement(location)
        for v in adjacent_vertices:
            for p in self.players:
                if v in p.settlements or v in p.cities:
                    return False  # Too close to another settlement/city

        # Check road connectivity (not enforced during setup phase)
        is_setup_phase = len(player.settlements) < 2
        if not is_setup_phase:
            road_connected = False
            for road in player.roads:
                if location in road:
                    road_connected = True
                    break
            if not road_connected:
                return False

        # All checks passed, build the settlement
        for resource, amount in required_resources.items():
            player.resources[resource] -= amount

        player.settlements.append(location)
        player.victory_points += 1
        return True

    def build_city(self, player, location):
        # location is a frozenset of Hex objects
        # Check resources
        required_resources = {Resource.GRAIN: 2, Resource.ORE: 3}
        for resource, amount in required_resources.items():
            if player.resources[resource] < amount:
                return False  # Not enough resources

        # Check if player has a settlement at the location
        if location not in player.settlements:
            return False  # No settlement to upgrade

        # All checks passed, build the city
        for resource, amount in required_resources.items():
            player.resources[resource] -= amount

        player.settlements.remove(location)
        player.cities.append(location)
        player.victory_points += 1  # +1 for upgrading settlement to city
        return True
