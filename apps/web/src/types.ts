/** Player resource status */
export interface PlayerStatus {
  spirituality: number;
  corruption: number;
  stability: number;
  current_location_id: string;
  current_location_name: string;
  visited_locations: LocationInfo[];
}

/** Location info */
export interface LocationInfo {
  location_id: string;
  display_name: string;
  description: string;
  is_current: boolean;
  has_been_visited: boolean;
  available_clues: ClueInfo[];
  available_npcs: string[];
}

/** Clue info */
export interface ClueInfo {
  clue_id: string;
  display_name: string;
  description: string;
  source_type: string;
  is_new: boolean;
}

/** NPC info */
export interface NpcInfo {
  npc_id: string;
  name: string;
  description: string;
  emotion: string;
  current_location_id: string;
  available_claims: ClaimInfo[];
}

/** Claim info */
export interface ClaimInfo {
  claim_id: string;
  content: string;
  is_lie: boolean;
  speaker_believes_it: boolean;
}

/** Hypothesis info */
export interface HypothesisInfo {
  hypothesis_id: string;
  title: string;
  description: string;
  status: string;
  min_confidence: number;
  required_clue_count: number;
  found_clue_count: number;
  can_submit: boolean;
}

/** Ending info */
export interface EndingInfo {
  ending_id: string;
  title: string;
  description: string;
  ending_type: string;
}

/** Item info */
export interface ItemInfo {
  item_id: string;
  name: string;
  description: string;
  active_ability: string;
  holding_cost: string;
}

/** Ritual info */
export interface RitualInfo {
  ritual_id: string;
  name: string;
  purpose: string;
  required_materials: string[];
  space_condition: string;
  steps: string[];
  can_perform: boolean;
}

/** Event log entry */
export interface EventLogEntry {
  event_id: string;
  event_type: string;
  description: string;
  timestamp: string;
}

/** Action info returned by the backend — frontend must render from this data only */
export interface ActionInfo {
  action_id: string;
  action_type: string;
  target_id: string | null;
  label: string;
  enabled: boolean;
  disabled_reason: string | null;
  expected_version: number;
  parameters_schema: Record<string, unknown>;
}

/** Full game state view returned by the API */
export interface GameView {
  state_version: number;
  player: PlayerStatus;
  current_scene: string;
  current_description: string;
  available_actions: ActionInfo[];
  clues: ClueInfo[];
  npcs: NpcInfo[];
  hypotheses: HypothesisInfo[];
  endings: EndingInfo[];
  items: ItemInfo[];
  rituals: RitualInfo[];
  event_log: EventLogEntry[];
  game_over: boolean;
  final_ending: EndingInfo | null;
  ai_enabled: boolean;
}

/** Case metadata */
export interface CaseMeta {
  case_id: string;
  title: string;
  description: string;
  version: string;
}

/** Case list response */
export interface CaseListResponse {
  cases: CaseMeta[];
}

/** New game response */
export interface NewGameResponse {
  save_id: string;
  case_id: string;
  view: GameView;
}

/** Action request */
export interface ActionRequest {
  action_type: string;
  target_id?: string;
  parameters?: Record<string, unknown>;
  expected_version: number;
}

/** Recovery hint returned with recoverable errors */
export interface RecoveryInfo {
  refresh_view: boolean;
  latest_state_version: number;
}

/** Action response */
export interface ActionResponse {
  success: boolean;
  state_version: number;
  events: Array<{ event_type: string; description: string }>;
  view: GameView | null;
  error_code: string | null;
  error_detail: string | null;
  request_id?: string;
  recoverable?: boolean;
  recovery?: RecoveryInfo | null;
}

/** Save/Load response */
export interface SaveResponse {
  success: boolean;
  save_id: string;
}

/** Save slot metadata */
export interface SaveSlot {
  save_id: string;
  case_id: string;
  state_version: number;
  game_over: number;
  created_at: string;
  updated_at: string;
}
