import { create } from "zustand";
import { getSocket } from "../socket";
import { play as playSound } from "../sound";
import type { GameStateDTO, LobbyDTO, ResourceName } from "../types";

type Screen = "landing" | "lobby" | "game" | "gameover";

type BuildMode =
  | { type: "none" }
  | { type: "setup_settlement" }
  | { type: "setup_road" }
  | { type: "road" }
  | { type: "settlement" }
  | { type: "city" }
  | { type: "move_robber" }
  | { type: "road_building_1" }
  | { type: "road_building_2"; first: [number, number] };

interface ChatMessage {
  from: string;
  message: string;
}

interface GameStore {
  screen: Screen;
  username: string;
  roomId: string;
  lobby: LobbyDTO | null;
  game: GameStateDTO | null;
  chat: ChatMessage[];
  errorToast: string | null;
  diceAnimation: number | null;
  buildMode: BuildMode;

  // actions
  init(): void;
  createRoom(username: string): void;
  joinRoom(username: string, roomId: string): void;
  addBot(): void;
  startGame(): void;
  sendChat(message: string): void;

  setBuildMode(mode: BuildMode): void;
  clearError(): void;

  // game actions
  roll(): void;
  endTurn(): void;
  buildRoad(edge: [number, number]): void;
  buildSettlement(vertex: number): void;
  buildCity(vertex: number): void;
  buyDevCard(): void;
  playDevCard(kind: string, payload?: Record<string, unknown>): void;
  offerTrade(
    to: string[],
    offer: Partial<Record<ResourceName, number>>,
    request: Partial<Record<ResourceName, number>>,
  ): void;
  acceptTrade(tradeId: number): void;
  rejectTrade(tradeId: number): void;
  cancelTrade(tradeId: number): void;
  maritimeTrade(give: ResourceName, get: ResourceName): void;
  moveRobber(hex: number): void;
  stealFrom(target: string): void;
  discard(resources: Partial<Record<ResourceName, number>>): void;
  placeSetupSettlement(vertex: number): void;
  placeSetupRoad(edge: [number, number]): void;
}

export const useGameStore = create<GameStore>((set, get) => ({
  screen: "landing",
  username: "",
  roomId: "",
  lobby: null,
  game: null,
  chat: [],
  errorToast: null,
  diceAnimation: null,
  buildMode: { type: "none" },

  init() {
    const s = getSocket();

    s.on("lobby:created", (data: { room_id: string; you: string }) => {
      set({ roomId: data.room_id, username: data.you, screen: "lobby" });
    });
    s.on("lobby:joined", (data: { room_id: string; you: string }) => {
      set({ roomId: data.room_id, username: data.you, screen: "lobby" });
    });
    s.on("lobby:update", (lobby: LobbyDTO) => {
      set({ lobby });
    });
    s.on("game:started", () => {
      set({ screen: "game" });
    });
    s.on("game:state", (state: GameStateDTO) => {
      const prev = get().game;
      // Play build chime when any player's settlement/road/city count grows.
      if (prev) {
        const prevTotals = totalPieces(prev);
        const nextTotals = totalPieces(state);
        if (nextTotals > prevTotals) playSound("build");
      }
      set({
        game: state,
        screen: state.phase === "GAME_OVER" ? "gameover" : "game",
      });
    });
    s.on("game:dice", (data: { roll: number }) => {
      playSound("dice");
      set({ diceAnimation: data.roll });
      setTimeout(() => set({ diceAnimation: null }), 2500);
    });
    s.on("game:over", () => {
      set({ screen: "gameover" });
    });
    s.on("chat:message", (msg: ChatMessage) => {
      set((st) => ({ chat: [...st.chat, msg] }));
    });
    s.on("error", (data: { message: string }) => {
      playSound("error");
      set({ errorToast: data.message });
      setTimeout(() => {
        if (get().errorToast === data.message) set({ errorToast: null });
      }, 4000);
    });
  },

  createRoom(username) {
    getSocket().emit("lobby:create", { username });
  },
  joinRoom(username, roomId) {
    getSocket().emit("lobby:join", { username, room_id: roomId });
  },
  addBot() {
    getSocket().emit("lobby:add_bot", {});
  },
  startGame() {
    getSocket().emit("lobby:start", {});
  },
  sendChat(message) {
    getSocket().emit("lobby:chat", { message });
  },

  setBuildMode(mode) {
    set({ buildMode: mode });
  },
  clearError() {
    set({ errorToast: null });
  },

  roll() {
    getSocket().emit("turn:roll", {});
  },
  endTurn() {
    getSocket().emit("turn:end", {});
    set({ buildMode: { type: "none" } });
  },
  buildRoad(edge) {
    getSocket().emit("build:road", { edge });
    set({ buildMode: { type: "none" } });
  },
  buildSettlement(vertex) {
    getSocket().emit("build:settlement", { vertex });
    set({ buildMode: { type: "none" } });
  },
  buildCity(vertex) {
    getSocket().emit("build:city", { vertex });
    set({ buildMode: { type: "none" } });
  },
  buyDevCard() {
    getSocket().emit("devcard:buy", {});
  },
  playDevCard(kind, payload) {
    getSocket().emit("devcard:play", { kind, ...(payload ?? {}) });
  },
  offerTrade(to, offer, request) {
    getSocket().emit("trade:offer", { to, offer, request });
  },
  acceptTrade(trade_id) {
    getSocket().emit("trade:accept", { trade_id });
  },
  rejectTrade(trade_id) {
    getSocket().emit("trade:reject", { trade_id });
  },
  cancelTrade(trade_id) {
    getSocket().emit("trade:cancel", { trade_id });
  },
  maritimeTrade(give, get) {
    getSocket().emit("trade:maritime", { give, get });
  },
  moveRobber(hex) {
    getSocket().emit("robber:move", { hex });
    set({ buildMode: { type: "none" } });
  },
  stealFrom(target) {
    getSocket().emit("robber:steal", { target });
  },
  discard(resources) {
    getSocket().emit("discard:submit", { resources });
  },
  placeSetupSettlement(vertex) {
    getSocket().emit("setup:place_settlement", { vertex });
  },
  placeSetupRoad(edge) {
    getSocket().emit("setup:place_road", { edge });
  },
}));

// Derived helpers
export function isMyTurn(state: GameStore): boolean {
  return !!state.game && state.game.current_player === state.username;
}

function totalPieces(state: GameStateDTO): number {
  let n = 0;
  for (const p of Object.values(state.players)) {
    n += p.settlements.length + p.cities.length + p.roads.length;
  }
  return n;
}
