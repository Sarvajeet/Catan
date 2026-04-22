import { useGameStore } from "../stores/gameStore";

export function GameOver() {
  const state = useGameStore((s) => s.game);
  if (!state || !state.winner) return null;
  const winner = state.players[state.winner];
  return (
    <div className="h-full flex items-center justify-center p-4">
      <div className="bg-catan-panel rounded-xl shadow-2xl p-8 w-full max-w-md text-center">
        <h1 className="text-2xl text-slate-300 mb-1">Game Over</h1>
        <h2
          className="text-4xl font-bold mb-4"
          style={{ color: winner.color }}
        >
          {winner.name} wins!
        </h2>
        <div className="text-lg mb-6">
          {winner.public_victory_points} Victory Points
        </div>
        <div className="space-y-2 text-left text-sm">
          {state.player_order
            .map((n) => state.players[n])
            .sort((a, b) => b.public_victory_points - a.public_victory_points)
            .map((p) => (
              <div
                key={p.name}
                className="flex items-center justify-between bg-catan-panel2 px-3 py-2 rounded-md"
                style={{ borderLeft: `4px solid ${p.color}` }}
              >
                <span>{p.name}</span>
                <span>{p.public_victory_points} VP</span>
              </div>
            ))}
        </div>
        <button
          className="btn-primary w-full mt-6"
          onClick={() => window.location.reload()}
        >
          New Game
        </button>
      </div>
    </div>
  );
}
