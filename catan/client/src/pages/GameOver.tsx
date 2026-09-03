import { motion } from "framer-motion";
import { useGameStore } from "../stores/gameStore";

const CONFETTI_COLORS = ["#e6b23a", "#b34722", "#8ac64a", "#6d7784", "#4f9dde", "#e05c8a"];

export function GameOver() {
  const state = useGameStore((s) => s.game);
  if (!state || !state.winner) return null;
  const winner = state.players[state.winner];
  const ranked = state.player_order
    .map((n) => state.players[n])
    .sort((a, b) => b.public_victory_points - a.public_victory_points);

  return (
    <div className="h-full flex items-center justify-center p-4 relative overflow-hidden">
      <Confetti />
      <motion.div
        initial={{ scale: 0.85, opacity: 0, y: 12 }}
        animate={{ scale: 1, opacity: 1, y: 0 }}
        transition={{ type: "spring", stiffness: 220, damping: 20 }}
        className="relative bg-catan-panel rounded-2xl shadow-2xl ring-1 ring-white/10 p-8 w-full max-w-md text-center"
      >
        <motion.div
          initial={{ rotate: -12, scale: 0 }}
          animate={{ rotate: 0, scale: 1 }}
          transition={{ delay: 0.15, type: "spring", stiffness: 260 }}
          className="text-5xl mb-1"
          aria-hidden
        >
          🏆
        </motion.div>
        <h1 className="text-sm uppercase tracking-widest text-slate-400 mb-1">Game Over</h1>
        <h2 className="text-4xl font-bold mb-4" style={{ color: winner.color }}>
          {winner.name} wins!
        </h2>
        <div className="text-lg mb-6 text-slate-200">
          {winner.public_victory_points} Victory Points
        </div>
        <div className="space-y-2 text-left text-sm">
          {ranked.map((p, i) => (
            <motion.div
              key={p.name}
              initial={{ x: -12, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ delay: 0.25 + i * 0.08 }}
              className="flex items-center justify-between bg-catan-panel2 px-3 py-2 rounded-md"
              style={{ borderLeft: `4px solid ${p.color}` }}
            >
              <span className="flex items-center gap-2">
                <span className="text-slate-500 w-4">{i + 1}</span>
                <span
                  className="w-2.5 h-2.5 rounded-full"
                  style={{ backgroundColor: p.color }}
                />
                {p.name}
              </span>
              <span className="font-semibold">{p.public_victory_points} VP</span>
            </motion.div>
          ))}
        </div>
        <button
          className="btn-primary w-full mt-6"
          onClick={() => window.location.reload()}
        >
          New Game
        </button>
      </motion.div>
    </div>
  );
}

function Confetti() {
  const pieces = Array.from({ length: 40 });
  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden">
      {pieces.map((_, i) => {
        const left = Math.random() * 100;
        const color = CONFETTI_COLORS[i % CONFETTI_COLORS.length];
        const delay = Math.random() * 0.6;
        const duration = 2.2 + Math.random() * 1.6;
        const size = 6 + Math.random() * 6;
        return (
          <motion.span
            key={i}
            initial={{ y: -40, x: 0, rotate: 0, opacity: 1 }}
            animate={{ y: "110vh", rotate: 360, opacity: [1, 1, 0.6] }}
            transition={{ delay, duration, repeat: Infinity, ease: "linear" }}
            style={{
              position: "absolute",
              left: `${left}%`,
              width: size,
              height: size * 0.5,
              backgroundColor: color,
              borderRadius: 1,
            }}
          />
        );
      })}
    </div>
  );
}
