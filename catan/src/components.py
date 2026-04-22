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
        self.location = None  # tuple of two vertex ids

    def to_dict(self):
        return {
            "ratio": self.ratio,
            "resource": self.resource.name if self.resource else None,
            "location": list(self.location) if self.location else None,
        }


class Tile:
    def __init__(self, resource, number):
        self.resource = resource
        self.number = number


class DevelopmentCard:
    kind = "generic"

    def __init__(self, name):
        self.name = name

    def to_dict(self):
        return {"kind": self.kind, "name": self.name}


class KnightCard(DevelopmentCard):
    kind = "knight"

    def __init__(self):
        super().__init__("Knight")


class VictoryPointCard(DevelopmentCard):
    kind = "victory_point"

    def __init__(self):
        super().__init__("Victory Point")


class ProgressCard(DevelopmentCard):
    kind = "progress"

    def __init__(self, name):
        super().__init__(name)


class MonopolyCard(ProgressCard):
    kind = "monopoly"

    def __init__(self):
        super().__init__("Monopoly")


class RoadBuildingCard(ProgressCard):
    kind = "road_building"

    def __init__(self):
        super().__init__("Road Building")


class YearOfPlentyCard(ProgressCard):
    kind = "year_of_plenty"

    def __init__(self):
        super().__init__("Year of Plenty")


DEV_CARD_KINDS = {
    "knight": KnightCard,
    "victory_point": VictoryPointCard,
    "monopoly": MonopolyCard,
    "road_building": RoadBuildingCard,
    "year_of_plenty": YearOfPlentyCard,
}
