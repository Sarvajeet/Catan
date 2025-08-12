import random
from catan.src.board import Board
from catan.src.player import Player
from catan.src.components import Resource, GamePhase

class Game:
    def __init__(self, player_names):
        self.board = Board()
        self.players = [Player(name, color) for name, color in zip(player_names, ["red", "blue", "green", "yellow"])]
        self.current_player_index = 0
        self.turn = 0
        self.game_phase = None
        self.setup_turn_index = 0
        self.setup_direction = 1
        self.last_built_settlement = None

    @property
    def current_player(self):
        return self.players[self.current_player_index]

    def start_game(self):
        self.game_phase = GamePhase.SETUP_ROUND_1
        self.current_player_index = 0
        self.turn = 1

    def next_setup_turn(self):
        if self.game_phase == GamePhase.SETUP_ROUND_1:
            self.current_player_index += 1
            if self.current_player_index >= len(self.players):
                self.game_phase = GamePhase.SETUP_ROUND_2
                self.current_player_index -= 1 # Last player goes again
        elif self.game_phase == GamePhase.SETUP_ROUND_2:
            self.current_player_index -= 1
            if self.current_player_index < 0:
                self.game_phase = GamePhase.MAIN_GAME
                self.current_player_index = 0
        self.last_built_settlement = None


    def roll_dice(self):
        if self.game_phase != GamePhase.MAIN_GAME:
            return # Can't roll dice during setup

        die1 = random.randint(1, 6)
        die2 = random.randint(1, 6)
        roll = die1 + die2
        if roll == 7:
            # Robber logic will be implemented later
            pass
        else:
            self.distribute_resources(roll)
        return roll

    def distribute_resources(self, roll, initial_setup=False):
        for hex_coord, tile in self.board.tiles.items():
            if initial_setup or (tile.number == roll and tile.resource is not None):
                for player in self.players:
                    if initial_setup:
                        # For initial setup, distribute for the last placed settlement
                        if self.last_built_settlement and hex_coord in self.last_built_settlement:
                            player.resources[tile.resource] += 1
                    else:
                        for settlement_location in player.settlements:
                            if hex_coord in settlement_location:
                                player.resources[tile.resource] += 1
                        for city_location in player.cities:
                            if hex_coord in city_location:
                                player.resources[tile.resource] += 2

    def next_turn(self):
        if self.game_phase != GamePhase.MAIN_GAME:
            return
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
        if not isinstance(location, frozenset) or len(location) != 2:
            return False

        is_setup = self.game_phase != GamePhase.MAIN_GAME
        if not is_setup:
            required_resources = {Resource.BRICK: 1, Resource.LUMBER: 1}
            for resource, amount in required_resources.items():
                if player.resources[resource] < amount:
                    return False

        for p in self.players:
            if location in p.roads:
                return False

        v1, v2 = tuple(location)
        is_connected = False
        if is_setup:
            if self.last_built_settlement and (v1 == self.last_built_settlement or v2 == self.last_built_settlement):
                is_connected = True
        else:
            if v1 in player.settlements or v1 in player.cities or v2 in player.settlements or v2 in player.cities:
                is_connected = True
            if not is_connected:
                for road in player.roads:
                    if v1 in road or v2 in road:
                        is_connected = True
                        break

        if not is_connected:
            return False

        if not is_setup:
            for resource, amount in required_resources.items():
                player.resources[resource] -= amount

        player.roads.append(location)
        return True

    def build_settlement(self, player, location):
        is_setup = self.game_phase != GamePhase.MAIN_GAME

        if not is_setup:
            required_resources = {Resource.BRICK: 1, Resource.LUMBER: 1, Resource.WOOL: 1, Resource.GRAIN: 1}
            for resource, amount in required_resources.items():
                if player.resources[resource] < amount:
                    return False

        for p in self.players:
            if location in p.settlements or location in p.cities:
                return False

        adjacent_vertices = self.board.get_vertices_for_settlement(location)
        for v in adjacent_vertices:
            for p in self.players:
                if v in p.settlements or v in p.cities:
                    return False

        if not is_setup:
            road_connected = False
            for road in player.roads:
                if location in road:
                    road_connected = True
                    break
            if not road_connected:
                return False

        if not is_setup:
            for resource, amount in required_resources.items():
                player.resources[resource] -= amount

        player.settlements.append(location)
        player.victory_points += 1
        self.last_built_settlement = location

        if self.game_phase == GamePhase.SETUP_ROUND_2:
            self.distribute_resources(0, initial_setup=True)

        return True

    def build_city(self, player, location):
        if self.game_phase != GamePhase.MAIN_GAME:
            return False

        required_resources = {Resource.GRAIN: 2, Resource.ORE: 3}
        for resource, amount in required_resources.items():
            if player.resources[resource] < amount:
                return False

        if location not in player.settlements:
            return False

        for resource, amount in required_resources.items():
            player.resources[resource] -= amount

        player.settlements.remove(location)
        player.cities.append(location)
        player.victory_points += 1
        return True
