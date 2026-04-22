import { useEffect } from "react";
import { useGameStore } from "./stores/gameStore";
import { Landing } from "./pages/Landing";
import { Lobby } from "./pages/Lobby";
import { Game } from "./pages/Game";
import { GameOver } from "./pages/GameOver";

export function App() {
  const screen = useGameStore((s) => s.screen);
  const init = useGameStore((s) => s.init);

  useEffect(() => {
    init();
  }, [init]);

  switch (screen) {
    case "landing":
      return <Landing />;
    case "lobby":
      return <Lobby />;
    case "game":
      return <Game />;
    case "gameover":
      return <GameOver />;
    default:
      return null;
  }
}
