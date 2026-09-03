import { useState } from "react";
import { useGameStore } from "../stores/gameStore";

export function Chat() {
  const chat = useGameStore((s) => s.chat);
  const send = useGameStore((s) => s.sendChat);
  const [text, setText] = useState("");

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = text.trim();
    if (!trimmed) return;
    send(trimmed);
    setText("");
  };

  return (
    <div className="bg-catan-panel rounded-md p-2 flex flex-col min-h-0">
      <h3 className="text-sm uppercase tracking-wider text-slate-400 mb-1">
        Chat
      </h3>
      <div className="scrollable overflow-y-auto flex-1 max-h-32 text-sm space-y-1 mb-2">
        {chat.slice(-50).map((m, i) => (
          <div key={i}>
            <span className="text-amber-300 font-semibold">{m.from}:</span>{" "}
            <span className="text-slate-200">{m.message}</span>
          </div>
        ))}
      </div>
      <form onSubmit={submit} className="flex gap-1">
        <input
          className="flex-1 bg-catan-panel2 rounded-md px-2 py-1 text-sm"
          placeholder="Say something..."
          value={text}
          maxLength={300}
          onChange={(e) => setText(e.target.value)}
        />
        <button type="submit" className="btn-primary px-3 py-1 text-sm">
          Send
        </button>
      </form>
    </div>
  );
}
