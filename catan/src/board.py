import random
from catan.src.components import Tile, Resource
from catan.src.graph import Graph

class Board:
    def __init__(self):
        self.graph = Graph()
        self.tiles = self._create_tiles()
        self._create_board_graph()

    def _create_tiles(self):
        resources = [
            Resource.LUMBER, Resource.LUMBER, Resource.LUMBER, Resource.LUMBER,
            Resource.WOOL, Resource.WOOL, Resource.WOOL, Resource.WOOL,
            Resource.GRAIN, Resource.GRAIN, Resource.GRAIN, Resource.GRAIN,
            Resource.BRICK, Resource.BRICK, Resource.BRICK,
            Resource.ORE, Resource.ORE, Resource.ORE
        ]
        random.shuffle(resources)

        numbers = [2, 3, 3, 4, 4, 5, 5, 6, 6, 8, 8, 9, 9, 10, 10, 11, 11, 12]
        random.shuffle(numbers)

        tiles = []
        for i in range(len(resources)):
            tiles.append(Tile(resources[i], numbers[i]))

        # Add the desert tile
        tiles.insert(random.randint(0, len(tiles)), Tile(None, 7))

        return tiles

    def _create_board_graph(self):
        # This is a simplified representation of the board graph.
        # We will improve this later.
        for i in range(len(self.tiles)):
            self.graph.addVertex(i)

        # Add edges between adjacent tiles
        # This is a simplified representation of the board graph.
        # We will improve this later.
        for i in range(len(self.tiles)):
            if i % 5 != 4:
                self.graph.addEdge(i, i + 1)
            if i < len(self.tiles) - 5:
                self.graph.addEdge(i, i + 5)

    def get_tiles_for_settlement(self, settlement_location):
        # This is a simplified version. We need to implement a way to get the
        # tiles for a given settlement location.
        return [self.tiles[0]]

    def get_vertices_for_settlement(self, settlement_location):
        # This is a simplified version. We need to implement a way to get the
        # vertices for a given settlement location.
        return [self.graph.getVertex(0)]
