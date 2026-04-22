import { useState } from "react";
import { useGameStore } from "../stores/gameStore";
import { RESOURCES, type PlayerDTO, type ResourceName } from "../types";

export function DiscardModal({
  me,
  required,
}: {
  me: PlayerDTO;
  required: number;
}) {
  const store = useGameStore();
  const [counts, setCounts] = useState<Record<ResourceName, number>>(() => ({
    LUMBER: 0,
    BRICK: 0,
    WOOL: 0,
    GRAIN: 0,
    ORE: 0,
  }));
  const total = Object.values(counts).reduce((a, b) => a + b, 0);

  const bump = (r: ResourceName, delta: number) => {
    setCounts((c) => {
      const next = Math.max(0, Math.min(me.resources![r], c[r] + delta));
      return { ...c, [r]: next };
    });
  };

  return (
    <Overlay>
      <div className="bg-catan-panel2 p-5 rounded-lg w-96 max-w-full">
        <h2 className="text-xl font-bold mb-2">Discard {required} cards</h2>
        <p className="text-slate-300 text-sm mb-3">
          A 7 was rolled. Choose which cards to discard.
        </p>
        <div className="space-y-2">
          {RESOURCES.map((r) => (
            <div key={r} className="flex items-center justify-between">
              <span className="w-20 text-sm">{r}</span>
              <span className="text-xs text-slate-400">have {me.resources![r]}</span>
              <div className="flex items-center gap-2">
                <button className="btn-ghost px-2" onClick={() => bump(r, -1)}>
                  −
                </button>
                <span className="w-6 text-center font-bold">{counts[r]}</span>
                <button className="btn-ghost px-2" onClick={() => bump(r, 1)}>
                  +
                </button>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-3 flex items-center justify-between">
          <span className={total === required ? "text-emerald-400" : "text-amber-300"}>
            Selected: {total} / {required}
          </span>
          <button
            className="btn-primary"
            disabled={total !== required}
            onClick={() => store.discard(counts)}
          >
            Discard
          </button>
        </div>
      </div>
    </Overlay>
  );
}

function Overlay({ children }: { children: React.ReactNode }) {
  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      {children}
    </div>
  );
}
