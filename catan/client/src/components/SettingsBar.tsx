import { useState } from "react";
import { isSoundEnabled, setSoundEnabled } from "../sound";

export function SettingsBar() {
  const [sound, setSound] = useState(isSoundEnabled());
  return (
    <div
      className="bg-catan-panel rounded-md px-3 py-2 flex items-center justify-between text-sm"
      role="toolbar"
      aria-label="Settings"
    >
      <label className="flex items-center gap-2 cursor-pointer">
        <input
          type="checkbox"
          checked={sound}
          aria-label="Sound effects"
          onChange={(e) => {
            setSound(e.target.checked);
            setSoundEnabled(e.target.checked);
          }}
        />
        Sound FX
      </label>
      <span className="text-slate-400 text-xs">Pinch / wheel to zoom</span>
    </div>
  );
}
