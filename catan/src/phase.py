from enum import Enum


class TurnPhase(str, Enum):
    """Finite state machine for a Catan game.

    Kept as a string enum so it serialises cleanly to JSON for the client.
    """

    SETUP_1 = "SETUP_1"
    SETUP_2 = "SETUP_2"
    ROLL = "ROLL"
    DISCARD = "DISCARD"
    MOVE_ROBBER = "MOVE_ROBBER"
    ROBBER_STEAL = "ROBBER_STEAL"
    MAIN = "MAIN"
    GAME_OVER = "GAME_OVER"


SETUP_PHASES = {TurnPhase.SETUP_1, TurnPhase.SETUP_2}
