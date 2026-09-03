import { useMemo } from "react";
import { motion } from "framer-motion";
import { useGameStore } from "../stores/gameStore";
import type { GameStateDTO } from "../types";
import {
  BOARD_HEIGHT,
  BOARD_WIDTH,
  NUMBER_PIPS,
  RESOURCE_FILL,
  RESOURCE_FILL_LIGHT,
  RESOURCE_LABEL,
  computeVertexPositions,
  edgeMidpoint,
  hexCorners,
  tileCenter,
  type VertexPosition,
} from "../board/geometry";
import { BoardResourceIcon } from "./icons/ResourceIcons";

const RESOURCE_KEYS = ["LUMBER", "BRICK", "WOOL", "GRAIN", "ORE", "DESERT"];

// Harbor markers cluttered the coastline; hidden for now. Maritime trade still
// works through the Trade menu regardless of this flag.
const SHOW_HARBORS = false;

interface Props {
  state: GameStateDTO;
}

export function BoardCanvas({ state }: Props) {
  const { board } = state;
  const buildMode = useGameStore((s) => s.buildMode);
  const username = useGameStore((s) => s.username);
  const myColor = state.players[username]?.color ?? "#ffd166";

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
      <defs>
        {/* Per-resource vertical gradients (light top → base bottom) so hexes
            read with depth instead of flat fills. */}
        {RESOURCE_KEYS.map((r) => (
          <linearGradient key={`grad-${r}`} id={`hexgrad-${r}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={RESOURCE_FILL_LIGHT[r] ?? "#555"} />
            <stop offset="100%" stopColor={RESOURCE_FILL[r] ?? "#333"} />
          </linearGradient>
        ))}
        {/* Deep sea radial gradient. */}
        <radialGradient id="seagrad" cx="42%" cy="30%" r="80%">
          <stop offset="0%" stopColor="#1d4a72" />
          <stop offset="100%" stopColor="#0c2438" />
        </radialGradient>
        {/* Soft drop shadow used under tiles and tokens. */}
        <filter id="hexShadow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="2" stdDeviation="2.5" floodColor="#000" floodOpacity="0.35" />
        </filter>
        <filter id="tokenShadow" x="-40%" y="-40%" width="180%" height="180%">
          <feDropShadow dx="0" dy="1" stdDeviation="1.2" floodColor="#000" floodOpacity="0.45" />
        </filter>
      </defs>

      {/* Sea background */}
      <rect width={BOARD_WIDTH} height={BOARD_HEIGHT} fill="url(#seagrad)" />

      {/* Harbor markers around the coast. Hidden by default — maritime trade
          still works via the Trade menu. Flip SHOW_HARBORS to re-enable. */}
      {SHOW_HARBORS &&
        board.harbors.map((h, i) =>
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
        const gradFill = `url(#hexgrad-${tile.resource})`;
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
              fill={gradFill}
              stroke="#0c1c2b"
              strokeWidth={2}
              strokeLinejoin="round"
              style={{
                filter: canClickHex && !isRobber ? "drop-shadow(0 0 7px #ffd166)" : "url(#hexShadow)",
              }}
            />
            {/* Inner bevel highlight for a subtle raised look. */}
            <polygon
              points={pointsStr}
              fill="none"
              stroke="#ffffff"
              strokeOpacity={0.12}
              strokeWidth={1.5}
              transform={`translate(${x} ${y}) scale(0.9) translate(${-x} ${-y})`}
              style={{ pointerEvents: "none" }}
            />
            <ResourceBadge cx={x} cy={y - 24} resource={tile.resource} />
            {tile.number !== 7 && (
              <NumberToken cx={x} cy={y + 20} number={tile.number} />
            )}
            {isRobber && <Robber cx={x} cy={y + 2} />}
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
        // During setup the only legal roads are those touching the settlement
        // just placed. Outside setup (normal/road-building modes) any empty
        // edge is a candidate and the server validates the actual placement.
        const inSetupRoad = setupPivot !== null;
        const isLegalSetupEdge =
          inSetupRoad && (a === setupPivot || b === setupPivot);
        // Show/allow an edge only when it is a real candidate: skip the whole
        // board's edge web during setup and light up just the legal spots.
        const showEdge = canClickEdge && !owner && (!inSetupRoad || isLegalSetupEdge);
        return (
          <g
            key={`edge-${key}`}
            className={showEdge ? "edge-hit" : ""}
            onClick={showEdge ? () => clickEdge(a, b) : undefined}
            style={{ pointerEvents: showEdge ? "auto" : "none" }}
          >
            {/* Invisible wide hit target so edges are easy to click/tap */}
            {showEdge && (
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
            {showEdge && (
              <line
                x1={va.x}
                y1={va.y}
                x2={vb.x}
                y2={vb.y}
                stroke="#ffd166"
                strokeWidth={isLegalSetupEdge ? 8 : 4}
                strokeLinecap="round"
                opacity={isLegalSetupEdge ? 0.95 : 0.4}
                className="edge-line"
                style={{
                  filter: isLegalSetupEdge
                    ? "drop-shadow(0 0 6px #ffd166)"
                    : undefined,
                }}
              />
            )}
            {owner && (
              <>
                {/* Dark underlay so roads stay legible over any hex color. */}
                <line
                  x1={va.x}
                  y1={va.y}
                  x2={vb.x}
                  y2={vb.y}
                  stroke="#0c1c2b"
                  strokeWidth={10}
                  strokeLinecap="round"
                />
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
              </>
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
            {/* Hover-only ghost preview of the building being placed. */}
            {highlight && !owner && buildMode.type !== "city" && (
              <g className="vertex-ghost" opacity={0} style={{ pointerEvents: "none" }}>
                <SettlementShape x={v.x} y={v.y} color={myColor} pattern={false} />
              </g>
            )}
            {owner?.type === "settlement" && (
              <SettlementShape x={v.x} y={v.y} color={owner.color} pattern={owner.pattern} />
            )}
            {owner?.type === "city" && (
              <CityShape x={v.x} y={v.y} color={owner.color} pattern={owner.pattern} />
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

function SettlementShape({
  x,
  y,
  color,
  pattern,
}: {
  x: number;
  y: number;
  color: string;
  pattern: boolean;
}) {
  // A little house: pitched roof over a square body.
  const house = `M${x - 8} ${y + 8} L${x - 8} ${y - 1} L${x} ${y - 9} L${x + 8} ${y - 1} L${x + 8} ${y + 8} Z`;
  return (
    <g style={{ filter: "url(#tokenShadow)" }}>
      <path d={house} fill={color} stroke="#fff" strokeWidth={1.6} strokeLinejoin="round" />
      {/* Roof shading + door for a touch of depth. */}
      <path d={`M${x - 8} ${y - 1} L${x} ${y - 9} L${x + 8} ${y - 1} Z`} fill="#000" fillOpacity={0.18} />
      <rect x={x - 2} y={y + 2} width={4} height={6} fill="#fff" fillOpacity={0.85} />
      {pattern && (
        <path d={house} fill="none" stroke="#fff" strokeWidth={1.2} strokeDasharray="2 2" />
      )}
    </g>
  );
}

function CityShape({
  x,
  y,
  color,
  pattern,
}: {
  x: number;
  y: number;
  color: string;
  pattern: boolean;
}) {
  // A two-tier structure so it reads as an upgrade from a settlement.
  const body = `M${x - 11} ${y + 9}
                L${x - 11} ${y - 1}
                L${x - 4} ${y - 1}
                L${x - 4} ${y - 6}
                L${x + 2} ${y - 10}
                L${x + 8} ${y - 6}
                L${x + 8} ${y - 1}
                L${x + 11} ${y - 1}
                L${x + 11} ${y + 9} Z`;
  return (
    <g style={{ filter: "url(#tokenShadow)" }}>
      <path d={body} fill={color} stroke="#fff" strokeWidth={1.6} strokeLinejoin="round" />
      {/* Windows */}
      <g fill="#fff" fillOpacity={0.85}>
        <rect x={x - 9} y={y + 1} width={2.6} height={2.6} />
        <rect x={x - 5} y={y + 1} width={2.6} height={2.6} />
        <rect x={x - 9} y={y + 5} width={2.6} height={2.6} />
        <rect x={x - 5} y={y + 5} width={2.6} height={2.6} />
        <rect x={x + 2.4} y={y + 1} width={2.6} height={2.6} />
        <rect x={x + 2.4} y={y + 5} width={2.6} height={2.6} />
      </g>
      {pattern && (
        <path d={body} fill="none" stroke="#fff" strokeWidth={1.2} strokeDasharray="2 2" />
      )}
    </g>
  );
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
  const pips = NUMBER_PIPS[number] ?? 0;
  const dotColor = red ? "#b31212" : "#4a4a4a";
  const dotGap = 3.2;
  const startX = cx - ((pips - 1) * dotGap) / 2;
  return (
    <g style={{ filter: "url(#tokenShadow)" }}>
      <circle cx={cx} cy={cy} r={17} fill="#f4efdd" stroke="#cbb98a" strokeWidth={2} />
      <circle cx={cx} cy={cy} r={13.5} fill="none" stroke={red ? "#b31212" : "#d8caa0"} strokeWidth={red ? 1.4 : 1} strokeOpacity={red ? 0.8 : 0.6} />
      <text
        x={cx}
        y={cy}
        textAnchor="middle"
        dominantBaseline="central"
        fontSize={red ? 18 : 16}
        fontWeight={800}
        fill={red ? "#b31212" : "#2a2a2a"}
        dy={-3}
      >
        {number}
      </text>
      <g fill={dotColor}>
        {Array.from({ length: pips }).map((_, i) => (
          <circle key={i} cx={startX + i * dotGap} cy={cy + 9} r={1.2} />
        ))}
      </g>
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
  const label = RESOURCE_LABEL[resource] ?? resource;
  return (
    <g pointerEvents="none">
      <BoardResourceIcon resource={resource} cx={cx} cy={cy} size={34} />
      <text
        x={cx}
        y={cy + 26}
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
  // A hooded-pawn silhouette so the robber reads clearly on any tile.
  return (
    <motion.g
      initial={{ opacity: 0, scale: 0.4, y: -8 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ type: "spring", stiffness: 300, damping: 18 }}
      style={{ filter: "url(#tokenShadow)" }}
    >
      <ellipse cx={cx} cy={cy + 15} rx={11} ry={3.5} fill="#00000055" />
      {/* Cloaked body */}
      <path
        d={`M${cx} ${cy - 14}
            C${cx + 9} ${cy - 14} ${cx + 11} ${cy - 2} ${cx + 10} ${cy + 12}
            L${cx - 10} ${cy + 12}
            C${cx - 11} ${cy - 2} ${cx - 9} ${cy - 14} ${cx} ${cy - 14} Z`}
        fill="#1b1b1f"
        stroke="#000"
        strokeWidth={1}
      />
      {/* Hood opening */}
      <ellipse cx={cx} cy={cy - 6} rx={4.5} ry={5.5} fill="#3a3a44" />
      <ellipse cx={cx} cy={cy - 5} rx={3} ry={4} fill="#111114" />
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
  const ratioText = `${ratio}:1`;
  return (
    <g transform={`translate(${mid.x}, ${mid.y})`} style={{ filter: "url(#tokenShadow)" }}>
      {/* Wooden dock plank */}
      <rect x={-16} y={-13} width={32} height={26} rx={5} fill="#5a3d24" stroke="#3a2716" strokeWidth={1.5} />
      <rect x={-13} y={-10} width={26} height={20} rx={3} fill="#7a5230" stroke="#e6b23a" strokeWidth={1} strokeOpacity={0.7} />
      {resource ? (
        <>
          <BoardResourceIcon resource={resource} cx={0} cy={-2} size={16} />
          <text textAnchor="middle" fontSize={7.5} fill="#ffe0a3" y={10} fontWeight={800}>
            {ratioText}
          </text>
        </>
      ) : (
        <text textAnchor="middle" fontSize={11} fill="#ffe0a3" y={4} fontWeight={800}>
          {ratioText}
        </text>
      )}
    </g>
  );
}
