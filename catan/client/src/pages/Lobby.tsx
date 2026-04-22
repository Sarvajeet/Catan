import { useGameStore } from "../stores/gameStore";

export function Lobby() {
  const store = useGameStore();
  const lobby = store.lobby;
  if (!lobby) {
    return (
      <div className="h-full flex items-center justify-center text-slate-400">
        Connecting...
      </div>
    );
  }
  const isHost = lobby.host === store.username;

  return (
    <div className="h-full flex items-center justify-center p-4">
      <div className="bg-catan-panel rounded-xl shadow-2xl p-8 w-full max-w-md">
        <h1 className="text-3xl font-bold text-center text-amber-300">
          Room {lobby.id}
        </h1>
        <p className="text-center text-slate-400 mb-6">
          Share this code with friends
        </p>
        <h2 className="text-sm uppercase text-slate-400 mb-2">
          Players ({lobby.players.length}/4)
        </h2>
        <ul className="space-y-1 mb-6">
          {lobby.players.map((p) => (
            <li
              key={p.name}
              className="flex items-center justify-between bg-catan-panel2 rounded-md px-3 py-2"
            >
              <span>
                {p.name}
                {p.name === lobby.host && (
                  <span className="text-xs text-amber-300 ml-2">(host)</span>
                )}
                {p.is_bot && (
                  <span className="text-xs text-slate-400 ml-2">[bot]</span>
                )}
              </span>
              <span
                className={`text-xs ${p.connected ? "text-emerald-400" : "text-slate-500"}`}
              >
                {p.connected ? "online" : "offline"}
              </span>
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
            Waiting for host to start...
          </div>
        )}
      </div>
    </div>
  );
}
