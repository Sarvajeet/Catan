import random
from catan.src.board import Board
from catan.src.player import Player

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
        self.distribute_resources(roll)
        return roll

    def distribute_resources(self, roll):
        for tile in self.board.tiles:
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
        # This is a simplified version. We need to implement a way to check
        # if the location is valid and if the player has the resources.
        player.roads.append(location)
        return True

    def build_settlement(self, player, location):
        # This is a simplified version. We need to implement a way to check
        # if the location is valid and if the player has the resources.
        player.settlements.append(location)
        player.victory_points += 1
        return True

    def build_city(self, player, location):
        # This is a simplified version. We need to implement a way to check
        # if the location is valid and if the player has the resources.
        player.cities.append(location)
        player.victory_points += 1
        return True
