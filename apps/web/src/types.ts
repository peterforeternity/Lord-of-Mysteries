// ============================================================
// Game API TypeScript Interfaces — Grey Fog (灰雾调查录)
// ============================================================

/** Player status values */
export interface PlayerStatus {
  spirituality: number;
  corruption: number;
  stability: number;
  max_spirituality: number;
  max_corruption: number;
  max_stability: number;
}

/** An item in the player's inventory */
export interface Item {
  id: string;
  name: string;
  description: string;
  quantity: number;
  usable: boolean;
}

/** A location in the game world */
export interface Location {
  id: string;
  name: string;
  description: string;
  is_current: boolean;
  is_visited: boolean;
  available_actions: Action[];
}

/** An action the player can take */
export interface Action {
  id: string;
  name: string;
  description: string;
  action_type: string;
  requires_item?: string;
  requires_condition?: string;
}

/** A clue discovered during investigation */
export interface Clue {
  id: string;
  name: string;
  description: string;
  source: string;
  discovered_at: string;
  is_key: boolean;
}

/** An NPC met during the game */
export interface Npc {
  id: string;
  name: string;
  description: string;
  dialogue_available: boolean;
  statements: string[];
}

/** A hypothesis the player can form */
export interface Hypothesis {
  id: string;
  title: string;
  description: string;
  status: "locked" | "unlocked" | "confirmed" | "refuted";
  required_clues: string[];
  progress: number;
}

/** A task or objective */
export interface Task {
  id: string;
  title: string;
  description: string;
  status: "active" | "completed" | "failed";
}

/** A ritual template */
export interface Ritual {
  id: string;
  name: string;
  description: string;
  required_materials: RitualMaterial[];
  is_available: boolean;
}

/** Material required for a ritual */
export interface RitualMaterial {
  item_id: string;
  item_name: string;
  quantity: number;
  has_enough: boolean;
}

/** A single event log entry */
export interface EventLogEntry {
  id: string;
  timestamp: string;
  type: "info" | "discovery" | "dialogue" | "ritual" | "combat" | "system";
  content: string;
}

/** Divination result */
export interface DivinationResult {
  id: string;
  content: string;
  interpretation: string;
  potency: number;
}

/** Full game view returned by the API */
export interface GameView {
  save_id: string;
  case_id: string;
  case_name: string;
  chapter: string;
  scene_id: string;
  scene_name: string;
  scene_description: string;
  player_status: PlayerStatus;
  locations: Location[];
  current_location: Location;
  items: Item[];
  clues: Clue[];
  npcs: Npc[];
  hypotheses: Hypothesis[];
  active_tasks: Task[];
  available_actions: Action[];
  event_log: EventLogEntry[];
  dialogue_content: string | null;
  dialogue_options: string[];
  rituals: Ritual[];
  divination_results: DivinationResult[];
  is_game_over: boolean;
  ending_type: string | null;
  ending_description: string | null;
}

/** Case metadata */
export interface CaseMeta {
  case_id: string;
  title: string;
  description: string;
  difficulty: string;
  estimated_hours: string;
  is_available: boolean;
}

/** Case list response */
export interface CaseListResponse {
  cases: CaseMeta[];
}

/** New game request */
export interface NewGameRequest {
  case_id: string;
  player_name?: string;
}

/** New game response */
export interface NewGameResponse {
  save_id: string;
  view: GameView;
}

/** Action request */
export interface ActionRequest {
  action_id: string;
  parameters?: Record<string, unknown>;
}

/** Action response */
export interface ActionResponse {
  view: GameView;
  message: string;
}

/** Save response */
export interface SaveResponse {
  success: boolean;
  save_id: string;
  saved_at: string;
}

/** Load response */
export interface LoadResponse {
  success: boolean;
  view: GameView;
}

/** Save slot metadata */
export interface SaveSlot {
  slot_id: string;
  save_id: string;
  case_name: string;
  chapter: string;
  location: string;
  saved_at: string;
  play_time: string;
}
