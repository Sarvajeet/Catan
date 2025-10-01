from collections import defaultdict
from catan.src.components import Resource, VictoryPointCard

class Player:
    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.resources = defaultdict(int)
        for resource in Resource:
            self.resources[resource] = 0
        self.settlements = []
        self.cities = []
        self.roads = []
        self.harbors = []
        self.development_cards = []
        self.new_development_cards = []
        self.knights = 0
        self.has_longest_road = False
        self.has_largest_army = False

    @property
    def victory_points(self):
        vp = 0
        vp += len(self.settlements)
        vp += 2 * len(self.cities)
        for card in self.development_cards + self.new_development_cards:
            if isinstance(card, VictoryPointCard):
                vp += 1
        if self.has_longest_road:
            vp += 2
        if self.has_largest_army:
            vp += 2
        return vp
