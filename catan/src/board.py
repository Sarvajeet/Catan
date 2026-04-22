import random

from catan.src.components import Harbor, Resource, Tile
from catan.src.graph import Graph


# Canonical 19-hex Catan layout. Vertex ids 0..53 are assigned row-by-row
# from the top-left corner of the board.
TILE_TO_VERTICES = {
    0: [0, 1, 2, 10, 9, 8],
    1: [2, 3, 4, 12, 11, 10],
    2: [4, 5, 6, 14, 13, 12],
    3: [7, 8, 9, 19, 18, 17],
    4: [9, 10, 11, 21, 20, 19],
    5: [11, 12, 13, 23, 22, 21],
    6: [13, 14, 15, 25, 24, 23],
    7: [17, 18, 19, 30, 29, 28],
    8: [19, 20, 21, 32, 31, 30],
    9: [21, 22, 23, 34, 33, 32],
    10: [23, 24, 25, 36, 35, 34],
    11: [25, 26, 27, 38, 37, 36],
    12: [29, 30, 31, 41, 40, 39],
    13: [31, 32, 33, 43, 42, 41],
    14: [33, 34, 35, 45, 44, 43],
    15: [35, 36, 37, 47, 46, 45],
    16: [40, 41, 42, 50, 49, 48],
    17: [42, 43, 44, 52, 51, 50],
    18: [44, 45, 46, 53, 52, 51],
}

# Harbor vertex pairs (edges that border the sea) - canonical layout
HARBOR_LOCATIONS = [
    (0, 1),
    (3, 4),
    (7, 17),
    (15, 25),
    (27, 38),
    (35, 47),
    (39, 48),
    (44, 53),
    (50, 51),
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
