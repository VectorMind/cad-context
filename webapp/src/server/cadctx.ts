/**
 * The bridge to the Python side.
 *
 * The web app owns no geometry logic. Everything it knows about shapes comes
 * from the `cadctx` CLI — the single documented interface of this repository
 * (`specifications/agent-interface/spec.md`) — invoked as a subprocess from
 * Astro SSR handlers. Nothing here parses a CAD file or reimplements a
 * parameter range; the CLI's `--json` payload is the only source.
 */
import { execFile } from 'node:child_process';
import { existsSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

export interface CadctxResult {
  command: string;
  status: 'ok' | 'degraded' | 'error';
  summary: string;
  timestamp: string;
  facts: Record<string, unknown>;
  files: string[];
  report: string | null;
  notes: string[];
  data: Record<string, any>;
}

export interface ParameterSpec {
  name: string;
  type: 'number' | 'integer' | 'string' | 'boolean';
  default: number | string | boolean;
  minimum: number | null;
  maximum: number | null;
  step: number | null;
  unit: string;
  options: string[] | null;
  control: string;
  description: string;
}

export interface GeneratorSchema {
  generator: string;
  title: string;
  kind: '2d' | '3d';
  backend: string;
  /** Generators that build the same part on different backends share a family. */
  family: string;
  formats: string[];
  description: string;
  parameters: ParameterSpec[];
}

export interface GeneratorInfo {
  id: string;
  title: string;
  kind: '2d' | '3d';
  backend: string;
  family: string;
  formats: string[];
  available: boolean;
  description: string;
}

/** Repository root: the parent of `webapp/`, or `CAD_CONTEXT_ROOT` when set. */
export function repoRoot(): string {
  const override = process.env.CAD_CONTEXT_ROOT;
  if (override) return resolve(override);
  const here = dirname(fileURLToPath(import.meta.url)); // …/webapp/src/server
  let dir = here;
  for (let up = 0; up < 6; up += 1) {
    if (existsSync(join(dir, 'pyproject.toml'))) return dir;
    dir = dirname(dir);
  }
  return resolve(here, '../../..');
}

/**
 * How the CLI is launched. `uv run cadctx` is the documented invocation;
 * `CADCTX_COMMAND` overrides it for an environment where `cadctx` is already
 * on PATH (e.g. an activated venv), so the app never hardcodes a runner.
 */
function launcher(): { file: string; prefix: string[] } {
  const override = process.env.CADCTX_COMMAND;
  if (override) {
    const parts = override.split(' ').filter(Boolean);
    return { file: parts[0]!, prefix: parts.slice(1) };
  }
  return { file: 'uv', prefix: ['run', 'cadctx'] };
}

export class CadctxError extends Error {
  constructor(
    message: string,
    readonly result?: CadctxResult,
    readonly stderr?: string,
  ) {
    super(message);
    this.name = 'CadctxError';
  }
}

/** Run one `cadctx --json` command and return its parsed result payload. */
export function cadctx(args: string[], timeoutMs = 180_000): Promise<CadctxResult> {
  const { file, prefix } = launcher();
  const argv = [...prefix, '--json', ...args];
  return new Promise((resolvePromise, reject) => {
    execFile(
      file,
      argv,
      { cwd: repoRoot(), timeout: timeoutMs, maxBuffer: 64 * 1024 * 1024, windowsHide: true },
      (error, stdout, stderr) => {
        let payload: CadctxResult | undefined;
        try {
          payload = JSON.parse(stdout) as CadctxResult;
        } catch {
          payload = undefined;
        }
        // A failing command still writes its result payload to stdout before
        // exiting non-zero, so an error carries the same structure as success.
        if (error && !payload) {
          reject(
            new CadctxError(
              `${file} ${argv.join(' ')} failed: ${error.message}`,
              undefined,
              stderr,
            ),
          );
          return;
        }
        if (!payload) {
          reject(new CadctxError('cadctx produced no JSON payload', undefined, stderr));
          return;
        }
        if (payload.status === 'error') {
          reject(new CadctxError(payload.summary, payload, stderr));
          return;
        }
        resolvePromise(payload);
      },
    );
  });
}

/**
 * Answers that cannot change while the server runs (the registry, a parameter
 * schema, the workspace layout) are fetched once. Regeneration is never
 * cached — it is the whole point of the app.
 */
const memo = new Map<string, Promise<any>>();
function once<T>(key: string, produce: () => Promise<T>): Promise<T> {
  let hit = memo.get(key) as Promise<T> | undefined;
  if (!hit) {
    hit = produce().catch((err) => {
      memo.delete(key);
      throw err;
    });
    memo.set(key, hit);
  }
  return hit;
}

export function listGenerators(): Promise<GeneratorInfo[]> {
  return once('generators', async () => (await cadctx(['generators'])).data.generators);
}

export function generatorSchema(id: string): Promise<GeneratorSchema> {
  return once(`schema:${id}`, async () => (await cadctx(['schema', id])).data as GeneratorSchema);
}

export function workspaceLayout(): Promise<Record<string, string>> {
  return once('paths', async () => (await cadctx(['paths'])).data.layout);
}

/** Absolute path of the `.cache/cad/` root, resolved from `cadctx paths`. */
export async function cadDir(): Promise<string> {
  const layout = await workspaceLayout();
  return resolve(repoRoot(), layout.cad ?? '.cache/cad');
}

/**
 * Serialize generation per generator.
 *
 * Geometry paths are fixed (`specifications/workspace-layout/spec.md`), so two
 * concurrent runs of the same generator would write the same file. The client
 * already keeps one request in flight; this makes a second browser tab safe
 * too.
 */
const queues = new Map<string, Promise<unknown>>();
export function serialized<T>(key: string, work: () => Promise<T>): Promise<T> {
  const previous = queues.get(key) ?? Promise.resolve();
  const next = previous.then(work, work);
  queues.set(
    key,
    next.catch(() => undefined),
  );
  return next;
}

export interface GenerateOutcome {
  status: string;
  files: Record<string, string>;
  metrics: Record<string, unknown>;
  skipped: Record<string, string>;
  params: Record<string, unknown>;
  cliMs: number;
}

/** Generate one shape: `cadctx generate <id> -p k=v … -f <format>`. */
export async function generate(
  generatorId: string,
  params: Record<string, unknown>,
  formats: string[],
): Promise<GenerateOutcome> {
  const args = ['generate', generatorId, '--no-measure'];
  for (const [key, value] of Object.entries(params)) args.push('-p', `${key}=${value}`);
  for (const format of formats) args.push('-f', format);
  return serialized(generatorId, async () => {
    const started = Date.now();
    const result = await cadctx(args);
    return {
      status: result.status,
      files: result.data.files ?? {},
      metrics: result.data.metrics ?? {},
      skipped: result.data.skipped ?? {},
      params: result.data.params ?? {},
      cliMs: Date.now() - started,
    };
  });
}
