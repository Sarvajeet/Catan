from collections import defaultdict
from catan.src.components import Resource

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
        self.victory_points = 0
