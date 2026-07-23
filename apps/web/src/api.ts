import type {
  NewGameResponse,
  ActionRequest,
  ActionResponse,
  GameView,
  CaseListResponse,
  CaseMeta,
} from "./types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const REQUEST_TIMEOUT_MS = 30_000;

/** Generate a unique request ID using crypto.randomUUID() */
export function generateRequestId(): string {
  return crypto.randomUUID();
}

/** Generate an idempotency key for action deduplication */
export function generateIdempotencyKey(): string {
  return `${Date.now()}-${crypto.randomUUID().slice(0, 8)}`;
}

/** Extended request options with session ID and abort signal support */
interface RequestOptions extends RequestInit {
  sessionId?: string | null;
  requestId?: string;
  signal?: AbortSignal;
}

async function request<T>(
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  const requestId = options.requestId ?? generateRequestId();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "X-Request-ID": requestId,
    ...(options.headers as Record<string, string>),
  };

  if (options.sessionId) {
    headers["X-Session-ID"] = options.sessionId;
  }

  // Set up timeout via AbortController
  let timeoutId: ReturnType<typeof setTimeout> | undefined;
  let controller: AbortController | undefined;

  if (!options.signal) {
    controller = new AbortController();
    timeoutId = setTimeout(() => controller!.abort(), REQUEST_TIMEOUT_MS);
  }

  const url = `${BASE_URL}${path}`;
  try {
    const res = await fetch(url, {
      ...options,
      headers,
      signal: options.signal ?? controller?.signal,
    });

    if (!res.ok) {
      const body = await res.text();
      const err = new Error(`API error ${res.status}: ${body}`) as Error & { statusCode: number };
      err.statusCode = res.status;
      throw err;
    }

    return res.json() as Promise<T>;
  } finally {
    if (timeoutId !== undefined) {
      clearTimeout(timeoutId);
    }
  }
}

/** Create a new game */
export async function newGame(
  caseId: string,
  seed?: number
): Promise<NewGameResponse> {
  const params = new URLSearchParams({ case_id: caseId });
  if (seed !== undefined) {
    params.set("seed", String(seed));
  }
  return request<NewGameResponse>(`/v1/game/new?${params.toString()}`, {
    method: "POST",
  });
}

/** Execute an action in the game — automatically includes idempotency_key */
export async function executeAction(
  saveId: string,
  req: ActionRequest,
  sessionId?: string | null
): Promise<ActionResponse> {
  const body = {
    ...req,
    idempotency_key: generateIdempotencyKey(),
  };
  return request<ActionResponse>(`/v1/game/${saveId}/action`, {
    method: "POST",
    body: JSON.stringify(body),
    sessionId,
  });
}

/** Get the current game view */
export async function getView(
  saveId: string,
  sessionId?: string | null
): Promise<GameView> {
  return request<GameView>(`/v1/game/${saveId}/view`, {
    sessionId,
  });
}

/** Save the game */
export async function saveGame(
  saveId: string,
  sessionId?: string | null
): Promise<{ success: boolean; save_id: string }> {
  return request<{ success: boolean; save_id: string }>(`/v1/game/${saveId}/save`, {
    method: "POST",
    sessionId,
  });
}

/** Load a saved game */
export async function loadGame(
  saveId: string,
  sessionId?: string | null
): Promise<GameView> {
  return request<GameView>(`/v1/game/${saveId}/load`, {
    method: "POST",
    sessionId,
  });
}

/** List all available cases */
export async function listCases(): Promise<CaseListResponse> {
  return request<CaseListResponse>("/v1/cases");
}

/** Get metadata for a specific case */
export async function getCaseMeta(caseId: string): Promise<CaseMeta> {
  return request<CaseMeta>(`/v1/cases/${caseId}/metadata`);
}
