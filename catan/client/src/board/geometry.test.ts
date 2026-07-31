import { describe, it, expect } from "vitest";
import {
  BOARD_WIDTH,
  HEX_SIZE,
  NUMBER_PIPS,
  RESOURCE_FILL,
  RESOURCE_FILL_LIGHT,
  RESOURCE_LABEL,
  TILE_GRID,
  computeVertexPositions,
  edgeMidpoint,
  hexCorners,
  tileCenter,
} from "./geometry";

describe("tileCenter", () => {
  it("produces a center for all 19 tiles", () => {
    const centers = TILE_GRID.map((_, i) => tileCenter(i));
    expect(centers).toHaveLength(19);
    for (const c of centers) {
      expect(Number.isFinite(c.x)).toBe(true);
      expect(Number.isFinite(c.y)).toBe(true);
    }
  });

  it("places every tile center at a distinct position", () => {
    const keys = new Set(TILE_GRID.map((_, i) => {
      const { x, y } = tileCenter(i);
      return `${x.toFixed(2)},${y.toFixed(2)}`;
    }));
    expect(keys.size).toBe(19);
  });
});

describe("hexCorners", () => {
  it("returns exactly 6 corners", () => {
    expect(hexCorners(100, 100)).toHaveLength(6);
  });

  it("places every corner at HEX_SIZE distance from the center", () => {
    const cx = 100;
    const cy = 100;
    for (const p of hexCorners(cx, cy)) {
      const d = Math.hypot(p.x - cx, p.y - cy);
      expect(d).toBeCloseTo(HEX_SIZE, 5);
    }
  });
});

describe("computeVertexPositions", () => {
  it("maps a single tile's six vertices to its six corners", () => {
    const map = computeVertexPositions({ "0": [0, 1, 2, 3, 4, 5] });
    const corners = hexCorners(tileCenter(0).x, tileCenter(0).y);
    expect(map.size).toBe(6);
    corners.forEach((corner, i) => {
      const v = map.get(i)!;
      expect(v.x).toBeCloseTo(corner.x, 5);
      expect(v.y).toBeCloseTo(corner.y, 5);
    });
  });

  it("averages the positions of a vertex shared across two tiles", () => {
    // Vertex id 0 sits at corner 0 of tile 0 and corner 5 of tile 1.
    const map = computeVertexPositions({
      "0": [0, 1, 2, 3, 4, 5],
      "1": [6, 7, 8, 9, 10, 0],
    });
    const t0 = hexCorners(tileCenter(0).x, tileCenter(0).y)[0];
    const t1 = hexCorners(tileCenter(1).x, tileCenter(1).y)[5];
    const shared = map.get(0)!;
    expect(shared.x).toBeCloseTo((t0.x + t1.x) / 2, 5);
    expect(shared.y).toBeCloseTo((t0.y + t1.y) / 2, 5);
  });

  it("ignores tile indices outside the board grid", () => {
    const map = computeVertexPositions({ "999": [0, 1, 2, 3, 4, 5] });
    expect(map.size).toBe(0);
  });
});

describe("edgeMidpoint", () => {
  it("computes the midpoint and angle of an edge", () => {
    const mid = edgeMidpoint({ id: 0, x: 0, y: 0 }, { id: 1, x: 10, y: 0 });
    expect(mid.x).toBe(5);
    expect(mid.y).toBe(0);
    expect(mid.angle).toBeCloseTo(0, 5);
  });

  it("reports a 90° angle for a vertical edge", () => {
    const mid = edgeMidpoint({ id: 0, x: 0, y: 0 }, { id: 1, x: 0, y: 10 });
    expect(mid.angle).toBeCloseTo(90, 5);
  });
});

describe("resource color maps", () => {
  const keys = ["LUMBER", "BRICK", "WOOL", "GRAIN", "ORE", "DESERT"];

  it("defines a base + lighter gradient color for every resource", () => {
    for (const k of keys) {
      expect(RESOURCE_FILL[k]).toMatch(/^#[0-9a-f]{6}$/i);
      expect(RESOURCE_FILL_LIGHT[k]).toMatch(/^#[0-9a-f]{6}$/i);
      expect(RESOURCE_FILL_LIGHT[k]).not.toBe(RESOURCE_FILL[k]);
    }
  });

  it("has a human label for every resource", () => {
    for (const k of keys) expect(RESOURCE_LABEL[k]).toBeTruthy();
  });

  it("centers board layout horizontally", () => {
    expect(BOARD_WIDTH).toBeGreaterThan(0);
  });
});

describe("NUMBER_PIPS", () => {
  it("assigns the most pips to 6 and 8", () => {
    expect(NUMBER_PIPS[6]).toBe(5);
    expect(NUMBER_PIPS[8]).toBe(5);
  });

  it("assigns the fewest pips to 2 and 12", () => {
    expect(NUMBER_PIPS[2]).toBe(1);
    expect(NUMBER_PIPS[12]).toBe(1);
  });

  it("is symmetric around 7", () => {
    for (let n = 2; n <= 6; n++) {
      expect(NUMBER_PIPS[n]).toBe(NUMBER_PIPS[14 - n]);
    }
  });
});
