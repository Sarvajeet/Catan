import { useGameStore } from "../stores/gameStore";
import type { GameStateDTO, PlayerDTO } from "../types";
import { RESOURCES } from "../types";
import { ResourceIcon } from "./icons/ResourceIcons";

interface Props {
  state: GameStateDTO;
  me: PlayerDTO | null;
}

export const PHASE_LABELS: Record<string, string> = {
  SETUP_1: "Setup — round 1",
  SETUP_2: "Setup — round 2",
  ROLL: "Roll the dice",
  MAIN: "Build & trade",
  DISCARD: "Discard cards",
  MOVE_ROBBER: "Move the robber",
  ROBBER_STEAL: "Steal a card",
  GAME_OVER: "Game over",
};

/** A small resource-cost badge: icon + count, repeated per resource. */
function Cost({ needs }: { needs: Array<[string, number]> }) {
  return (
    <span className="inline-flex items-center gap-1 ml-1">
      {needs.map(([r, n]) => (
        <span key={r} className="inline-flex items-center gap-0.5">
          {Array.from({ length: n }).map((_, i) => (
            <ResourceIcon key={i} resource={r} size={14} />
          ))}
        </span>
      ))}
    </span>
  );
}

export function ActionBar({ state, me }: Props) {
  const store = useGameStore();
  const isMyTurn = state.current_player === store.username;
  const phase = state.phase;

  const canAfford = (needs: Partial<Record<string, number>>): boolean => {
    if (!me?.resources) return false;
    for (const [r, n] of Object.entries(needs)) {
      if ((me.resources[r as (typeof RESOURCES)[number]] ?? 0) < (n ?? 0)) return false;
    }
    return true;
  };

  return (
    <div className="flex flex-col gap-2 bg-catan-panel rounded-md p-3">
      <div className="text-xs uppercase text-slate-400">
        <span className="text-amber-300">{PHASE_LABELS[phase] ?? phase}</span>
        {" · "}Turn {state.turn}
      </div>

      {(phase === "SETUP_1" || phase === "SETUP_2") && isMyTurn && (
        <SetupHint state={state} />
      )}

      {phase === "ROLL" && isMyTurn && (
        <button className="btn-primary" onClick={() => store.roll()}>
          Roll Dice
        </button>
      )}

      {phase === "DISCARD" && store.game?.pending_discards[store.username] && (
        <div className="text-amber-300 text-sm">Open the discard dialog.</div>
      )}

      {phase === "MOVE_ROBBER" && isMyTurn && (
        <button
          className="btn-primary"
          onClick={() => store.setBuildMode({ type: "move_robber" })}
        >
          Click a hex to place the robber
        </button>
      )}

      {phase === "MAIN" && isMyTurn && (
        <>
          <button
            className="btn-action flex items-center justify-between"
            disabled={!canAfford({ BRICK: 1, LUMBER: 1 })}
            onClick={() => store.setBuildMode({ type: "road" })}
          >
            <span>Build Road</span>
            <Cost needs={[["BRICK", 1], ["LUMBER", 1]]} />
          </button>
          <button
            className="btn-action flex items-center justify-between"
            disabled={!canAfford({ BRICK: 1, LUMBER: 1, WOOL: 1, GRAIN: 1 })}
            onClick={() => store.setBuildMode({ type: "settlement" })}
          >
            <span>Build Settlement</span>
            <Cost needs={[["BRICK", 1], ["LUMBER", 1], ["WOOL", 1], ["GRAIN", 1]]} />
          </button>
          <button
            className="btn-action flex items-center justify-between"
            disabled={!canAfford({ GRAIN: 2, ORE: 3 })}
            onClick={() => store.setBuildMode({ type: "city" })}
          >
            <span>Build City</span>
            <Cost needs={[["GRAIN", 2], ["ORE", 3]]} />
          </button>
          <button
            className="btn-action flex items-center justify-between"
            disabled={!canAfford({ ORE: 1, WOOL: 1, GRAIN: 1 }) || state.dev_card_deck_count === 0}
            onClick={() => store.buyDevCard()}
          >
            <span>Buy Dev Card</span>
            <Cost needs={[["ORE", 1], ["WOOL", 1], ["GRAIN", 1]]} />
          </button>
          <button className="btn-secondary" onClick={() => store.endTurn()}>
            End Turn
          </button>
        </>
      )}

      {store.buildMode.type !== "none" && (
        <button
          className="btn-ghost text-xs"
          onClick={() => store.setBuildMode({ type: "none" })}
        >
          Cancel {store.buildMode.type}
        </button>
      )}

      {!isMyTurn && phase !== "DISCARD" && (
        <div className="text-slate-400 text-sm italic">
          Waiting for {state.current_player}...
        </div>
      )}
    </div>
  );
}

function SetupHint({ state }: { state: GameStateDTO }) {
  const store = useGameStore();
  if (state.setup?.expects_road_for != null) {
    if (store.buildMode.type !== "setup_road") {
      store.setBuildMode({ type: "setup_road" });
    }
    return (
      <div className="text-amber-300 text-sm">
        Click an edge next to your new settlement to place your road.
      </div>
    );
  }
  if (store.buildMode.type !== "setup_settlement") {
    store.setBuildMode({ type: "setup_settlement" });
  }
  return (
    <div className="text-amber-300 text-sm">
      Click a vertex to place your {state.phase === "SETUP_1" ? "first" : "second"} settlement.
    </div>
  );
}
