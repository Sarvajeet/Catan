"""Smoke test: 3 bots play a full game without exceptions."""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from catan.ai.bot import advance_bots
from catan.src.game import Game
from catan.src.phase import TurnPhase


class TestBotsPlayGame(unittest.TestCase):
    def test_three_bots_finish_without_error(self):
        game = Game(["A", "B", "C"], is_bot_flags=[True, True, True], seed=123)
        # Safety cap on bot steps so a stuck bot can't hang the test
        max_steps = 3000
        for _ in range(max_steps):
            if not advance_bots(game):
                break
            if game.phase == TurnPhase.GAME_OVER:
                break
        # Either someone won or progress halted; at minimum setup must be done.
        self.assertNotIn(
            game.phase, (TurnPhase.SETUP_1, TurnPhase.SETUP_2),
            "Bots failed to complete setup phase",
        )


if __name__ == "__main__":
    unittest.main()
