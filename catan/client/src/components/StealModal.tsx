import { useGameStore } from "../stores/gameStore";
import type { GameStateDTO } from "../types";

export function StealModal({ state }: { state: GameStateDTO }) {
  const store = useGameStore();
  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-catan-panel2 p-5 rounded-lg w-80 max-w-full">
        <h2 className="text-xl font-bold mb-2">Pick a victim</h2>
        <p className="text-slate-300 text-sm mb-3">
          Steal one random resource from a player adjacent to the robber.
        </p>
        <div className="space-y-2">
          {state.pending_steal_targets.map((name) => {
            const p = state.players[name];
            return (
              <button
                key={name}
                className="w-full btn-action flex items-center justify-between"
                style={{ borderLeft: `6px solid ${p.color}` }}
                onClick={() => store.stealFrom(name)}
              >
                <span>{name}</span>
                <span className="text-xs text-slate-300">
                  {p.resource_count} cards
                </span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
