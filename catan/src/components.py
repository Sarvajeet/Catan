from enum import Enum

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
