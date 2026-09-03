// Mirrors catan/src/phase.py::TurnPhase
export type TurnPhase =
  | "SETUP_1"
  | "SETUP_2"
  | "ROLL"
  | "DISCARD"
  | "MOVE_ROBBER"
  | "ROBBER_STEAL"
  | "MAIN"
  | "GAME_OVER";

export type ResourceName = "LUMBER" | "BRICK" | "WOOL" | "GRAIN" | "ORE";
export const RESOURCES: ResourceName[] = ["LUMBER", "BRICK", "WOOL", "GRAIN", "ORE"];

export interface HarborDTO {
  ratio: number;
  resource: ResourceName | null;
  location: [number, number] | null;
}

export interface DevCardDTO {
  kind: "knight" | "victory_point" | "monopoly" | "road_building" | "year_of_plenty";
  name: string;
}

export interface PlayerDTO {
  name: string;
  color: string;
  is_bot: boolean;
  connected: boolean;
  settlements: number[];
  cities: number[];
  roads: [number, number][];
  public_victory_points: number;
  knights: number;
  has_longest_road: boolean;
  has_largest_army: boolean;
  resource_count: number;
  dev_card_count: number;
  harbors: HarborDTO[];
  // Present only for the viewer
  resources?: Record<ResourceName, number>;
  development_cards?: DevCardDTO[];
  new_development_cards?: DevCardDTO[];
  victory_points?: number;
}

export interface TileDTO {
  resource: ResourceName | "DESERT";
  number: number;
}

export interface BoardDTO {
  tiles: TileDTO[];
  robber_location: number;
  tile_to_vertices: Record<string, number[]>;
  harbors: HarborDTO[];
  edges: [number, number][];
}

export interface TradeDTO {
  id: number;
  from: string;
  to: string[];
  offer: Partial<Record<ResourceName, number>>;
  request: Partial<Record<ResourceName, number>>;
  responses: Record<string, boolean>;
}

export interface GameStateDTO {
  phase: TurnPhase;
  turn: number;
  current_player: string;
  current_player_index: number;
  dice_roll: number | null;
  winner: string | null;
  players: Record<string, PlayerDTO>;
  player_order: string[];
  board: BoardDTO;
  setup: { expects_road_for: number | null; step: number; order: string[] } | null;
  pending_discards: Record<string, number>;
  pending_steal_targets: string[];
  pending_trades: TradeDTO[];
  dev_card_deck_count: number;
  log: string[];
}

export interface LobbyPlayer {
  name: string;
  is_bot: boolean;
  connected: boolean;
}

export interface LobbyDTO {
  id: string;
  host: string;
  started: boolean;
  players: LobbyPlayer[];
}
