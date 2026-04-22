from collections import defaultdict

from catan.src.components import Resource, VictoryPointCard


class Player:
    # Standard Catan stock limits
    MAX_SETTLEMENTS = 5
    MAX_CITIES = 4
    MAX_ROADS = 15

    def __init__(self, name, color, is_bot=False):
        self.name = name
        self.color = color
        self.is_bot = is_bot
        self.resources = defaultdict(int)
        for resource in Resource:
            self.resources[resource] = 0
        self.settlements = []  # list[int] vertex ids
        self.cities = []  # list[int] vertex ids
        self.roads = []  # list[tuple[int,int]] edges (sorted)
        self.harbors = []  # list[Harbor]
        self.development_cards = []  # playable (bought in prior turns)
        self.new_development_cards = []  # bought this turn; not playable yet
        self.played_victory_point_cards = 0  # VP cards revealed as part of winning
        self.knights = 0
        self.has_longest_road = False
        self.has_largest_army = False
        self.connected = True  # socket connection status

    @property
    def total_resources(self):
        return sum(self.resources.values())

    @property
    def victory_points(self):
        vp = 0
        vp += len(self.settlements)
        vp += 2 * len(self.cities)
        # Hidden VP cards count toward the player's own total (used for win check)
        for card in self.development_cards + self.new_development_cards:
            if isinstance(card, VictoryPointCard):
                vp += 1
        if self.has_longest_road:
            vp += 2
        if self.has_largest_army:
            vp += 2
        return vp

    @property
    def public_victory_points(self):
        """Victory points visible to opponents (hides unplayed VP cards)."""
        vp = 0
        vp += len(self.settlements)
        vp += 2 * len(self.cities)
        vp += self.played_victory_point_cards
        if self.has_longest_road:
            vp += 2
        if self.has_largest_army:
            vp += 2
        return vp
