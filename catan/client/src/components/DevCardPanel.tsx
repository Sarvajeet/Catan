import { useState } from "react";
import { useGameStore } from "../stores/gameStore";
import { RESOURCES, type PlayerDTO, type ResourceName } from "../types";

export function DevCardPanel({ me }: { me: PlayerDTO }) {
  const store = useGameStore();
  const [prompt, setPrompt] = useState<null | "monopoly" | "year_of_plenty">(null);
  const [monoRes, setMonoRes] = useState<ResourceName>("WOOL");
  const [yop1, setYop1] = useState<ResourceName>("LUMBER");
  const [yop2, setYop2] = useState<ResourceName>("BRICK");

  const cards = me.development_cards ?? [];
  const newCards = me.new_development_cards ?? [];

  const playCard = (kind: string) => {
    if (kind === "monopoly") {
      setPrompt("monopoly");
      return;
    }
    if (kind === "year_of_plenty") {
      setPrompt("year_of_plenty");
      return;
    }
    if (kind === "road_building") {
      store.setBuildMode({ type: "road_building_1" });
      return;
    }
    store.playDevCard(kind);
  };

  return (
    <div className="bg-catan-panel rounded-md p-3">
      <h3 className="text-sm uppercase tracking-wider text-slate-400 mb-2">
        Development Cards
      </h3>
      {cards.length === 0 && newCards.length === 0 && (
        <div className="text-xs text-slate-400">No dev cards.</div>
      )}
      <div className="grid grid-cols-1 gap-1">
        {cards.map((c, i) => (
          <button
            key={`c-${i}`}
            className="btn-action text-left text-xs"
            onClick={() => playCard(c.kind)}
            title={`Play ${c.name}`}
          >
            {c.name}
          </button>
        ))}
        {newCards.map((c, i) => (
          <div
            key={`n-${i}`}
            className="text-xs text-slate-400 px-2 py-1 italic border border-slate-600 rounded"
            title="Bought this turn; playable next turn"
          >
            {c.name} (new)
          </div>
        ))}
      </div>

      {prompt === "monopoly" && (
        <Prompt onClose={() => setPrompt(null)} title="Monopoly: pick a resource">
          <select
            className="w-full bg-catan-panel2 rounded-md px-2 py-1 mb-2"
            value={monoRes}
            onChange={(e) => setMonoRes(e.target.value as ResourceName)}
          >
            {RESOURCES.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
          <button
            className="btn-primary w-full"
            onClick={() => {
              store.playDevCard("monopoly", { resource: monoRes });
              setPrompt(null);
            }}
          >
            Play Monopoly
          </button>
        </Prompt>
      )}

      {prompt === "year_of_plenty" && (
        <Prompt onClose={() => setPrompt(null)} title="Year of Plenty: pick two resources">
          <div className="space-y-2 mb-3">
            <select
              className="w-full bg-catan-panel2 rounded-md px-2 py-1"
              value={yop1}
              onChange={(e) => setYop1(e.target.value as ResourceName)}
            >
              {RESOURCES.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
            <select
              className="w-full bg-catan-panel2 rounded-md px-2 py-1"
              value={yop2}
              onChange={(e) => setYop2(e.target.value as ResourceName)}
            >
              {RESOURCES.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>
          <button
            className="btn-primary w-full"
            onClick={() => {
              store.playDevCard("year_of_plenty", { resource1: yop1, resource2: yop2 });
              setPrompt(null);
            }}
          >
            Play Year of Plenty
          </button>
        </Prompt>
      )}
    </div>
  );
}

function Prompt({
  title,
  children,
  onClose,
}: {
  title: string;
  children: React.ReactNode;
  onClose(): void;
}) {
  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-catan-panel2 p-5 rounded-lg w-80 max-w-full">
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-bold">{title}</h3>
          <button className="btn-ghost" onClick={onClose}>
            ✕
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
