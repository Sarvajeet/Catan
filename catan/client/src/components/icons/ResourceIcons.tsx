// Stylized inline-SVG resource icons.
//
// These replace the raw Unicode emoji that were previously rendered on the
// board and in the resource panel. Inline SVG renders crisply at any zoom
// (the board pans/zooms), is consistent across every OS/browser, and is the
// single source of truth for resource iconography (board + panels + buttons).
//
// Every glyph is drawn inside a 24x24 coordinate box so it can be scaled and
// positioned uniformly, whether standalone (<ResourceIcon>) or placed inside
// the board SVG (<BoardResourceIcon>).

import type { ReactElement } from "react";

export type ResourceKey =
  | "LUMBER"
  | "BRICK"
  | "WOOL"
  | "GRAIN"
  | "ORE"
  | "DESERT";

// Glyph paths, drawn in a 0..24 box. Kept intentionally simple + readable.
function glyph(resource: string): ReactElement {
  switch (resource) {
    case "LUMBER":
      return (
        <g>
          <rect x={10.6} y={14} width={2.8} height={7} rx={0.6} fill="#6b4423" />
          <path d="M12 2.5 L17.5 10 H6.5 Z" fill="#3f9142" stroke="#255c28" strokeWidth={0.6} strokeLinejoin="round" />
          <path d="M12 6 L19 15 H5 Z" fill="#2f7d32" stroke="#1e5220" strokeWidth={0.6} strokeLinejoin="round" />
        </g>
      );
    case "BRICK":
      return (
        <g stroke="#7d2f16" strokeWidth={0.9} strokeLinejoin="round">
          <rect x={3} y={7} width={8} height={4} rx={0.6} fill="#c1573a" />
          <rect x={13} y={7} width={8} height={4} rx={0.6} fill="#c1573a" />
          <rect x={3} y={13} width={5.5} height={4} rx={0.6} fill="#b34722" />
          <rect x={10.5} y={13} width={10.5} height={4} rx={0.6} fill="#b34722" />
        </g>
      );
    case "WOOL":
      return (
        <g>
          <path
            d="M8 9 a4 4 0 0 1 4-3 a3.5 3.5 0 0 1 4 2 a3.5 3.5 0 0 1 1 6.5 a3.5 3.5 0 0 1-4 2 a4 4 0 0 1-6 0 a3.5 3.5 0 0 1-1-6.5 A3.5 3.5 0 0 1 8 9 Z"
            fill="#f3efe4"
            stroke="#c9c2ad"
            strokeWidth={0.7}
          />
          <circle cx={8.5} cy={12.5} r={2.6} fill="#3d3a36" />
          <rect x={9} y={17.5} width={1.4} height={3} rx={0.6} fill="#3d3a36" />
          <rect x={13} y={17.5} width={1.4} height={3} rx={0.6} fill="#3d3a36" />
        </g>
      );
    case "GRAIN":
      return (
        <g stroke="#a9791b" strokeWidth={0.7}>
          <line x1={12} y1={21} x2={12} y2={7} strokeWidth={1.2} />
          <g fill="#eab73a">
            <ellipse cx={12} cy={6} rx={1.5} ry={2.6} />
            <ellipse cx={9} cy={9} rx={1.4} ry={2.4} transform="rotate(-32 9 9)" />
            <ellipse cx={15} cy={9} rx={1.4} ry={2.4} transform="rotate(32 15 9)" />
            <ellipse cx={9.2} cy={13} rx={1.4} ry={2.4} transform="rotate(-32 9.2 13)" />
            <ellipse cx={14.8} cy={13} rx={1.4} ry={2.4} transform="rotate(32 14.8 13)" />
          </g>
        </g>
      );
    case "ORE":
      return (
        <g>
          <path
            d="M2.5 20 L8.5 8 L12 14.5 L15.5 7.5 L21.5 20 Z"
            fill="#7b8593"
            stroke="#4a525c"
            strokeWidth={0.8}
            strokeLinejoin="round"
          />
          <path d="M6.7 11.5 L8.5 8 L10.3 11.5 L8.5 12.6 Z" fill="#eef1f5" />
          <path d="M13.9 10.6 L15.5 7.5 L17.2 10.6 L15.5 11.6 Z" fill="#eef1f5" />
        </g>
      );
    case "DESERT":
    default:
      return (
        <g>
          <circle cx={16} cy={8} r={3.2} fill="#f2c14e" />
          <path d="M2 20 q5-6 10-2 q4 3 10-1 v3 H2 Z" fill="#c8a15a" />
          <path d="M2 20 q6-4 11-1 q4 2.5 9-1.5 v4 H2 Z" fill="#d9b26b" />
        </g>
      );
  }
}

/** Standalone icon for panels/buttons. */
export function ResourceIcon({
  resource,
  size = 24,
  className,
  title,
}: {
  resource: string;
  size?: number;
  className?: string;
  title?: string;
}) {
  return (
    <svg
      viewBox="0 0 24 24"
      width={size}
      height={size}
      className={className}
      role={title ? "img" : undefined}
      aria-label={title}
      aria-hidden={title ? undefined : true}
    >
      {title ? <title>{title}</title> : null}
      {glyph(resource)}
    </svg>
  );
}

/** Icon placed inside the board <svg>, centered at (cx, cy). */
export function BoardResourceIcon({
  resource,
  cx,
  cy,
  size = 30,
}: {
  resource: string;
  cx: number;
  cy: number;
  size?: number;
}) {
  const s = size / 24;
  return (
    <g
      transform={`translate(${cx - size / 2}, ${cy - size / 2}) scale(${s})`}
      style={{ pointerEvents: "none" }}
    >
      {glyph(resource)}
    </g>
  );
}
