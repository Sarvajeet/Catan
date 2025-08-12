import random
from catan.src.components import Tile, Resource, Hex, hex_neighbor
from catan.src.graph import Graph

class Board:
    def __init__(self):
        self.graph = Graph()
        self.tiles = {}
        self._create_tiles()
        self._create_board_graph()

    def _get_hex_coords(self):
        coords = []
        for q in range(-2, 3):
            r1 = max(-2, -q - 2)
            r2 = min(2, -q + 2)
            for r in range(r1, r2 + 1):
                coords.append(Hex(q, r, -q - r))
        return coords

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

        # Add the desert tile
        desert_index = random.randint(0, len(resources))
        resources.insert(desert_index, None)
        numbers.insert(desert_index, 7)

        hex_coords = self._get_hex_coords()
        for i, hex_coord in enumerate(hex_coords):
            resource = resources[i]
            number = numbers[i]
            if resource is None:
                number = 7
            self.tiles[hex_coord] = Tile(resource, number)


    def _create_board_graph(self):
        all_vertices = set()
        for h in self.tiles:
            for i in range(6):
                n1 = hex_neighbor(h, i)
                n2 = hex_neighbor(h, (i + 1) % 6)

                vertex_tiles = {h}
                if n1 in self.tiles:
                    vertex_tiles.add(n1)
                if n2 in self.tiles:
                    vertex_tiles.add(n2)

                all_vertices.add(frozenset(vertex_tiles))

        self.vertex_map = {}
        vertex_id = 0
        for v_tiles in all_vertices:
            self.graph.addVertex(vertex_id)
            self.vertex_map[v_tiles] = vertex_id
            vertex_id += 1

        self.reverse_vertex_map = {v: k for k, v in self.vertex_map.items()}

        for h in self.tiles:
            tile_vertices_fs = []
            for i in range(6):
                n1 = hex_neighbor(h, i)
                n2 = hex_neighbor(h, (i + 1) % 6)

                vertex_tiles = {h}
                if n1 in self.tiles:
                    vertex_tiles.add(n1)
                if n2 in self.tiles:
                    vertex_tiles.add(n2)

                tile_vertices_fs.append(frozenset(vertex_tiles))

            for i in range(6):
                v1_fs = tile_vertices_fs[i]
                v2_fs = tile_vertices_fs[(i + 1) % 6]

                v1_id = self.vertex_map.get(v1_fs)
                v2_id = self.vertex_map.get(v2_fs)

                if v1_id is not None and v2_id is not None:
                    self.graph.addEdge(v1_id, v2_id)

    def get_tiles_for_settlement(self, settlement_location):
        # settlement_location is a frozenset of Hex objects
        return [self.tiles[h] for h in settlement_location if h in self.tiles]

    def get_vertices_for_settlement(self, settlement_location):
        # settlement_location is a frozenset of Hex objects
        vertex_id = self.vertex_map.get(settlement_location)
        if vertex_id is None:
            return []

        vertex = self.graph.getVertex(vertex_id)
        if not vertex:
            return []

        neighbor_verts = vertex.getConnections()

        return [self.reverse_vertex_map[v.getId()] for v in neighbor_verts]
