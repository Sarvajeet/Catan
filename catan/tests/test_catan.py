import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from catan.src.game import Game
from catan.src.player import Player
from catan.src.components import Resource, KnightCard, VictoryPointCard, MonopolyCard, RoadBuildingCard, YearOfPlentyCard

class TestGame(unittest.TestCase):
    def setUp(self):
        self.game = Game(player_names=["Alice", "Bob", "Charlie"])
        # Simplified setup for testing
        initial_placements = [
            {"settlement": 8, "road": (8, 9)},
            {"settlement": 22, "road": (22, 21)},
            {"settlement": 14, "road": (14, 13)},
            {"settlement": 33, "road": (33, 32)},
            {"settlement": 40, "road": (40, 41)},
            {"settlement": 45, "road": (45, 46)},
        ]
        self.game.start_game(initial_placements)
        self.player1 = self.game.players[0]
        self.player2 = self.game.players[1]

    def test_initial_setup(self):
        self.assertEqual(len(self.player1.settlements), 2)
        self.assertEqual(len(self.player1.roads), 2)
        self.assertEqual(self.player1.victory_points, 2)
        # Check that initial resources were distributed
        self.assertGreater(sum(self.player1.resources.values()), 0)

    def test_roll_dice_and_resource_distribution(self):
        # Manually set up a scenario for resource distribution
        # Player 1 starts with a settlement on vertex 8. Tile 0 is adjacent to vertex 8.
        self.game.board.tiles[0].number = 4
        self.game.board.tiles[0].resource = Resource.LUMBER

        # Clear resources to make test deterministic
        for res in Resource:
            self.player1.resources[res] = 0

        initial_lumber = self.player1.resources[Resource.LUMBER] # Should be 0
        self.game.distribute_resources(4)

        # Player 1 should get 1 lumber because they have 1 settlement on tile 0
        self.assertEqual(self.player1.resources[Resource.LUMBER], initial_lumber + 1)

    def test_build_road(self):
        # Clear resources for a clean test
        for res in Resource:
            self.player1.resources[res] = 0
        self.player1.resources[Resource.BRICK] = 1
        self.player1.resources[Resource.LUMBER] = 1
        # Player 1 has a settlement at vertex 8
        self.assertTrue(self.game.build_road(self.player1, (8, 7)))
        self.assertEqual(self.player1.resources[Resource.BRICK], 0)
        self.assertEqual(self.player1.resources[Resource.LUMBER], 0)
        self.assertIn((8, 7), self.player1.roads)

    def test_build_settlement(self):
        # Clear resources for a clean test
        for res in Resource:
            self.player1.resources[res] = 0
        self.player1.resources.update({Resource.BRICK: 1, Resource.LUMBER: 1, Resource.WOOL: 1, Resource.GRAIN: 1})
        # Player 1 has a road (8,9)
        self.assertTrue(self.game.build_settlement(self.player1, 9))
        self.assertEqual(self.player1.victory_points, 3) # 2 initial + 1 new

    def test_build_city(self):
        # Clear resources for a clean test
        for res in Resource:
            self.player1.resources[res] = 0
        self.player1.resources.update({Resource.GRAIN: 2, Resource.ORE: 3})
        settlement_loc = self.player1.settlements[0]
        self.assertTrue(self.game.build_city(self.player1, settlement_loc))
        self.assertIn(settlement_loc, self.player1.cities)
        self.assertNotIn(settlement_loc, self.player1.settlements)
        self.assertEqual(self.player1.victory_points, 3) # 2 initial settlements (2 VP) + 1 for city upgrade = 3VP

    def test_trade(self):
        # Clear resources for a clean test
        for res in Resource:
            self.player1.resources[res] = 0
            self.player2.resources[res] = 0
        self.player1.resources[Resource.LUMBER] = 1
        self.player2.resources[Resource.BRICK] = 1
        self.assertTrue(self.game.trade(self.player1, self.player2, {Resource.LUMBER: 1}, {Resource.BRICK: 1}))
        self.assertEqual(self.player1.resources[Resource.LUMBER], 0)
        self.assertEqual(self.player1.resources[Resource.BRICK], 1)
        self.assertEqual(self.player2.resources[Resource.BRICK], 0)
        self.assertEqual(self.player2.resources[Resource.LUMBER], 1)

    def test_buy_development_card(self):
        self.player1.resources.update({Resource.ORE: 1, Resource.WOOL: 1, Resource.GRAIN: 1})
        self.assertTrue(self.game.buy_development_card(self.player1))
        self.assertEqual(len(self.player1.new_development_cards), 1)

    def test_play_knight_card(self):
        card = KnightCard()
        self.player1.development_cards.append(card)
        self.game.play_development_card(self.player1, card, new_location=10)
        self.assertEqual(self.player1.knights, 1)
        self.assertEqual(self.game.board.robber_location, 10)
        self.assertNotIn(card, self.player1.development_cards)

    def test_win_condition(self):
        self.player1.victory_points = 9
        self.assertIsNone(self.game.check_for_winner())
        self.player1.victory_points = 10
        self.assertEqual(self.game.check_for_winner(), self.player1)

if __name__ == '__main__':
    unittest.main()