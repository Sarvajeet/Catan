import unittest
from collections import defaultdict
from enum import Enum
import random

class Resource(Enum):
    LUMBER = "lumber"
    WOOL = "wool"
    GRAIN = "grain"
    BRICK = "brick"
    ORE = "ore"

class Tile:
    def __init__(self, resource, number):
        self.resource = resource
        self.number = number

class Player:
    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.resources = defaultdict(int)
        for resource in Resource:
            self.resources[resource] = 0
        self.settlements = []
        self.cities = []
        self.roads = []
        self.victory_points = 0

class Board:
    def __init__(self):
        self.tiles = self._create_tiles()

    def _create_tiles(self):
        resources = [
            Resource.LUMBER, Resource.LUMBER, Resource.LUMBER, Resource.LUMBER,
            Resource.WOOL, Resource.WOOL, Resource.WOOL, Resource.WOOL,
            Resource.GRAIN, Resource.GRAIN, Resource.GRAIN, Resource.GRAIN,
            Resource.BRICK, Resource.BRICK, Resource.BRICK,
            Resource.ORE, Resource.ORE, Resource.ORE
        ]
        random.shuffle(resources)

        numbers = [2, 3, 3, 4, 4, 5, 5, 6, 6, 8, 8, 9, 9, 10, 10, 11, 11, 12]
        random.shuffle(numbers)

        tiles = []
        for i in range(len(resources)):
            tiles.append(Tile(resources[i], numbers[i]))

        # Add the desert tile
        tiles.insert(random.randint(0, len(tiles)), Tile(None, 7))

        return tiles

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

class TestGame(unittest.TestCase):
    def setUp(self):
        self.game = Game(player_names=["Alice", "Bob"])

    def test_initial_game_state(self):
        self.assertEqual(len(self.game.players), 2)
        self.assertEqual(self.game.turn, 0)
        self.assertIsInstance(self.game.players[0], Player)
        self.assertEqual(self.game.players[0].name, "Alice")

    def test_roll_dice(self):
        roll = self.game.roll_dice()
        self.assertGreaterEqual(roll, 2)
        self.assertLessEqual(roll, 12)

    def test_distribute_resources(self):
        player = self.game.players[0]
        tile = self.game.board.tiles[0]
        tile.number = 6
        tile.resource = Resource.LUMBER
        player.settlements.append(tile)

        initial_lumber = player.resources[Resource.LUMBER]
        self.game.distribute_resources(6)
        self.assertEqual(player.resources[Resource.LUMBER], initial_lumber + 1)

if __name__ == "__main__":
    unittest.main()
