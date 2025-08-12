from enum import Enum
import collections

class GamePhase(Enum):
    SETUP_ROUND_1 = "setup_round_1"
    SETUP_ROUND_2 = "setup_round_2"
    MAIN_GAME = "main_game"

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

Hex = collections.namedtuple("Hex", ["q", "r", "s"])

def hex_add(a, b):
    return Hex(a.q + b.q, a.r + b.r, a.s + b.s)

def hex_subtract(a, b):
    return Hex(a.q - b.q, a.r - b.r, a.s - b.s)

def hex_scale(a, k):
    return Hex(a.q * k, a.r * k, a.s * k)

hex_directions = [Hex(1, 0, -1), Hex(1, -1, 0), Hex(0, -1, 1), Hex(-1, 0, 1), Hex(-1, 1, 0), Hex(0, 1, -1)]

def hex_direction(direction):
    return hex_directions[direction]

def hex_neighbor(h, direction):
    return hex_add(h, hex_direction(direction))
