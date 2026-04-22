import { useMemo } from "react";
import { motion } from "framer-motion";
import { useGameStore } from "../stores/gameStore";
import type { GameStateDTO } from "../types";
import {
  BOARD_HEIGHT,
  BOARD_WIDTH,
  NUMBER_PIPS,
  RESOURCE_FILL,
  RESOURCE_ICON,
  RESOURCE_LABEL,
  computeVertexPositions,
  edgeMidpoint,
  hexCorners,
  tileCenter,
  type VertexPosition,
} from "../board/geometry";

interface Props {
  state: GameStateDTO;
}

export function BoardCanvas({ state }: Props) {
  const { board } = state;
  const buildMode = useGameStore((s) => s.buildMode);
  const username = useGameStore((s) => s.username);

  const vertexPositions = useMemo(
    () => computeVertexPositions(board.tile_to_vertices),
    [board.tile_to_vertices],
  );

  // Lookup: vertex -> owner (player color + type)
  const vertexOwner = new Map<number, { color: string; type: "settlement" | "city"; pattern: boolean }>();
  for (const [name, p] of Object.entries(state.players)) {
    const pattern = shouldUsePattern(state.player_order.indexOf(name));
    for (const v of p.settlements) vertexOwner.set(v, { color: p.color, type: "settlement", pattern });
    for (const v of p.cities) vertexOwner.set(v, { color: p.color, type: "city", pattern });
  }

  // Lookup: edge -> owner
  const edgeOwner = new Map<string, { color: string; pattern: boolean }>();
  for (const [name, p] of Object.entries(state.players)) {
    const pattern = shouldUsePattern(state.player_order.indexOf(name));
    for (const [a, b] of p.roads) {
      edgeOwner.set(edgeKey(a, b), { color: p.color, pattern });
    }
  }

  // Harbor vertex pairs
  const harborAt = new Map<string, { ratio: number; resource: string | null }>();
  for (const h of board.harbors) {
    if (!h.location) continue;
    harborAt.set(edgeKey(h.location[0], h.location[1]), {
      ratio: h.ratio,
      resource: h.resource,
    });
  }

  const clickVertex = (vId: number) => {
    const st = useGameStore.getState();
    const bm = st.buildMode.type;
    if (bm === "setup_settlement") st.placeSetupSettlement(vId);
    else if (bm === "settlement") st.buildSettlement(vId);
    else if (bm === "city") st.buildCity(vId);
  };

  const clickEdge = (a: number, b: number) => {
    const st = useGameStore.getState();
    const mode = st.buildMode;
    if (mode.type === "setup_road") st.placeSetupRoad([a, b]);
    else if (mode.type === "road") st.buildRoad([a, b]);
    else if (mode.type === "road_building_1") {
      st.setBuildMode({ type: "road_building_2", first: [a, b] });
    } else if (mode.type === "road_building_2") {
      st.playDevCard("road_building", { edge1: mode.first, edge2: [a, b] });
      st.setBuildMode({ type: "none" });
    }
  };

  const clickHex = (idx: number) => {
    const st = useGameStore.getState();
    if (st.buildMode.type === "move_robber") {
      st.moveRobber(idx);
    }
  };

  const canClickHex = buildMode.type === "move_robber";
  const isSetupPhase = state.phase === "SETUP_1" || state.phase === "SETUP_2";
  const isMyTurn = state.current_player === username;
  const canClickVertex =
    buildMode.type === "setup_settlement" ||
    buildMode.type === "settlement" ||
    buildMode.type === "city";
  const canClickEdge =
    buildMode.type === "setup_road" ||
    buildMode.type === "road" ||
    buildMode.type === "road_building_1" ||
    buildMode.type === "road_building_2";
  const setupPivot =
    buildMode.type === "setup_road" && state.setup?.expects_road_for != null
      ? state.setup.expects_road_for
      : null;

  return (
    <svg
      viewBox={`0 0 ${BOARD_WIDTH} ${BOARD_HEIGHT}`}
      className="w-full h-full select-none"
      role="img"
      aria-label="Catan board"
    >
      {/* Sea background */}
      <rect width={BOARD_WIDTH} height={BOARD_HEIGHT} fill="#143a5c" />

      {/* Harbor lines: short segments near sea edges */}
      {board.harbors.map((h, i) =>
        h.location ? (
          <g key={`harbor-${i}`} opacity={0.85} style={{ pointerEvents: "none" }}>
            <HarborMarker
              location={h.location}
              ratio={h.ratio}
              resource={h.resource}
              vertexPositions={vertexPositions}
            />
          </g>
        ) : null,
      )}

      {/* Tiles */}
      {board.tiles.map((tile, idx) => {
        const { x, y } = tileCenter(idx);
        const corners = hexCorners(x, y);
        const pointsStr = corners.map((p) => `${p.x},${p.y}`).join(" ");
        const fill = RESOURCE_FILL[tile.resource] ?? "#333";
        const isRobber = idx === board.robber_location;
        return (
          <g
            key={`tile-${idx}`}
            className={canClickHex ? "cursor-pointer" : ""}
            onClick={canClickHex ? () => clickHex(idx) : undefined}
            style={{ pointerEvents: canClickHex ? "auto" : "none" }}
          >
            <title>
              {`${tile.resource}${tile.number !== 7 ? ` · rolls on ${tile.number}` : ""}${isRobber ? " · robber here" : ""}`}
            </title>
            <polygon
              points={pointsStr}
              fill={fill}
              stroke="#0c1c2b"
              strokeWidth={2}
              style={{
                filter: canClickHex && !isRobber ? "drop-shadow(0 0 6px #ffd166)" : undefined,
              }}
            />
            <ResourceBadge cx={x} cy={y - 26} resource={tile.resource} />
            {tile.number !== 7 && (
              <NumberToken cx={x} cy={y + 18} number={tile.number} />
            )}
            {isRobber && <Robber cx={x} cy={y + 4} />}
          </g>
        );
      })}

      {/* Edges (roads) — render all board edges so we can click; owned ones styled */}
      {board.edges.map(([a, b]) => {
        const va = vertexPositions.get(a);
        const vb = vertexPositions.get(b);
        if (!va || !vb) return null;
        const key = edgeKey(a, b);
        const owner = edgeOwner.get(key);
        const highlight = canClickEdge;
        const isLegalSetupEdge =
          setupPivot !== null && (a === setupPivot || b === setupPivot);
        return (
          <g
            key={`edge-${key}`}
            className={highlight ? "edge-hit" : ""}
            onClick={canClickEdge ? () => clickEdge(a, b) : undefined}
            style={{ pointerEvents: canClickEdge ? "auto" : "none" }}
          >
            {/* Invisible wide hit target so edges are easy to click/tap */}
            {highlight && !owner && (
              <line
                x1={va.x}
                y1={va.y}
                x2={vb.x}
                y2={vb.y}
                stroke="transparent"
                strokeWidth={20}
                strokeLinecap="round"
              />
            )}
            {highlight && !owner && (
              <line
                x1={va.x}
                y1={va.y}
                x2={vb.x}
                y2={vb.y}
                stroke="#ffd166"
                strokeWidth={isLegalSetupEdge ? 8 : 4}
                strokeLinecap="round"
                opacity={isLegalSetupEdge ? 0.9 : 0.35}
                className="edge-line"
                style={{
                  filter: isLegalSetupEdge
                    ? "drop-shadow(0 0 6px #ffd166)"
                    : undefined,
                }}
              />
            )}
            {owner && (
              <line
                x1={va.x}
                y1={va.y}
                x2={vb.x}
                y2={vb.y}
                stroke={owner.color}
                strokeWidth={7}
                strokeLinecap="round"
                style={owner.pattern ? { strokeDasharray: "6 3" } : undefined}
              />
            )}
          </g>
        );
      })}

      {/* Vertices */}
      {Array.from(vertexPositions.values()).map((v) => {
        const owner = vertexOwner.get(v.id);
        const highlight = canClickVertex;
        return (
          <g
            key={`v-${v.id}`}
            className={highlight ? "vertex-hit" : ""}
            onClick={canClickVertex ? () => clickVertex(v.id) : undefined}
            style={{ pointerEvents: canClickVertex || owner ? "auto" : "none" }}
          >
            {/* Invisible wide hit target for easier clicking */}
            {highlight && !owner && (
              <circle cx={v.x} cy={v.y} r={18} fill="transparent" />
            )}
            {highlight && !owner && (
              <circle
                cx={v.x}
                cy={v.y}
                r={10}
                fill="#ffd166"
                opacity={0.4}
                className="vertex-dot"
              />
            )}
            {owner?.type === "settlement" && (
              <polygon
                points={settlementPoints(v.x, v.y)}
                fill={owner.color}
                stroke="white"
                strokeWidth={2}
                style={owner.pattern ? { strokeDasharray: "2 2" } : undefined}
              />
            )}
            {owner?.type === "city" && (
              <rect
                x={v.x - 10}
                y={v.y - 10}
                width={20}
                height={20}
                fill={owner.color}
                stroke="white"
                strokeWidth={2}
                style={owner.pattern ? { strokeDasharray: "2 2" } : undefined}
              />
            )}
          </g>
        );
      })}

      {/* Setup phase "must place road on..." hint */}
      {isSetupPhase && isMyTurn && state.setup?.expects_road_for != null && (
        <SetupHint
          vertex={state.setup.expects_road_for}
          vertexPositions={vertexPositions}
        />
      )}
    </svg>
  );
}

function settlementPoints(cx: number, cy: number): string {
  // Simple house shape
  const s = 9;
  return `${cx - s},${cy + s} ${cx - s},${cy} ${cx},${cy - s} ${cx + s},${cy} ${cx + s},${cy + s}`;
}

function edgeKey(a: number, b: number): string {
  const [lo, hi] = a < b ? [a, b] : [b, a];
  return `${lo}-${hi}`;
}

function shouldUsePattern(index: number): boolean {
  // Alternate players get a patterned overlay for color-blind accessibility.
  return index % 2 === 1;
}

function NumberToken({ cx, cy, number }: { cx: number; cy: number; number: number }) {
  const red = number === 6 || number === 8;
  return (
    <g>
      <circle cx={cx} cy={cy} r={18} fill="#f3eedc" stroke="#222" strokeWidth={1.5} />
      <text
        x={cx}
        y={cy - 1}
        textAnchor="middle"
        fontSize={18}
        fontWeight={700}
        fill={red ? "#b31212" : "#222"}
      >
        {number}
      </text>
      <text
        x={cx}
        y={cy + 12}
        textAnchor="middle"
        fontSize={10}
        fill={red ? "#b31212" : "#444"}
      >
        {".".repeat(NUMBER_PIPS[number] ?? 0)}
      </text>
    </g>
  );
}

function ResourceBadge({
  cx,
  cy,
  resource,
}: {
  cx: number;
  cy: number;
  resource: string;
}) {
  const icon = RESOURCE_ICON[resource] ?? "";
  const label = RESOURCE_LABEL[resource] ?? resource;
  return (
    <g pointerEvents="none">
      <text
        x={cx}
        y={cy}
        textAnchor="middle"
        fontSize={26}
        style={{ userSelect: "none" }}
      >
        {icon}
      </text>
      <text
        x={cx}
        y={cy + 14}
        textAnchor="middle"
        fontSize={10}
        fontWeight={700}
        fill="#0c1c2b"
        stroke="#f3eedc"
        strokeWidth={2.5}
        paintOrder="stroke"
        style={{ letterSpacing: 0.5, userSelect: "none" }}
      >
        {label.toUpperCase()}
      </text>
    </g>
  );
}

function Robber({ cx, cy }: { cx: number; cy: number }) {
  return (
    <motion.g
      initial={{ opacity: 0, scale: 0.5 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ type: "spring", stiffness: 300 }}
    >
      <ellipse cx={cx} cy={cy + 10} rx={10} ry={4} fill="#00000055" />
      <circle cx={cx} cy={cy - 6} r={6} fill="#111" />
      <polygon
        points={`${cx - 9},${cy + 10} ${cx + 9},${cy + 10} ${cx + 6},${cy - 2} ${cx - 6},${cy - 2}`}
        fill="#111"
      />
    </motion.g>
  );
}

function SetupHint({
  vertex,
  vertexPositions,
}: {
  vertex: number;
  vertexPositions: Map<number, VertexPosition>;
}) {
  const v = vertexPositions.get(vertex);
  if (!v) return null;
  return (
    <motion.circle
      cx={v.x}
      cy={v.y}
      r={16}
      fill="none"
      stroke="#ffd166"
      strokeWidth={2}
      animate={{ r: [16, 22, 16] }}
      transition={{ duration: 1.2, repeat: Infinity }}
    />
  );
}

function HarborMarker({
  location,
  ratio,
  resource,
  vertexPositions,
}: {
  location: [number, number];
  ratio: number;
  resource: string | null;
  vertexPositions: Map<number, VertexPosition>;
}) {
  const a = vertexPositions.get(location[0]);
  const b = vertexPositions.get(location[1]);
  if (!a || !b) return null;
  const mid = edgeMidpoint(a, b);
  const label = resource ? `2:1 ${resource[0]}` : `${ratio}:1`;
  return (
    <g transform={`translate(${mid.x}, ${mid.y})`}>
      <circle r={14} fill="#23445c" stroke="#ffd166" strokeWidth={1.5} />
      <text textAnchor="middle" fontSize={9} fill="#ffd166" y={3} fontWeight={700}>
        {label}
      </text>
    </g>
  );
}
