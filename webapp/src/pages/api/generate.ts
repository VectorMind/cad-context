/**
 * The regeneration bridge: browser → SSR handler → `cadctx` → fresh artifact.
 *
 * Request  `{ generator, params, changed?, seq }`
 * Response `{ seq, artifacts, timings }` — or `{ seq, error }`.
 *
 * `params` is always the full editable set (the mode-(a) subprocess bridge is
 * stateless); `changed` names the single parameter that moved and is ignored
 * here — it exists so a warm worker can drop in behind the same contract.
 * The contract lives in `specifications/web-app/spec.md`.
 */
import type { APIRoute } from 'astro';

import { generate } from '../../server/cadctx.ts';
import { checkParameters, exposedSchema } from '../../server/exposure.ts';

export const prerender = false;

interface GenerateRequest {
  generator?: string;
  params?: Record<string, unknown>;
  changed?: string | null;
  seq?: number;
}

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json', 'cache-control': 'no-store' },
  });

export const POST: APIRoute = async ({ request }) => {
  const started = Date.now();
  let body: GenerateRequest;
  try {
    body = (await request.json()) as GenerateRequest;
  } catch {
    return json({ seq: 0, error: 'request body must be JSON' }, 400);
  }
  const seq = typeof body.seq === 'number' ? body.seq : 0;
  const generatorId = body.generator ?? '';

  try {
    const exposed = await exposedSchema(generatorId);
    const params = checkParameters(exposed, body.params ?? {});
    const outcome = await generate(generatorId, params, [exposed.preview]);
    const stamp = Date.now();
    const artifacts: Record<string, string> = {};
    for (const [format, path] of Object.entries(outcome.files)) {
      // Geometry paths are fixed by contract, so the URL is stable across a
      // whole session; the query only defeats the browser cache.
      artifacts[format] = `/api/artifact/${path.split('/').slice(-2).join('/')}?v=${stamp}`;
    }
    return json({
      seq,
      artifacts,
      timings: { total_ms: Date.now() - started, cli_ms: outcome.cliMs },
      status: outcome.status,
      params: outcome.params,
      metrics: outcome.metrics,
      notes: Object.entries(outcome.skipped).map(([f, why]) => `${f} skipped: ${why}`),
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    return json({ seq, error: message }, 400);
  }
};
