/** The app's registry: every generator, with the knobs it exposes. */
import type { APIRoute } from 'astro';

import { listGenerators } from '../../server/cadctx.ts';
import { exposureFor } from '../../server/exposure.ts';

export const prerender = false;

export const GET: APIRoute = async () => {
  const generators = await listGenerators();
  const body = generators.map((g) => ({
    id: g.id,
    title: g.title,
    kind: g.kind,
    backend: g.backend,
    available: g.available,
    formats: g.formats,
    editable: exposureFor(g.id).editable,
    viewer: `/viewer/${g.id}`,
  }));
  return new Response(JSON.stringify({ generators: body }, null, 2), {
    headers: { 'content-type': 'application/json', 'cache-control': 'no-store' },
  });
};
