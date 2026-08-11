/**
 * The editable contract for one generator: the exposed knobs with their
 * ranges (read from the generator), plus the parameters held at their default.
 */
import type { APIRoute } from 'astro';

import { exposedSchema } from '../../../server/exposure.ts';

export const prerender = false;

export const GET: APIRoute = async ({ params }) => {
  try {
    const exposed = await exposedSchema(params.generator ?? '');
    return new Response(JSON.stringify(exposed, null, 2), {
      headers: { 'content-type': 'application/json', 'cache-control': 'no-store' },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    return new Response(JSON.stringify({ error: message }, null, 2), {
      status: 404,
      headers: { 'content-type': 'application/json' },
    });
  }
};
