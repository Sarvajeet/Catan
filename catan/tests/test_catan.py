import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from catan.src.game import Game
from catan.src.player import Player
from catan.src.components import Resource

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
