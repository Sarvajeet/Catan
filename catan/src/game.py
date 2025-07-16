import random
from catan.src.board import Board
from catan.src.player import Player

class Game:
    def __init__(self, player_names):
        self.board = Board()
        self.players = [Player(name, color) for name, color in zip(player_names, ["red", "blue", "green", "yellow"])]
        self.current_player_index = 0
        self.turn = 0

    def start_game(self):
        # Initial setup phase (placing first two settlements and roads) will be implemented later
        self.turn = 1

    def roll_dice(self):
        die1 = random.randint(1, 6)
        die2 = random.randint(1, 6)
        roll = die1 + die2
        self.distribute_resources(roll)
        return roll

    def distribute_resources(self, roll):
        for tile in self.board.tiles:
            if tile.number == roll:
                for player in self.players:
                    # This is a simplified version. We need to check if the settlement is adjacent to the tile.
                    # This will be implemented later.
                    for settlement in player.settlements:
                        if settlement == tile: # Simplified adjacency check
                            player.resources[tile.resource] += 1
                    for city in player.cities:
                        if city == tile: # Simplified adjacency check
                            player.resources[tile.resource] += 2

    def next_turn(self):
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        self.turn += 1
