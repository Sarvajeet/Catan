import { RESOURCE_FILL } from "../board/geometry";
import type { PlayerDTO } from "../types";
import { RESOURCES } from "../types";

const ICONS: Record<string, string> = {
  LUMBER: "🪵",
  BRICK: "🧱",
  WOOL: "🐑",
  GRAIN: "🌾",
  ORE: "⛰",
};

export function ResourcePanel({ me }: { me: PlayerDTO | null }) {
  if (!me || !me.resources) return null;
  return (
    <div className="bg-catan-panel rounded-md p-3">
      <h3 className="text-sm uppercase tracking-wider text-slate-400 mb-2">
        Your Hand
      </h3>
      <div className="grid grid-cols-5 gap-2">
        {RESOURCES.map((r) => (
          <div
            key={r}
            className="flex flex-col items-center rounded-md py-1"
            style={{ backgroundColor: RESOURCE_FILL[r] + "33" }}
          >
            <span className="text-lg">{ICONS[r]}</span>
            <span className="font-bold">{me.resources![r]}</span>
            <span className="text-[10px] uppercase text-slate-400">{r}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
