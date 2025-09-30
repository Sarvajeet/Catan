from enum import Enum

class Resource(Enum):
    LUMBER = "lumber"
    WOOL = "wool"
    GRAIN = "grain"
    BRICK = "brick"
    ORE = "ore"

class Harbor:
    def __init__(self, ratio, resource=None):
        self.ratio = ratio
        self.resource = resource


class Tile:
    def __init__(self, resource, number):
        self.resource = resource
        self.number = number

class DevelopmentCard:
    def __init__(self, name):
        self.name = name

class KnightCard(DevelopmentCard):
    def __init__(self):
        super().__init__("Knight")

class VictoryPointCard(DevelopmentCard):
    def __init__(self):
        super().__init__("Victory Point")

class ProgressCard(DevelopmentCard):
    def __init__(self, name):
        super().__init__(name)

class MonopolyCard(ProgressCard):
    def __init__(self):
        super().__init__("Monopoly")

class RoadBuildingCard(ProgressCard):
    def __init__(self):
        super().__init__("Road Building")

class YearOfPlentyCard(ProgressCard):
    def __init__(self):
        super().__init__("Year of Plenty")
