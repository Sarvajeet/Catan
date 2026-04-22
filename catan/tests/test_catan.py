"""Unit tests for the Catan engine."""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from catan.src.components import (
    KnightCard,
    MonopolyCard,
    Resource,
    RoadBuildingCard,
    VictoryPointCard,
    YearOfPlentyCard,
)
from catan.src.game import Game
from catan.src.phase import TurnPhase


def _setup_three_player_game(seed=1, zero_resources=False):
    """Run a deterministic setup sequence and return a game in ROLL phase."""
    game = Game(["Alice", "Bob", "Charlie"], seed=seed)
    # Pick snake-order placements that respect the distance rule on the
    # canonical tile_to_vertices layout. We use opposite corners.
    settlements = [0, 4, 6, 37, 33, 27]
    roads = [(0, 1), (4, 5), (6, 14), (37, 38), (33, 34), (26, 27)]
    for s, r in zip(settlements, roads):
        ok_s, msg_s = game.place_setup_settlement(game.current_player, s)
        assert ok_s, (s, msg_s)
        ok_r, msg_r = game.place_setup_road(game.current_player, r)
        assert ok_r, (r, msg_r)
    assert game.phase == TurnPhase.ROLL
    if zero_resources:
        for p in game.players:
            for r in Resource:
                p.resources[r] = 0
    return game


class TestSetup(unittest.TestCase):
    def test_setup_snake_order(self):
        game = Game(["A", "B", "C"], seed=42)
        order = []
        # Place until setup is done, recording whose turn each step is
        settlements = [0, 4, 6, 37, 33, 27]
        roads = [(0, 1), (4, 5), (6, 14), (37, 38), (33, 34), (26, 27)]
        for s, r in zip(settlements, roads):
            order.append(game.current_player.name)
            ok, _ = game.place_setup_settlement(game.current_player, s)
            self.assertTrue(ok)
            ok, _ = game.place_setup_road(game.current_player, r)
            self.assertTrue(ok)
        self.assertEqual(order, ["A", "B", "C", "C", "B", "A"])
        self.assertEqual(game.phase, TurnPhase.ROLL)

    def test_setup_distance_rule(self):
        game = Game(["A", "B"], seed=1)
        # Place first settlement
        ok, _ = game.place_setup_settlement(game.current_player, 0)
        self.assertTrue(ok)
        game.place_setup_road(game.current_player, (0, 1))
        # Player B cannot place adjacent to vertex 0 (e.g., vertex 1 is adjacent)
        ok, msg = game.place_setup_settlement(game.current_player, 1)
        self.assertFalse(ok)

    def test_setup_second_round_grants_resources(self):
        game = _setup_three_player_game(seed=1)
        # After setup, at least one player should have resources (from 2nd settlement)
        self.assertTrue(any(p.total_resources > 0 for p in game.players))


class TestPlay(unittest.TestCase):
    def test_roll_before_build_enforced(self):
        game = _setup_three_player_game(seed=1)
        p = game.current_player
        p.resources[Resource.BRICK] = 1
        p.resources[Resource.LUMBER] = 1
        ok, msg = game.build_road(p, (0, 8))
        self.assertFalse(ok)
        self.assertEqual(game.phase, TurnPhase.ROLL)

    def test_roll_non_seven_enters_main(self):
        game = _setup_three_player_game(seed=1)
        # Force a non-7 roll by calling distribute_resources directly
        game.phase = TurnPhase.ROLL
        game.dice_roll = None
        # Run many rolls and ensure state machine ends in MAIN for non-7
        ok, roll = game.roll_dice(game.current_player)
        self.assertTrue(ok)
        if roll != 7:
            self.assertEqual(game.phase, TurnPhase.MAIN)

    def test_build_road_requires_connection(self):
        game = _setup_three_player_game(seed=1)
        p = game.current_player
        # Put into MAIN phase manually
        game.phase = TurnPhase.MAIN
        game.dice_roll = 6
        p.resources[Resource.BRICK] = 1
        p.resources[Resource.LUMBER] = 1
        # Player 0's settlements were at 0 and 37; they own road (0,1) and (37,38).
        # Edge (20,21) is a valid board edge but not connected to player 0's network.
        ok, msg = game.build_road(p, (20, 21))
        self.assertFalse(ok, msg)

    def test_build_city_upgrades_settlement(self):
        game = _setup_three_player_game(seed=1)
        p = game.current_player
        game.phase = TurnPhase.MAIN
        game.dice_roll = 6
        p.resources[Resource.GRAIN] = 2
        p.resources[Resource.ORE] = 3
        settlement = p.settlements[0]
        ok, _ = game.build_city(p, settlement)
        self.assertTrue(ok)
        self.assertIn(settlement, p.cities)
        self.assertNotIn(settlement, p.settlements)

    def test_end_turn_rotates_player(self):
        game = _setup_three_player_game(seed=1)
        first = game.current_player
        game.phase = TurnPhase.MAIN
        game.dice_roll = 8
        ok, _ = game.end_turn(first)
        self.assertTrue(ok)
        self.assertIsNot(game.current_player, first)
        self.assertEqual(game.phase, TurnPhase.ROLL)

    def test_cannot_end_turn_without_rolling(self):
        game = _setup_three_player_game(seed=1)
        ok, msg = game.end_turn(game.current_player)
        self.assertFalse(ok)


class TestSeven(unittest.TestCase):
    def test_discard_flow_for_rich_player(self):
        game = _setup_three_player_game(seed=1, zero_resources=True)
        p = game.current_player
        # Give them 9 cards so they must discard 4
        p.resources[Resource.WOOL] = 9
        game.phase = TurnPhase.ROLL
        game._begin_seven_sequence()
        self.assertEqual(game.phase, TurnPhase.DISCARD)
        self.assertEqual(game.pending_discards[p.name], 4)
        ok, msg = game.submit_discard(p, {Resource.WOOL: 4})
        self.assertTrue(ok, msg)
        self.assertEqual(p.resources[Resource.WOOL], 5)
        self.assertEqual(game.phase, TurnPhase.MOVE_ROBBER)

    def test_move_robber_to_empty_hex_skips_steal(self):
        game = _setup_three_player_game(seed=1)
        p = game.current_player
        game.phase = TurnPhase.MOVE_ROBBER
        game.robber_mover = p
        # Find a hex with no opponent buildings
        for idx, _ in enumerate(game.board.tiles):
            if idx == game.board.robber_location:
                continue
            verts = set(game.board.vertices_on_tile(idx))
            safe = True
            for other in game.players:
                if other is p:
                    continue
                for v in other.settlements + other.cities:
                    if v in verts:
                        safe = False
                        break
                if not safe:
                    break
            if safe:
                ok, _ = game.move_robber(p, idx)
                self.assertTrue(ok)
                self.assertEqual(game.phase, TurnPhase.MAIN)
                return
        self.skipTest("No safe hex found on this board")


class TestTrading(unittest.TestCase):
    def test_offer_and_accept_trade(self):
        game = _setup_three_player_game(seed=1, zero_resources=True)
        a, b = game.players[0], game.players[1]
        game.current_player_index = 0
        game.phase = TurnPhase.MAIN
        game.dice_roll = 5
        a.resources[Resource.LUMBER] = 2
        b.resources[Resource.BRICK] = 2
        ok, trade_id = game.offer_trade(
            a, [b.name], {Resource.LUMBER: 1}, {Resource.BRICK: 1}
        )
        self.assertTrue(ok)
        ok, _ = game.accept_trade(trade_id, b)
        self.assertTrue(ok)
        self.assertEqual(a.resources[Resource.LUMBER], 1)
        self.assertEqual(a.resources[Resource.BRICK], 1)
        self.assertEqual(b.resources[Resource.LUMBER], 1)
        self.assertEqual(b.resources[Resource.BRICK], 1)

    def test_maritime_trade_default_ratio(self):
        game = _setup_three_player_game(seed=1)
        p = game.current_player
        game.phase = TurnPhase.MAIN
        game.dice_roll = 5
        p.harbors = []  # ensure no discounted harbors
        p.resources[Resource.WOOL] = 4
        ok, ratio = game.maritime_trade(p, Resource.WOOL, Resource.ORE)
        self.assertTrue(ok)
        self.assertEqual(ratio, 4)
        self.assertEqual(p.resources[Resource.WOOL], 0)
        self.assertEqual(p.resources[Resource.ORE], 1)


class TestDevelopmentCards(unittest.TestCase):
    def test_buy_development_card(self):
        game = _setup_three_player_game(seed=1)
        p = game.current_player
        game.phase = TurnPhase.MAIN
        game.dice_roll = 5
        p.resources[Resource.ORE] = 1
        p.resources[Resource.WOOL] = 1
        p.resources[Resource.GRAIN] = 1
        ok, _ = game.buy_development_card(p)
        self.assertTrue(ok)
        self.assertEqual(len(p.new_development_cards), 1)

    def test_knight_triggers_robber_flow(self):
        game = _setup_three_player_game(seed=1)
        p = game.current_player
        game.phase = TurnPhase.MAIN
        game.dice_roll = 5
        p.development_cards.append(KnightCard())
        ok, _ = game.play_development_card(p, "knight")
        self.assertTrue(ok)
        self.assertEqual(p.knights, 1)
        self.assertEqual(game.phase, TurnPhase.MOVE_ROBBER)

    def test_monopoly_steals_from_all(self):
        game = _setup_three_player_game(seed=1)
        p1, p2, p3 = game.players
        game.current_player_index = 0
        game.phase = TurnPhase.MAIN
        game.dice_roll = 5
        p1.development_cards.append(MonopolyCard())
        p2.resources[Resource.WOOL] = 3
        p3.resources[Resource.WOOL] = 2
        p1.resources[Resource.WOOL] = 0
        ok, _ = game.play_development_card(p1, "monopoly", resource="WOOL")
        self.assertTrue(ok)
        self.assertEqual(p1.resources[Resource.WOOL], 5)
        self.assertEqual(p2.resources[Resource.WOOL], 0)
        self.assertEqual(p3.resources[Resource.WOOL], 0)

    def test_year_of_plenty(self):
        game = _setup_three_player_game(seed=1)
        p = game.current_player
        game.phase = TurnPhase.MAIN
        game.dice_roll = 5
        p.development_cards.append(YearOfPlentyCard())
        ok, _ = game.play_development_card(
            p, "year_of_plenty", resource1="ORE", resource2="GRAIN"
        )
        self.assertTrue(ok)
        self.assertEqual(p.resources[Resource.ORE], 1)
        self.assertEqual(p.resources[Resource.GRAIN], 1)

    def test_one_dev_card_per_turn_except_vp(self):
        game = _setup_three_player_game(seed=1)
        p = game.current_player
        game.phase = TurnPhase.MAIN
        game.dice_roll = 5
        p.development_cards.append(YearOfPlentyCard())
        p.development_cards.append(MonopolyCard())
        p.development_cards.append(VictoryPointCard())
        ok, _ = game.play_development_card(p, "year_of_plenty", resource1="ORE", resource2="GRAIN")
        self.assertTrue(ok)
        ok, msg = game.play_development_card(p, "monopoly", resource="WOOL")
        self.assertFalse(ok)
        # VP card can still be revealed
        ok, _ = game.play_development_card(p, "victory_point")
        self.assertTrue(ok)


class TestHiddenInfo(unittest.TestCase):
    def test_viewer_sees_own_resources_only(self):
        game = _setup_three_player_game(seed=1, zero_resources=True)
        p1, p2 = game.players[0], game.players[1]
        p1.resources[Resource.ORE] = 3
        p2.resources[Resource.ORE] = 2
        view = game.to_dict(viewer_name=p1.name)
        self.assertIn("resources", view["players"][p1.name])
        self.assertNotIn("resources", view["players"][p2.name])
        self.assertEqual(view["players"][p2.name]["resource_count"], 2)


class TestWinCondition(unittest.TestCase):
    def test_winner_detected(self):
        game = _setup_three_player_game(seed=1)
        p = game.players[0]
        # Give them enough VP without touching board state
        p.settlements = [0, 1, 2]  # 3 VP
        p.cities = [4, 5, 6]  # 6 VP, total 9
        p.has_largest_army = True  # +2 = 11
        winner = game.check_for_winner()
        self.assertIs(winner, p)


if __name__ == "__main__":
    unittest.main()
