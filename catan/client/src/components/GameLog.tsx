export function GameLog({ log }: { log: string[] }) {
  const recent = log.slice(-50).reverse();
  return (
    <div className="bg-catan-panel rounded-md p-3">
      <h3 className="text-sm uppercase tracking-wider text-slate-400 mb-2">
        Game Log
      </h3>
      <div className="scrollable max-h-48 overflow-y-auto text-sm space-y-1">
        {recent.map((entry, i) => (
          <div key={i} className="text-slate-300">
            {entry}
          </div>
        ))}
      </div>
    </div>
  );
}
