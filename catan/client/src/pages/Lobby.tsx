import { useState } from "react";
import { motion } from "framer-motion";
import { useGameStore } from "../stores/gameStore";
import { HexBackdrop } from "../components/HexBackdrop";

// Seat colors mirror catan/src/game.py::PLAYER_COLORS (assigned by seat order).
const SEAT_COLORS = ["red", "blue", "green", "orange"];

export function Lobby() {
  const store = useGameStore();
  const lobby = store.lobby;
  const [copied, setCopied] = useState(false);

  if (!lobby) {
    return (
      <div className="h-full flex flex-col items-center justify-center gap-3 text-slate-400">
        <div className="w-8 h-8 rounded-full border-2 border-amber-400 border-t-transparent animate-spin" />
        Connecting…
      </div>
    );
  }
  const isHost = lobby.host === store.username;

  const copyCode = async () => {
    try {
      await navigator.clipboard.writeText(lobby.id);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard may be unavailable; ignore */
    }
  };

  const slots = Array.from({ length: 4 }, (_, i) => lobby.players[i] ?? null);

  return (
    <div className="h-full flex items-center justify-center p-4 relative overflow-hidden">
      <HexBackdrop />
      <motion.div
        initial={{ y: 16, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="relative bg-catan-panel/95 backdrop-blur rounded-2xl shadow-2xl ring-1 ring-white/10 p-8 w-full max-w-md"
      >
        <h1 className="text-3xl font-bold text-center text-amber-300">
          Room {lobby.id}
        </h1>
        <div className="flex items-center justify-center gap-2 mb-6">
          <p className="text-slate-400 text-sm">Share this code</p>
          <button
            onClick={copyCode}
            className="text-xs bg-catan-panel2 hover:bg-slate-700 rounded px-2 py-1 transition-colors"
          >
            {copied ? "Copied!" : "Copy"}
          </button>
        </div>
        <h2 className="text-sm uppercase text-slate-400 mb-2">
          Players ({lobby.players.length}/4)
        </h2>
        <ul className="space-y-2 mb-6">
          {slots.map((p, i) => (
            <li
              key={i}
              className={`flex items-center justify-between rounded-md px-3 py-2 ${
                p ? "bg-catan-panel2" : "bg-catan-panel2/40 border border-dashed border-slate-700"
              }`}
            >
              {p ? (
                <>
                  <span className="flex items-center gap-2">
                    <span
                      className="w-3 h-3 rounded-full ring-1 ring-white/40"
                      style={{ backgroundColor: SEAT_COLORS[i] }}
                    />
                    {p.name}
                    {p.name === lobby.host && (
                      <span className="text-xs text-amber-300">(host)</span>
                    )}
                    {p.is_bot && <span className="text-xs text-slate-400">[bot]</span>}
                  </span>
                  <span
                    className={`text-xs ${p.connected ? "text-emerald-400" : "text-slate-500"}`}
                  >
                    {p.connected ? "online" : "offline"}
                  </span>
                </>
              ) : (
                <span className="text-slate-500 text-sm italic">Empty seat</span>
              )}
            </li>
          ))}
        </ul>
        {isHost ? (
          <div className="flex gap-2">
            <button
              className="btn-secondary flex-1"
              disabled={lobby.players.length >= 4}
              onClick={() => store.addBot()}
            >
              Add Bot
            </button>
            <button
              className="btn-primary flex-1"
              disabled={lobby.players.length < 2}
              onClick={() => store.startGame()}
            >
              Start Game
            </button>
          </div>
        ) : (
          <div className="text-center text-slate-400 italic">
            Waiting for host to start…
          </div>
        )}
      </motion.div>
    </div>
  );
}
