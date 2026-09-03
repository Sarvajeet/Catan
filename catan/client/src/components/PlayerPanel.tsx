import type { GameStateDTO, PlayerDTO } from "../types";

interface Props {
  state: GameStateDTO;
  myName: string;
}

export function PlayerPanel({ state, myName }: Props) {
  return (
    <div className="space-y-2">
      <h3 className="text-sm uppercase tracking-wider text-slate-400">Players</h3>
      {state.player_order.map((name) => {
        const p = state.players[name];
        if (!p) return null;
        return (
          <PlayerRow
            key={name}
            player={p}
            active={state.current_player === name}
            isMe={name === myName}
            mustDiscard={state.pending_discards[name]}
          />
        );
      })}
    </div>
  );
}

function PlayerRow({
  player,
  active,
  isMe,
  mustDiscard,
}: {
  player: PlayerDTO;
  active: boolean;
  isMe: boolean;
  mustDiscard?: number;
}) {
  return (
    <div
      className={`rounded-md p-2 transition-colors ${
        active ? "bg-catan-panel2 ring-2 ring-amber-400" : "bg-catan-panel"
      }`}
      style={{ borderLeft: `6px solid ${player.color}` }}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="font-semibold">
            {player.name}
            {isMe && <span className="text-slate-400"> (you)</span>}
            {player.is_bot && <span className="text-slate-400"> [bot]</span>}
          </span>
          {!player.connected && (
            <span className="text-xs text-red-400">disconnected</span>
          )}
        </div>
        <div className="text-lg font-bold">{player.public_victory_points} VP</div>
      </div>
      <div className="mt-1 flex gap-3 text-xs text-slate-300">
        <span title="Cards in hand">Cards: {player.resource_count}</span>
        <span title="Development cards">Dev: {player.dev_card_count}</span>
        <span title="Knights played">
          Knights: {player.knights}
          {player.has_largest_army && " *"}
        </span>
        <span title="Longest road">{player.has_longest_road && "LR *"}</span>
      </div>
      {mustDiscard !== undefined && (
        <div className="mt-1 text-xs text-amber-300">Must discard {mustDiscard}</div>
      )}
    </div>
  );
}
