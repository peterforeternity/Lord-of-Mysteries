/** Performance metrics for a single user interaction */
export interface InteractionMetric {
  interaction_start: number;
  visual_feedback_shown: number;
  request_sent: number;
  response_received: number;
  view_committed: number;
  navigation_completed: number;
  input_to_feedback_ms: number;
  request_duration_ms: number;
  response_to_render_ms: number;
  total_interaction_ms: number;
  success: boolean;
  error_code: string | null;
  route: string;
  action_type: string;
  target_id: string;
  state_version: number;
}

const MAX_METRICS = 100;

/** Simple performance monitor that records interaction metrics */
export class PerformanceMonitor {
  private metrics: InteractionMetric[] = [];

  /** Create a new metric record and return its index */
  start(): number {
    const metric: InteractionMetric = {
      interaction_start: performance.now(),
      visual_feedback_shown: 0,
      request_sent: 0,
      response_received: 0,
      view_committed: 0,
      navigation_completed: 0,
      input_to_feedback_ms: 0,
      request_duration_ms: 0,
      response_to_render_ms: 0,
      total_interaction_ms: 0,
      success: false,
      error_code: null,
      route: "",
      action_type: "",
      target_id: "",
      state_version: 0,
    };
    const idx = this.metrics.push(metric) - 1;
    return idx;
  }

  /** Mark a timestamp for a given metric index */
  mark(
    idx: number,
    phase: keyof Pick<
      InteractionMetric,
      | "visual_feedback_shown"
      | "request_sent"
      | "response_received"
      | "view_committed"
      | "navigation_completed"
    >
  ): void {
    const m = this.metrics[idx];
    if (m) {
      m[phase] = performance.now();
    }
  }

  /** Complete and record the metric */
  end(
    idx: number,
    overrides: Partial<
      Pick<
        InteractionMetric,
        | "success"
        | "error_code"
        | "route"
        | "action_type"
        | "target_id"
        | "state_version"
      >
    >
  ): void {
    const m = this.metrics[idx];
    if (!m) return;

    const now = performance.now();
    m.total_interaction_ms = now - m.interaction_start;

    if (m.visual_feedback_shown > 0) {
      m.input_to_feedback_ms = m.visual_feedback_shown - m.interaction_start;
    }
    if (m.response_received > 0 && m.request_sent > 0) {
      m.request_duration_ms = m.response_received - m.request_sent;
    }
    if (m.view_committed > 0 && m.response_received > 0) {
      m.response_to_render_ms = m.view_committed - m.response_received;
    }

    Object.assign(m, overrides);

    // Trim oldest metrics if exceeding limit
    if (this.metrics.length > MAX_METRICS) {
      this.metrics = this.metrics.slice(-MAX_METRICS);
    }

    if (import.meta.env.DEV) {
      console.debug("[Perf]", m);
    }
  }

  /** Get all recorded metrics */
  getAll(): InteractionMetric[] {
    return [...this.metrics];
  }

  /** Get average interaction duration for recent successful actions */
  getAverageDuration(count = 10): number {
    const recent = this.metrics
      .filter((m) => m.success)
      .slice(-count);
    if (recent.length === 0) return 0;
    return (
      recent.reduce((sum, m) => sum + m.total_interaction_ms, 0) /
      recent.length
    );
  }

  /** Clear all metrics */
  clear(): void {
    this.metrics = [];
  }
}

/** Singleton instance */
export const perfMonitor = new PerformanceMonitor();
