// ============================================================
// Game API Client — Grey Fog (灰雾调查录)
// ============================================================

import type {
  NewGameRequest,
  NewGameResponse,
  ActionRequest,
  ActionResponse,
  GameView,
  SaveResponse,
  LoadResponse,
  CaseListResponse,
  CaseMeta,
} from "./types";

const BASE_URL = "http://localhost:8001";

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const res = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    },
    ...options,
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API error ${res.status}: ${body}`);
  }

  return res.json() as Promise<T>;
}

/** Create a new game */
export async function newGame(req: NewGameRequest): Promise<NewGameResponse> {
  return request<NewGameResponse>("/v1/game/new", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

/** Execute an action in the game */
export async function executeAction(
  saveId: string,
  req: ActionRequest
): Promise<ActionResponse> {
  return request<ActionResponse>(`/v1/game/${saveId}/action`, {
    method: "POST",
    body: JSON.stringify(req),
  });
}

/** Get the current game view */
export async function getView(saveId: string): Promise<GameView> {
  return request<GameView>(`/v1/game/${saveId}/view`);
}

/** Save the game */
export async function saveGame(saveId: string): Promise<SaveResponse> {
  return request<SaveResponse>(`/v1/game/${saveId}/save`, {
    method: "POST",
  });
}

/** Load a saved game */
export async function loadGame(saveId: string): Promise<LoadResponse> {
  return request<LoadResponse>(`/v1/game/${saveId}/load`, {
    method: "POST",
  });
}

/** List all available cases */
export async function listCases(): Promise<CaseListResponse> {
  return request<CaseListResponse>("/v1/cases");
}

/** Get metadata for a specific case */
export async function getCaseMeta(
  caseId: string
): Promise<CaseMeta> {
  return request<CaseMeta>(`/v1/cases/${caseId}/metadata`);
}
