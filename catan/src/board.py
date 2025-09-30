import random
from catan.src.components import Tile, Resource, Harbor
from catan.src.graph import Graph

class Board:
    def __init__(self):
        self.graph = Graph()
        self.tiles = self._create_tiles()
        self.robber_location = -1
        self.vertex_tile_map = {}
        self.harbors = []
        self._create_board_graph()
        self._create_vertex_tile_map()
        self._create_harbors()

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
        desert_index = random.randint(0, len(tiles))
        tiles.insert(desert_index, Tile(None, 7))
        self.robber_location = desert_index

        return tiles

    def _create_board_graph(self):
        self.tile_to_vertices = {
            0: [0, 1, 2, 10, 9, 8], 1: [2, 3, 4, 12, 11, 10], 2: [4, 5, 6, 14, 13, 12],
            3: [7, 8, 9, 19, 18, 17], 4: [9, 10, 11, 21, 20, 19], 5: [11, 12, 13, 23, 22, 21],
            6: [13, 14, 15, 25, 24, 23], 7: [17, 18, 19, 30, 29, 28], 8: [19, 20, 21, 32, 31, 30],
            9: [21, 22, 23, 34, 33, 32], 10: [23, 24, 25, 36, 35, 34], 11: [25, 26, 27, 38, 37, 36],
            12: [29, 30, 31, 41, 40, 39], 13: [31, 32, 33, 43, 42, 41], 14: [33, 34, 35, 45, 44, 43],
            15: [35, 36, 37, 47, 46, 45], 16: [40, 41, 42, 50, 49, 48], 17: [42, 43, 44, 52, 51, 50],
            18: [44, 45, 46, 53, 52, 51]
        }

        for i in range(54):
            self.graph.addVertex(i)

        all_edges = set()
        for tile_index in self.tile_to_vertices:
            vertices = self.tile_to_vertices[tile_index]
            for i in range(len(vertices)):
                v1 = vertices[i]
                v2 = vertices[(i + 1) % len(vertices)]
                edge = tuple(sorted((v1, v2)))
                all_edges.add(edge)

        for edge in all_edges:
            self.graph.addEdge(edge[0], edge[1])

    def _create_vertex_tile_map(self):
        for tile_index, vertices in self.tile_to_vertices.items():
            for vertex in vertices:
                if vertex not in self.vertex_tile_map:
                    self.vertex_tile_map[vertex] = []
                self.vertex_tile_map[vertex].append(tile_index)

    def get_tiles_for_settlement(self, settlement_location):
        tile_indices = self.vertex_tile_map.get(settlement_location, [])
        return [self.tiles[i] for i in tile_indices]

    def _create_harbors(self):
        # Hardcoded harbor locations (vertex pairs)
        harbor_locations = [
            (0, 1), (3, 4), (7, 17), (15, 25), (27, 38),
            (35, 36), (40, 41), (43, 44), (50, 51)
        ]

        harbor_types = [
            Harbor(3), Harbor(3), Harbor(3), Harbor(3),
            Harbor(2, Resource.WOOL), Harbor(2, Resource.GRAIN),
            Harbor(2, Resource.LUMBER), Harbor(2, Resource.BRICK),
            Harbor(2, Resource.ORE)
        ]
        random.shuffle(harbor_types)

        self.harbors = []
        for i in range(len(harbor_locations)):
            harbor = harbor_types[i]
            harbor.location = harbor_locations[i]
            self.harbors.append(harbor)
