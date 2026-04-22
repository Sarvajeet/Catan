import { useMemo, useState } from "react";
import { useGameStore } from "../stores/gameStore";
import { RESOURCES, type GameStateDTO, type PlayerDTO, type ResourceName } from "../types";

interface Props {
  state: GameStateDTO;
  me: PlayerDTO;
  onClose(): void;
}

type Counts = Record<ResourceName, number>;

const EMPTY: Counts = { LUMBER: 0, BRICK: 0, WOOL: 0, GRAIN: 0, ORE: 0 };

export function TradeModal({ state, me, onClose }: Props) {
  const store = useGameStore();
  const [offer, setOffer] = useState<Counts>({ ...EMPTY });
  const [want, setWant] = useState<Counts>({ ...EMPTY });
  const [tab, setTab] = useState<"player" | "bank">("player");

  const otherPlayers = state.player_order.filter((n) => n !== me.name);

  // Compute best maritime ratio per resource for the Bank tab
  const ratios = useMemo(() => {
    const r: Record<ResourceName, number> = {
      LUMBER: 4, BRICK: 4, WOOL: 4, GRAIN: 4, ORE: 4,
    };
    for (const h of me.harbors) {
      if (h.resource === null) {
        for (const k of RESOURCES) r[k] = Math.min(r[k], 3);
      } else {
        r[h.resource] = Math.min(r[h.resource], 2);
      }
    }
    return r;
  }, [me.harbors]);

  const bumpOffer = (r: ResourceName, d: number) => {
    setOffer((c) => ({ ...c, [r]: Math.max(0, Math.min(me.resources![r], c[r] + d)) }));
  };
  const bumpWant = (r: ResourceName, d: number) => {
    setWant((c) => ({ ...c, [r]: Math.max(0, c[r] + d) }));
  };

  const offerTotal = Object.values(offer).reduce((a, b) => a + b, 0);
  const wantTotal = Object.values(want).reduce((a, b) => a + b, 0);

  const submitPlayerOffer = () => {
    if (offerTotal === 0 || wantTotal === 0) return;
    const filteredOffer: Partial<Record<ResourceName, number>> = {};
    const filteredWant: Partial<Record<ResourceName, number>> = {};
    for (const r of RESOURCES) {
      if (offer[r]) filteredOffer[r] = offer[r];
      if (want[r]) filteredWant[r] = want[r];
    }
    store.offerTrade(otherPlayers, filteredOffer, filteredWant);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-40 p-4">
      <div className="bg-catan-panel2 p-5 rounded-lg w-full max-w-lg">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xl font-bold">Trade</h2>
          <button className="btn-ghost" onClick={onClose}>
            ✕
          </button>
        </div>
        <div className="flex gap-2 mb-3">
          <button
            className={tab === "player" ? "btn-primary" : "btn-ghost"}
            onClick={() => setTab("player")}
          >
            With Players
          </button>
          <button
            className={tab === "bank" ? "btn-primary" : "btn-ghost"}
            onClick={() => setTab("bank")}
          >
            With Bank/Port
          </button>
        </div>

        {tab === "player" ? (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <h3 className="text-sm uppercase text-slate-400 mb-2">You offer</h3>
              <Picker counts={offer} bump={bumpOffer} max={me.resources!} />
            </div>
            <div>
              <h3 className="text-sm uppercase text-slate-400 mb-2">You want</h3>
              <Picker counts={want} bump={bumpWant} />
            </div>
          </div>
        ) : (
          <BankTab me={me} ratios={ratios} />
        )}

        {tab === "player" && (
          <div className="mt-4 flex justify-end gap-2">
            <button className="btn-ghost" onClick={onClose}>
              Cancel
            </button>
            <button
              className="btn-primary"
              disabled={offerTotal === 0 || wantTotal === 0}
              onClick={submitPlayerOffer}
            >
              Send Offer
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

function Picker({
  counts,
  bump,
  max,
}: {
  counts: Counts;
  bump(r: ResourceName, d: number): void;
  max?: Record<ResourceName, number>;
}) {
  return (
    <div className="space-y-1">
      {RESOURCES.map((r) => (
        <div key={r} className="flex items-center justify-between text-sm">
          <span>{r}</span>
          <div className="flex items-center gap-1">
            <button className="btn-ghost px-2" onClick={() => bump(r, -1)}>
              −
            </button>
            <span className="w-6 text-center">{counts[r]}</span>
            <button
              className="btn-ghost px-2"
              onClick={() => bump(r, 1)}
              disabled={max ? counts[r] >= max[r] : false}
            >
              +
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

function BankTab({
  me,
  ratios,
}: {
  me: PlayerDTO;
  ratios: Record<ResourceName, number>;
}) {
  const store = useGameStore();
  const [give, setGive] = useState<ResourceName>("LUMBER");
  const [get, setGet] = useState<ResourceName>("ORE");
  const need = ratios[give];
  const canTrade = (me.resources![give] ?? 0) >= need && give !== get;
  return (
    <div className="space-y-3">
      <p className="text-sm text-slate-300">
        Best ratio per resource is shown next to each option. Harbors give you a
        discount.
      </p>
      <div className="flex items-center gap-2">
        <label>Give</label>
        <select
          className="bg-catan-panel text-slate-100 rounded-md px-2 py-1"
          value={give}
          onChange={(e) => setGive(e.target.value as ResourceName)}
        >
          {RESOURCES.map((r) => (
            <option key={r} value={r}>
              {r} ({ratios[r]}:1, have {me.resources![r]})
            </option>
          ))}
        </select>
      </div>
      <div className="flex items-center gap-2">
        <label>Receive</label>
        <select
          className="bg-catan-panel text-slate-100 rounded-md px-2 py-1"
          value={get}
          onChange={(e) => setGet(e.target.value as ResourceName)}
        >
          {RESOURCES.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>
      </div>
      <button
        className="btn-primary"
        disabled={!canTrade}
        onClick={() => store.maritimeTrade(give, get)}
      >
        Trade {need} {give} for 1 {get}
      </button>
    </div>
  );
}

export function IncomingTrade({
  state,
  me,
}: {
  state: GameStateDTO;
  me: PlayerDTO;
}) {
  const store = useGameStore();
  const incoming = state.pending_trades.filter((t) => t.to.includes(me.name));
  const outgoing = state.pending_trades.filter((t) => t.from === me.name);
  if (incoming.length === 0 && outgoing.length === 0) return null;
  return (
    <div className="bg-catan-panel rounded-md p-3 space-y-2">
      {incoming.map((t) => (
        <div key={t.id} className="text-sm">
          <div className="font-semibold mb-1">Trade from {t.from}</div>
          <div className="text-slate-300">
            Offers: {formatCounts(t.offer)} · Wants: {formatCounts(t.request)}
          </div>
          <div className="mt-1 flex gap-2">
            <button className="btn-primary px-2 py-1 text-xs" onClick={() => store.acceptTrade(t.id)}>
              Accept
            </button>
            <button className="btn-ghost px-2 py-1 text-xs" onClick={() => store.rejectTrade(t.id)}>
              Reject
            </button>
          </div>
        </div>
      ))}
      {outgoing.map((t) => (
        <div key={t.id} className="text-sm">
          <div className="font-semibold">Your offer to {t.to.join(", ")}</div>
          <div className="text-slate-400 text-xs">
            Offer {formatCounts(t.offer)} ↔ {formatCounts(t.request)}
          </div>
          <button className="btn-ghost px-2 py-1 text-xs mt-1" onClick={() => store.cancelTrade(t.id)}>
            Cancel
          </button>
        </div>
      ))}
    </div>
  );
}

function formatCounts(c: Partial<Record<ResourceName, number>>): string {
  const parts: string[] = [];
  for (const r of RESOURCES) if (c[r]) parts.push(`${c[r]} ${r}`);
  return parts.join(", ") || "—";
}
