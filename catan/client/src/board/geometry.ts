// Hex/board layout constants — a single source of truth used by both the
// board renderer and hit-testing for vertices/edges.
//
// The canonical Catan layout is arranged in 5 rows of 3/4/5/4/3 hexes.
// Vertex ids 0..53 match catan/src/board.py::TILE_TO_VERTICES.

export const HEX_SIZE = 62;
export const BOARD_WIDTH = 760;
export const BOARD_HEIGHT = 780;

// Axial (col, row) coordinates for the 19 tiles matching TILE_TO_VERTICES order.
export const TILE_GRID: Array<[number, number]> = [
  [0, 0], [1, 0], [2, 0],
  [-0.5, 1], [0.5, 1], [1.5, 1], [2.5, 1],
  [-1, 2], [0, 2], [1, 2], [2, 2], [3, 2],
  [-0.5, 3], [0.5, 3], [1.5, 3], [2.5, 3],
  [0, 4], [1, 4], [2, 4],
];

export function tileCenter(tileIndex: number): { x: number; y: number } {
  const [col, row] = TILE_GRID[tileIndex];
  // Flat-top hex: horizontal spacing = size * sqrt(3); vertical = size * 1.5
  const dx = HEX_SIZE * Math.sqrt(3);
  const dy = HEX_SIZE * 1.5;
  const originX = BOARD_WIDTH / 2 - dx;
  const originY = HEX_SIZE * 1.3;
  return { x: originX + col * dx, y: originY + row * dy };
}

export function hexCorners(cx: number, cy: number): Array<{ x: number; y: number }> {
  // Pointy-top corners (angles 30,90,150,210,270,330) — but we're using flat-top
  // layout above, so use 0,60,...300. We'll stay consistent: flat-top hex has
  // corners at angles -30,30,90,150,210,270 from center.
  const pts: Array<{ x: number; y: number }> = [];
  for (let i = 0; i < 6; i++) {
    const angle = (Math.PI / 180) * (60 * i - 30);
    pts.push({ x: cx + HEX_SIZE * Math.cos(angle), y: cy + HEX_SIZE * Math.sin(angle) });
  }
  return pts;
}

export interface VertexPosition {
  id: number;
  x: number;
  y: number;
}

export function computeVertexPositions(tileToVertices: Record<string, number[]>): Map<number, VertexPosition> {
  // The server sends the six vertex ids for each tile in order matching the
  // corner order returned by hexCorners (starting at angle -30° and going
  // clockwise). We average positions coming from different tiles to tolerate
  // small floating-point differences.
  const acc = new Map<number, { x: number; y: number; n: number }>();
  for (const [tileIdxStr, verts] of Object.entries(tileToVertices)) {
    const tileIdx = Number(tileIdxStr);
    if (tileIdx < 0 || tileIdx >= TILE_GRID.length) continue;
    const { x: cx, y: cy } = tileCenter(tileIdx);
    const corners = hexCorners(cx, cy);
    for (let i = 0; i < 6 && i < verts.length; i++) {
      const vId = verts[i];
      const corner = corners[i];
      const prev = acc.get(vId);
      if (prev) {
        acc.set(vId, {
          x: prev.x + corner.x,
          y: prev.y + corner.y,
          n: prev.n + 1,
        });
      } else {
        acc.set(vId, { x: corner.x, y: corner.y, n: 1 });
      }
    }
  }
  const result = new Map<number, VertexPosition>();
  for (const [id, v] of acc) {
    result.set(id, { id, x: v.x / v.n, y: v.y / v.n });
  }
  return result;
}

export function edgeMidpoint(
  a: VertexPosition,
  b: VertexPosition,
): { x: number; y: number; angle: number } {
  const mx = (a.x + b.x) / 2;
  const my = (a.y + b.y) / 2;
  const angle = (Math.atan2(b.y - a.y, b.x - a.x) * 180) / Math.PI;
  return { x: mx, y: my, angle };
}

export const RESOURCE_FILL: Record<string, string> = {
  LUMBER: "#27632a",
  BRICK: "#b34722",
  WOOL: "#8ac64a",
  GRAIN: "#e6b23a",
  ORE: "#6d7784",
  DESERT: "#d9b26b",
};

// Lighter shade of each resource color, used as the top stop of the per-hex
// SVG gradients so tiles read with depth instead of flat fills.
export const RESOURCE_FILL_LIGHT: Record<string, string> = {
  LUMBER: "#3c9140",
  BRICK: "#d06a44",
  WOOL: "#a8dd6e",
  GRAIN: "#f4cd6a",
  ORE: "#8b95a3",
  DESERT: "#ecd29a",
};

// Unicode glyphs rendered on each tile to make resources instantly identifiable.
export const RESOURCE_ICON: Record<string, string> = {
  LUMBER: "\uD83C\uDF32", // evergreen tree
  BRICK: "\uD83E\uDDF1", // brick
  WOOL: "\uD83D\uDC11", // sheep
  GRAIN: "\uD83C\uDF3E", // sheaf of rice
  ORE: "\u26F0\uFE0F", // mountain
  DESERT: "\uD83C\uDFDC\uFE0F", // desert
};

export const RESOURCE_LABEL: Record<string, string> = {
  LUMBER: "Lumber",
  BRICK: "Brick",
  WOOL: "Wool",
  GRAIN: "Grain",
  ORE: "Ore",
  DESERT: "Desert",
};

// Pip counts for number tokens (probability dots)
export const NUMBER_PIPS: Record<number, number> = {
  2: 1,
  3: 2,
  4: 3,
  5: 4,
  6: 5,
  8: 5,
  9: 4,
  10: 3,
  11: 2,
  12: 1,
};
