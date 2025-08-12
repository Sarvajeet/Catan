import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from catan.src.game import Game
from catan.src.player import Player
from catan.src.components import Resource, Hex, Tile

class TestGame(unittest.TestCase):
    def setUp(self):
        self.game = Game(player_names=["Alice", "Bob"])
        self.game.start_game()
        self.player1 = self.game.players[0]
        self.player2 = self.game.players[1]

        # Manually set up a predictable board for testing
        self.game.board.tiles = {
            Hex(0, 0, 0): Tile(Resource.LUMBER, 10),
            Hex(1, 0, -1): Tile(Resource.BRICK, 2),
            Hex(0, 1, -1): Tile(Resource.WOOL, 9),
            Hex(1, -1, 0): Tile(Resource.GRAIN, 12),
            Hex(-1, 0, 1): Tile(Resource.ORE, 6),
            Hex(0, -1, 1): Tile(Resource.LUMBER, 4),
            Hex(-1, 1, 0): Tile(Resource.BRICK, 8),
        }
        # Re-create the graph for the new tiles
        self.game.board._create_board_graph()


    def give_resources(self, player, resource_dict):
        for resource, amount in resource_dict.items():
            player.resources[resource] = amount

    def test_distribute_resources(self):
        # Settlement at the junction of (0,0,0), (1,0,-1), and (0,1,-1)
        settlement_loc = frozenset([Hex(0,0,0), Hex(1,0,-1), Hex(0,1,-1)])
        self.player1.settlements.append(settlement_loc)

        self.game.distribute_resources(10)
        self.assertEqual(self.player1.resources[Resource.LUMBER], 1)
        self.game.distribute_resources(2)
        self.assertEqual(self.player1.resources[Resource.BRICK], 1)
        self.game.distribute_resources(9)
        self.assertEqual(self.player1.resources[Resource.WOOL], 1)

    def test_build_settlement_valid(self):
        self.give_resources(self.player1, {Resource.BRICK: 1, Resource.LUMBER: 1, Resource.WOOL: 1, Resource.GRAIN: 1})

        v1 = frozenset([Hex(0,0,0), Hex(1,0,-1), Hex(1,-1,0)])
        v2 = frozenset([Hex(0,0,0), Hex(1,-1,0), Hex(0,-1,1)])
        v3 = frozenset([Hex(0,0,0), Hex(0,-1,1), Hex(-1,0,1)])

        # Place initial settlement at v1. Player has 1 settlement, so is_setup_phase is true.
        self.player1.settlements.append(v1)
        self.player1.victory_points = 1

        # Place a chain of roads. Road connectivity is not checked in setup phase.
        self.player1.roads.append(frozenset([v1, v2]))
        self.player1.roads.append(frozenset([v2, v3]))

        # Attempt to build a new settlement at v3.
        # This is valid because it's 2 edges away from v1.
        self.assertTrue(self.game.build_settlement(self.player1, v3))
        self.assertEqual(len(self.player1.settlements), 2)
        self.assertEqual(self.player1.victory_points, 2)

    def test_build_settlement_invalid_resources(self):
        self.give_resources(self.player1, {Resource.BRICK: 0, Resource.LUMBER: 1, Resource.WOOL: 1, Resource.GRAIN: 1})
        settlement_loc = frozenset([Hex(0,0,0), Hex(1,0,-1), Hex(0,1,-1)])
        self.assertFalse(self.game.build_settlement(self.player1, settlement_loc))

    def test_build_settlement_invalid_distance(self):
        settlement1_loc = frozenset([Hex(0,0,0), Hex(1,0,-1), Hex(0,1,-1)])
        self.player1.settlements.append(settlement1_loc)

        self.give_resources(self.player1, {Resource.BRICK: 1, Resource.LUMBER: 1, Resource.WOOL: 1, Resource.GRAIN: 1})
        # This settlement is adjacent to the first one
        settlement2_loc = frozenset([Hex(0,0,0), Hex(1,0,-1), Hex(1,-1,0)])
        self.assertFalse(self.game.build_settlement(self.player1, settlement2_loc))

    def test_build_city_valid(self):
        settlement_loc = frozenset([Hex(0,0,0), Hex(1,0,-1), Hex(0,1,-1)])
        self.player1.settlements.append(settlement_loc)
        self.player1.victory_points = 1
        self.give_resources(self.player1, {Resource.GRAIN: 2, Resource.ORE: 3})

        self.assertTrue(self.game.build_city(self.player1, settlement_loc))
        self.assertIn(settlement_loc, self.player1.cities)
        self.assertNotIn(settlement_loc, self.player1.settlements)
        self.assertEqual(self.player1.victory_points, 2)

    def test_build_road_valid(self):
        settlement_loc = frozenset([Hex(0,0,0), Hex(1,0,-1), Hex(0,1,-1)])
        self.player1.settlements.append(settlement_loc)
        self.give_resources(self.player1, {Resource.BRICK: 1, Resource.LUMBER: 1})

        v1 = frozenset([Hex(0,0,0), Hex(1,0,-1), Hex(0,1,-1)])
        v2 = frozenset([Hex(0,0,0), Hex(0,1,-1), Hex(-1,1,0)])
        road_loc = frozenset([v1, v2])

        self.assertTrue(self.game.build_road(self.player1, road_loc))
        self.assertIn(road_loc, self.player1.roads)

    def test_build_road_invalid_connectivity(self):
        self.give_resources(self.player1, {Resource.BRICK: 1, Resource.LUMBER: 1})
        # Road is not connected to anything
        v1 = frozenset([Hex(0,0,0), Hex(1,0,-1), Hex(0,1,-1)])
        v2 = frozenset([Hex(0,0,0), Hex(0,1,-1), Hex(-1,1,0)])
        road_loc = frozenset([v1, v2])
        self.assertFalse(self.game.build_road(self.player1, road_loc))

if __name__ == "__main__":
    unittest.main()
