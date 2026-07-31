import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
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
import { PHASE_LABELS } from "../components/ActionBar";
import { useGameStore } from "../stores/gameStore";
import type { GameStateDTO } from "../types";

export function Game() {
  const state = useGameStore((s) => s.game);
  const username = useGameStore((s) => s.username);
  const diceAnimation = useGameStore((s) => s.diceAnimation);
  const setBuildMode = useGameStore((s) => s.setBuildMode);
  const [showTrade, setShowTrade] = useState(false);

  const { ref: boardRef, transform, reset: resetZoom } = usePanZoom();

  // Esc cancels an in-progress build mode (but never the forced setup modes,
  // which the setup flow immediately re-arms).
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== "Escape") return;
      const t = useGameStore.getState().buildMode.type;
      if (t !== "none" && t !== "setup_settlement" && t !== "setup_road") {
        setBuildMode({ type: "none" });
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [setBuildMode]);

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
      {/* Left sidebar — static column on desktop, bottom-sheet drawer on mobile */}
      <MobileDrawer id="info" title="Game Info" side="left">
        <RoomHeader />
        <SettingsBar />
        <PlayerPanel state={state} myName={username} />
        <GameLog log={state.log} />
        <Chat />
      </MobileDrawer>

      {/* Board */}
      <main className="flex-1 relative bg-catan-bg p-2 min-h-0">
        <TurnBanner state={state} username={username} />
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
          className="absolute top-3 right-3 btn-ghost text-xs bg-catan-panel/70 backdrop-blur"
          title="Reset zoom"
        >
          Reset view
        </button>
        <BuildModeChip />
      </main>

      {/* Right sidebar — static column on desktop, bottom-sheet drawer on mobile */}
      <MobileDrawer id="actions" title="Your Turn" side="right">
        <ActionBar state={state} me={me} />
        <ResourcePanel me={me} />
        {me && <DevCardPanel me={me} />}
        {me && <IncomingTrade state={state} me={me} />}
        {me && state.phase === "MAIN" && state.current_player === username && (
          <button className="btn-secondary" onClick={() => setShowTrade(true)}>
            Open Trade Menu
          </button>
        )}
      </MobileDrawer>

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

/**
 * On desktop (md+) this renders a static sidebar column, unchanged from before.
 * On mobile it collapses to a floating tab button that opens the panel as a
 * slide-up bottom sheet, so the board keeps full height instead of being
 * squeezed between two tall sidebars.
 */
function MobileDrawer({
  id,
  title,
  side,
  children,
}: {
  id: "info" | "actions";
  title: string;
  side: "left" | "right";
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(false);
  return (
    <>
      {/* Desktop: static column */}
      <aside className="hidden md:flex md:w-60 md:h-full overflow-y-auto scrollable bg-catan-bg p-3 flex-col gap-3">
        {children}
      </aside>

      {/* Mobile: floating tab button */}
      <button
        onClick={() => setOpen(true)}
        aria-label={`Open ${title}`}
        className={`md:hidden fixed bottom-3 z-30 bg-catan-panel text-slate-100 text-sm font-semibold px-4 py-2 rounded-full shadow-lg ring-1 ring-white/10 ${
          side === "left" ? "left-3" : "right-3"
        }`}
      >
        {title}
      </button>

      {/* Mobile: bottom-sheet drawer */}
      <AnimatePresence>
        {open && (
          <motion.div
            className="md:hidden fixed inset-0 z-40 flex items-end"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <div className="absolute inset-0 bg-black/50" onClick={() => setOpen(false)} />
            <motion.div
              key={id}
              initial={{ y: "100%" }}
              animate={{ y: 0 }}
              exit={{ y: "100%" }}
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
              className="relative w-full max-h-[75vh] overflow-y-auto scrollable bg-catan-bg rounded-t-2xl p-3 pt-2 flex flex-col gap-3"
            >
              <div className="sticky top-0 -mx-3 px-3 pb-2 pt-1 bg-catan-bg flex items-center justify-between">
                <span className="text-sm uppercase tracking-wider text-slate-400">{title}</span>
                <button className="btn-ghost text-sm" onClick={() => setOpen(false)}>
                  Close
                </button>
              </div>
              {children}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
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

function TurnBanner({
  state,
  username,
}: {
  state: GameStateDTO;
  username: string;
}) {
  if (state.phase === "GAME_OVER") return null;
  const isMe = state.current_player === username;
  const color = state.players[state.current_player]?.color ?? "#ffd166";
  const phaseLabel = PHASE_LABELS[state.phase] ?? state.phase;
  return (
    <motion.div
      key={`${state.current_player}-${state.phase}`}
      initial={{ y: 16, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      className="absolute bottom-3 left-1/2 -translate-x-1/2 z-20 flex items-center gap-2 rounded-full bg-catan-panel/80 backdrop-blur px-4 py-1.5 shadow-lg ring-1 ring-white/10"
    >
      <span
        className="w-3 h-3 rounded-full ring-2 ring-white/60"
        style={{ backgroundColor: color }}
      />
      <span className="text-sm font-semibold text-slate-100">
        {isMe ? "Your turn" : `${state.current_player}'s turn`}
      </span>
      <span className="text-xs text-slate-400">· {phaseLabel}</span>
    </motion.div>
  );
}

const BUILD_CHIP_LABELS: Record<string, string> = {
  road: "Placing a road — click an edge",
  settlement: "Placing a settlement — click a corner",
  city: "Upgrading to a city — click your settlement",
  move_robber: "Move the robber — click a hex",
  road_building_1: "Road Building — place road 1 of 2",
  road_building_2: "Road Building — place road 2 of 2",
};

function BuildModeChip() {
  const buildMode = useGameStore((s) => s.buildMode);
  const label = BUILD_CHIP_LABELS[buildMode.type];
  return (
    <AnimatePresence>
      {label && (
        <motion.div
          initial={{ y: 16, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: 16, opacity: 0 }}
          className="absolute bottom-16 left-1/2 -translate-x-1/2 z-20 rounded-full bg-amber-500 text-slate-900 text-sm font-semibold px-4 py-1.5 shadow-lg"
        >
          {label} · <span className="opacity-70">Esc to cancel</span>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

function ErrorToast() {
  const message = useGameStore((s) => s.errorToast);
  const clear = useGameStore((s) => s.clearError);
  return (
    <AnimatePresence>
      {message && (
        <motion.div
          role="alert"
          initial={{ y: 24, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: 24, opacity: 0 }}
          className="fixed bottom-4 left-1/2 -translate-x-1/2 bg-red-700 text-white px-4 py-2 rounded-md shadow-lg z-50 cursor-pointer"
          onClick={clear}
        >
          {message}
        </motion.div>
      )}
    </AnimatePresence>
  );
}
