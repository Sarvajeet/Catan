// Decorative, non-interactive tiled-hex background used behind the Landing and
// Lobby cards. Pure SVG pattern, no assets, sits under the content at low
// opacity so it reads as texture rather than noise.
export function HexBackdrop() {
  return (
    <svg
      className="absolute inset-0 w-full h-full pointer-events-none"
      aria-hidden
      preserveAspectRatio="xMidYMid slice"
    >
      <defs>
        <pattern id="hexbg" width="56" height="64" patternUnits="userSpaceOnUse" patternTransform="scale(1.4)">
          <polygon
            points="28,2 54,17 54,47 28,62 2,47 2,17"
            fill="none"
            stroke="#3a5f86"
            strokeWidth="1.5"
            strokeOpacity="0.25"
          />
        </pattern>
        <radialGradient id="hexbg-fade" cx="50%" cy="40%" r="75%">
          <stop offset="0%" stopColor="#000" stopOpacity="0" />
          <stop offset="100%" stopColor="#0a1624" stopOpacity="0.9" />
        </radialGradient>
      </defs>
      <rect width="100%" height="100%" fill="url(#hexbg)" />
      <rect width="100%" height="100%" fill="url(#hexbg-fade)" />
    </svg>
  );
}
