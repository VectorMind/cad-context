/**
 * The client half of the regeneration contract — framework-free, so it can be
 * driven by a test without a browser.
 *
 * Rules it enforces (see `specifications/web-app/spec.md`):
 *  - at most **one** request in flight;
 *  - changes arriving while one is running collapse into a single pending
 *    request carrying the latest values (latest-wins), dispatched when the
 *    in-flight one settles;
 *  - a response whose `seq` is older than the newest applied one is discarded,
 *    so a stale render never overwrites a fresh one.
 *
 * Dragging a slider therefore costs at most one queued generation, no matter
 * how many values it passes through.
 */

export interface RegenerationRequest {
  generator: string;
  params: Record<string, unknown>;
  changed: string | null;
  seq: number;
}

export interface RegenerationResponse {
  seq: number;
  artifacts?: Record<string, string>;
  timings?: { total_ms: number; cli_ms: number };
  status?: string;
  params?: Record<string, unknown>;
  metrics?: Record<string, unknown>;
  notes?: string[];
  error?: string;
}

export interface RegenerationStats {
  /** Requests actually sent. */
  dispatched: number;
  /** Parameter changes folded into an already-pending request. */
  coalesced: number;
  /** Responses dropped because a newer one had already been applied. */
  discarded: number;
}

export interface RegenerationState {
  artifacts: Record<string, string>;
  metrics: Record<string, unknown>;
  notes: string[];
  error: string | null;
  busy: boolean;
  /** Round-trip of the last applied response, milliseconds. */
  lastMs: number | null;
  /** Server-side `cadctx` time of the last applied response, milliseconds. */
  cliMs: number | null;
  stats: RegenerationStats;
}

export const initialState: RegenerationState = {
  artifacts: {},
  metrics: {},
  notes: [],
  error: null,
  busy: false,
  lastMs: null,
  cliMs: null,
  stats: { dispatched: 0, coalesced: 0, discarded: 0 },
};

export interface SchedulerOptions {
  generator: string;
  send: (request: RegenerationRequest) => Promise<RegenerationResponse>;
  onState: (state: RegenerationState) => void;
  /** Idle changes wait this long before the first dispatch. */
  debounceMs?: number;
  now?: () => number;
}

export class RegenerationScheduler {
  private state: RegenerationState = { ...initialState };
  private seq = 0;
  private appliedSeq = 0;
  private inFlight = false;
  private pending: { params: Record<string, unknown>; changed: string | null } | null = null;
  private timer: ReturnType<typeof setTimeout> | null = null;
  private disposed = false;
  private readonly options: SchedulerOptions;
  private readonly debounceMs: number;
  private readonly now: () => number;

  // Plain assignment rather than constructor parameter properties: this file is
  // executed directly by `node --test` through type stripping, which only
  // erases syntax and cannot synthesize fields.
  constructor(options: SchedulerOptions) {
    this.options = options;
    this.debounceMs = options.debounceMs ?? 150;
    this.now = options.now ?? (() => Date.now());
  }

  snapshot(): RegenerationState {
    return this.state;
  }

  /** Record a parameter change. Dispatch timing is this class's business. */
  request(params: Record<string, unknown>, changed: string | null = null): void {
    if (this.disposed) return;
    const replacing = this.pending !== null;
    this.pending = { params, changed };
    if (replacing) {
      this.patch({ stats: { ...this.state.stats, coalesced: this.state.stats.coalesced + 1 } });
    }
    if (this.inFlight) {
      this.patch({ busy: true });
      return; // dispatched when the in-flight request settles
    }
    // First change after an idle period starts the clock; later changes only
    // replace the payload. A timer that restarts on every change would never
    // fire while a slider is being dragged continuously.
    if (this.timer === null) this.timer = setTimeout(() => this.flush(), this.debounceMs);
  }

  dispose(): void {
    this.disposed = true;
    if (this.timer !== null) clearTimeout(this.timer);
    this.timer = null;
  }

  private flush(): void {
    this.timer = null;
    if (this.disposed || this.inFlight || !this.pending) return;
    const { params, changed } = this.pending;
    this.pending = null;
    this.inFlight = true;
    const seq = (this.seq += 1);
    const started = this.now();
    this.patch({ busy: true, stats: { ...this.state.stats, dispatched: this.state.stats.dispatched + 1 } });

    this.options
      .send({ generator: this.options.generator, params, changed, seq })
      .then((data) => this.apply(data, started))
      .catch((error: unknown) => {
        this.patch({ error: error instanceof Error ? error.message : String(error) });
      })
      .finally(() => {
        this.inFlight = false;
        if (this.disposed) return;
        this.patch({ busy: this.pending !== null });
        // The debounce was already paid by the request that just finished, so a
        // queued change goes out at once.
        if (this.pending) this.flush();
      });
  }

  private apply(data: RegenerationResponse, started: number): void {
    if (this.disposed) return;
    if (data.seq < this.appliedSeq) {
      this.patch({ stats: { ...this.state.stats, discarded: this.state.stats.discarded + 1 } });
      return;
    }
    this.appliedSeq = data.seq;
    this.patch({
      error: data.error ?? null,
      artifacts: data.artifacts ?? this.state.artifacts,
      metrics: data.metrics ?? this.state.metrics,
      notes: data.notes ?? [],
      lastMs: Math.round(this.now() - started),
      cliMs: data.timings?.cli_ms ?? null,
    });
  }

  private patch(part: Partial<RegenerationState>): void {
    this.state = { ...this.state, ...part };
    this.options.onState(this.state);
  }
}

/** The transport used in the browser: `POST /api/generate`. */
export async function postGenerate(request: RegenerationRequest): Promise<RegenerationResponse> {
  const response = await fetch('/api/generate', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(request),
  });
  return (await response.json()) as RegenerationResponse;
}
