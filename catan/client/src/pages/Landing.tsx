import { useState } from "react";
import { motion } from "framer-motion";
import { useGameStore } from "../stores/gameStore";
import { HexBackdrop } from "../components/HexBackdrop";

export function Landing() {
  const store = useGameStore();
  const [username, setUsername] = useState("");
  const [roomId, setRoomId] = useState("");

  return (
    <div className="h-full flex items-center justify-center p-4 relative overflow-hidden">
      <HexBackdrop />
      <motion.div
        initial={{ y: 16, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="relative bg-catan-panel/95 backdrop-blur rounded-2xl shadow-2xl ring-1 ring-white/10 p-8 w-full max-w-md"
      >
        <div className="flex justify-center mb-3">
          <svg width={64} height={64} viewBox="0 0 100 100" aria-hidden>
            <polygon
              points="50,6 91,29 91,71 50,94 9,71 9,29"
              fill="#e6b23a"
              stroke="#b8860b"
              strokeWidth={4}
              strokeLinejoin="round"
            />
            <polygon points="50,20 78,36 78,64 50,80 22,64 22,36" fill="#0f1f2e" opacity={0.25} />
            <text x={50} y={62} textAnchor="middle" fontSize={38} fontWeight={800} fill="#0f1f2e">
              C
            </text>
          </svg>
        </div>
        <h1 className="text-4xl font-bold text-center text-amber-300 mb-1 tracking-tight">Catan</h1>
        <p className="text-center text-slate-400 mb-6">Online Multiplayer</p>
        <label className="block text-sm text-slate-300 mb-1">Username</label>
        <input
          className="w-full bg-catan-panel2 rounded-md px-3 py-2 mb-4"
          placeholder="Your name"
          maxLength={20}
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        <button
          className="btn-primary w-full mb-6"
          disabled={!username.trim()}
          onClick={() => store.createRoom(username.trim())}
        >
          Create New Game
        </button>
        <div className="relative mb-4">
          <div className="border-t border-slate-700" />
          <div className="absolute left-1/2 -translate-x-1/2 -top-2 bg-catan-panel px-2 text-xs text-slate-400">
            or join
          </div>
        </div>
        <label className="block text-sm text-slate-300 mb-1">Room code</label>
        <input
          className="w-full bg-catan-panel2 rounded-md px-3 py-2 mb-3 uppercase"
          placeholder="ABC123"
          maxLength={8}
          value={roomId}
          onChange={(e) => setRoomId(e.target.value.toUpperCase())}
        />
        <button
          className="btn-secondary w-full"
          disabled={!username.trim() || !roomId.trim()}
          onClick={() => store.joinRoom(username.trim(), roomId.trim())}
        >
          Join Game
        </button>
      </motion.div>
    </div>
  );
}
