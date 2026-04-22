import { useState } from "react";
import { usePanZoom } from "../hooks/usePanZoom";
import { BoardCanvas } from "../components/BoardCanvas";
import { PlayerPanel } from "../components/PlayerPanel";
import { ActionBar } from "../components/ActionBar";
import { ResourcePanel } from "../components/ResourcePanel";
import { GameLog } from "../components/GameLog";
import { DevCardPanel } from "../components/DevCardPanel";
import { Chat } from "../components/Chat";
import { SettingsBar } from "../components/SettingsBar";
import { DiceAnimation } from "../components/DiceAnimation";
import { DiscardModal } from "../components/DiscardModal";
import { StealModal } from "../components/StealModal";
import { IncomingTrade, TradeModal } from "../components/TradeModal";
import { useGameStore } from "../stores/gameStore";

export function Game() {
  const state = useGameStore((s) => s.game);
  const username = useGameStore((s) => s.username);
  const diceAnimation = useGameStore((s) => s.diceAnimation);
  const [showTrade, setShowTrade] = useState(false);

  const { ref: boardRef, transform, reset: resetZoom } = usePanZoom();

  if (!state) {
    return <div className="h-full flex items-center justify-center">Loading...</div>;
  }
  const me = state.players[username] ?? null;

  const mustDiscard = state.phase === "DISCARD" && state.pending_discards[username];
  const mustPickSteal =
    state.phase === "ROBBER_STEAL" &&
    state.current_player === username &&
    state.pending_steal_targets.length > 0;

  return (
    <div className="h-full flex flex-col md:flex-row overflow-hidden">
      {/* Left sidebar */}
      <aside className="md:w-60 w-full md:h-full max-h-[40vh] md:max-h-full overflow-y-auto scrollable bg-catan-bg p-3 flex flex-col gap-3">
        <RoomHeader />
        <SettingsBar />
        <PlayerPanel state={state} myName={username} />
        <GameLog log={state.log} />
        <Chat />
      </aside>

      {/* Board */}
      <main className="flex-1 relative bg-catan-bg p-2 min-h-0">
        <DiceAnimation roll={diceAnimation} />
        <div
          ref={boardRef}
          className="h-full w-full touch-none overflow-hidden select-none"
          style={{ cursor: "grab" }}
        >
          <div
            className="h-full w-full origin-center"
            style={{
              transform: `translate(${transform.x}px, ${transform.y}px) scale(${transform.scale})`,
              transition: "transform 0.05s linear",
            }}
          >
            <BoardCanvas state={state} />
          </div>
        </div>
        <button
          onClick={resetZoom}
          className="absolute top-3 right-3 btn-ghost text-xs"
          title="Reset zoom"
        >
          Reset view
        </button>
      </main>

      {/* Right sidebar */}
      <aside className="md:w-60 w-full md:h-full max-h-[40vh] md:max-h-full overflow-y-auto scrollable bg-catan-bg p-3 flex flex-col gap-3">
        <ActionBar state={state} me={me} />
        <ResourcePanel me={me} />
        {me && <DevCardPanel me={me} />}
        {me && <IncomingTrade state={state} me={me} />}
        {me && state.phase === "MAIN" && state.current_player === username && (
          <button className="btn-secondary" onClick={() => setShowTrade(true)}>
            Open Trade Menu
          </button>
        )}
      </aside>

      {/* Modals */}
      {mustDiscard && me && (
        <DiscardModal me={me} required={state.pending_discards[username]!} />
      )}
      {mustPickSteal && <StealModal state={state} />}
      {showTrade && me && (
        <TradeModal state={state} me={me} onClose={() => setShowTrade(false)} />
      )}
      <ErrorToast />
    </div>
  );
}

function RoomHeader() {
  const roomId = useGameStore((s) => s.roomId);
  return (
    <div className="bg-catan-panel rounded-md px-3 py-2 flex items-center justify-between">
      <span className="text-sm text-slate-400">Room</span>
      <span className="font-bold text-amber-300 tracking-widest">{roomId}</span>
    </div>
  );
}

function ErrorToast() {
  const message = useGameStore((s) => s.errorToast);
  const clear = useGameStore((s) => s.clearError);
  if (!message) return null;
  return (
    <div
      role="alert"
      className="fixed bottom-4 left-1/2 -translate-x-1/2 bg-red-700 text-white px-4 py-2 rounded-md shadow-lg z-50 cursor-pointer"
      onClick={clear}
    >
      {message}
    </div>
  );
}
