import random

from catan.src.components import Harbor, Resource, Tile
from catan.src.graph import Graph


# Canonical 19-hex Catan layout. The 54 vertex ids are numbered row-by-row
# (top-to-bottom, left-to-right) over the physical board, and each tile lists
# its six vertices in clockwise corner order. This mapping is a valid planar
# hex tessellation: every vertex touches at most 3 tiles and has degree <= 3.
TILE_TO_VERTICES = {
    0: [4, 8, 12, 7, 3, 0],
    1: [5, 9, 13, 8, 4, 1],
    2: [6, 10, 14, 9, 5, 2],
    3: [12, 17, 22, 16, 11, 7],
    4: [13, 18, 23, 17, 12, 8],
    5: [14, 19, 24, 18, 13, 9],
    6: [15, 20, 25, 19, 14, 10],
    7: [22, 28, 33, 27, 21, 16],
    8: [23, 29, 34, 28, 22, 17],
    9: [24, 30, 35, 29, 23, 18],
    10: [25, 31, 36, 30, 24, 19],
    11: [26, 32, 37, 31, 25, 20],
    12: [34, 39, 43, 38, 33, 28],
    13: [35, 40, 44, 39, 34, 29],
    14: [36, 41, 45, 40, 35, 30],
    15: [37, 42, 46, 41, 36, 31],
    16: [44, 48, 51, 47, 43, 39],
    17: [45, 49, 52, 48, 44, 40],
    18: [46, 50, 53, 49, 45, 41],
}

# Harbor vertex pairs (perimeter edges that border the sea), spread around
# the coastline of the layout above.
HARBOR_LOCATIONS = [
    (33, 38),
    (16, 21),
    (3, 7),
    (1, 5),
    (6, 10),
    (20, 26),
    (42, 46),
    (49, 53),
    (48, 51),
]


class Board:
    def __init__(self, seed=None):
        if seed is not None:
            self._rng = random.Random(seed)
        else:
            self._rng = random
        self.graph = Graph()
        self.tiles = self._create_tiles()
        self.robber_location = self._initial_robber_location()
        self.vertex_tile_map = {}
        self.tile_to_vertices = {k: list(v) for k, v in TILE_TO_VERTICES.items()}
        self.edges = set()  # set[tuple[int,int]] - all board edges (sorted)
        self.harbors = []
        self._create_board_graph()
        self._create_vertex_tile_map()
        self._create_harbors()

    # ---------- construction ----------

    def _create_tiles(self):
        resources = [
            Resource.LUMBER, Resource.LUMBER, Resource.LUMBER, Resource.LUMBER,
            Resource.WOOL, Resource.WOOL, Resource.WOOL, Resource.WOOL,
            Resource.GRAIN, Resource.GRAIN, Resource.GRAIN, Resource.GRAIN,
            Resource.BRICK, Resource.BRICK, Resource.BRICK,
            Resource.ORE, Resource.ORE, Resource.ORE,
        ]
        self._rng.shuffle(resources)

        numbers = [2, 3, 3, 4, 4, 5, 5, 6, 6, 8, 8, 9, 9, 10, 10, 11, 11, 12]
        self._rng.shuffle(numbers)

        tiles = []
        for i in range(len(resources)):
            tiles.append(Tile(resources[i], numbers[i]))

        # Desert replaces a random slot and produces no resource (number 7).
        desert_index = self._rng.randint(0, len(tiles))
        tiles.insert(desert_index, Tile(None, 7))
        self._desert_index = desert_index
        return tiles

    def _initial_robber_location(self):
        return self._desert_index

    def _create_board_graph(self):
        for i in range(54):
            self.graph.addVertex(i)

        for vertices in self.tile_to_vertices.values():
            for i in range(len(vertices)):
                v1 = vertices[i]
                v2 = vertices[(i + 1) % len(vertices)]
                edge = tuple(sorted((v1, v2)))
                self.edges.add(edge)
                self.graph.addEdge(edge[0], edge[1])
                self.graph.addEdge(edge[1], edge[0])

    def _create_vertex_tile_map(self):
        for tile_index, vertices in self.tile_to_vertices.items():
            for vertex in vertices:
                self.vertex_tile_map.setdefault(vertex, []).append(tile_index)

    def _create_harbors(self):
        harbor_types = [
            Harbor(3), Harbor(3), Harbor(3), Harbor(3),
            Harbor(2, Resource.WOOL), Harbor(2, Resource.GRAIN),
            Harbor(2, Resource.LUMBER), Harbor(2, Resource.BRICK),
            Harbor(2, Resource.ORE),
        ]
        self._rng.shuffle(harbor_types)
        self.harbors = []
        for i, loc in enumerate(HARBOR_LOCATIONS):
            harbor = harbor_types[i]
            harbor.location = loc
            self.harbors.append(harbor)

    # ---------- queries ----------

    def get_tiles_for_settlement(self, vertex):
        tile_indices = self.vertex_tile_map.get(vertex, [])
        return [self.tiles[i] for i in tile_indices]

    def normalised_edge(self, edge):
        a, b = edge
        return tuple(sorted((int(a), int(b))))

    def is_edge(self, edge):
        return self.normalised_edge(edge) in self.edges

    def vertex_neighbors(self, vertex):
        v = self.graph.getVertex(vertex)
        if v is None:
            return []
        return [n.getId() for n in v.getConnections()]

    def vertices_on_tile(self, tile_index):
        return list(self.tile_to_vertices.get(tile_index, []))
