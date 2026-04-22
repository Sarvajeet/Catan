import { motion, AnimatePresence } from "framer-motion";

export function DiceAnimation({ roll }: { roll: number | null }) {
  return (
    <AnimatePresence>
      {roll !== null && (
        <motion.div
          initial={{ opacity: 0, y: -30, scale: 0.5 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 20 }}
          className="absolute top-6 left-1/2 -translate-x-1/2 z-20 bg-catan-panel2 px-5 py-3 rounded-lg shadow-lg text-center pointer-events-none"
        >
          <div className="text-xs uppercase text-slate-400">Rolled</div>
          <div className="text-4xl font-bold">{roll}</div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
