import { useState } from "react";
import { useGameStore } from "../stores/gameStore";

export function Landing() {
  const store = useGameStore();
  const [username, setUsername] = useState("");
  const [roomId, setRoomId] = useState("");

  return (
    <div className="h-full flex items-center justify-center p-4">
      <div className="bg-catan-panel rounded-xl shadow-2xl p-8 w-full max-w-md">
        <h1 className="text-4xl font-bold text-center text-amber-300 mb-1">Catan</h1>
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
      </div>
    </div>
  );
}
