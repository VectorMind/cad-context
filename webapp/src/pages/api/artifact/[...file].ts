/**
 * Serves generated geometry out of `.cache/cad/`.
 *
 * The directory is resolved from `cadctx paths`, never hardcoded, and a
 * request can only reach a file inside it.
 */
import { createReadStream } from 'node:fs';
import { stat } from 'node:fs/promises';
import { resolve, sep } from 'node:path';
import { Readable } from 'node:stream';

import type { APIRoute } from 'astro';

import { cadDir } from '../../../server/cadctx.ts';

export const prerender = false;

const CONTENT_TYPES: Record<string, string> = {
  glb: 'model/gltf-binary',
  gltf: 'model/gltf+json',
  stl: 'model/stl',
  svg: 'image/svg+xml',
  dxf: 'image/vnd.dxf',
  step: 'application/step',
  scad: 'text/plain; charset=utf-8',
};

export const GET: APIRoute = async ({ params }) => {
  const requested = params.file ?? '';
  const root = await cadDir();
  const target = resolve(root, requested);
  if (target !== root && !target.startsWith(root + sep)) {
    return new Response('forbidden', { status: 403 });
  }
  let size: number;
  try {
    const info = await stat(target);
    if (!info.isFile()) throw new Error('not a file');
    size = info.size;
  } catch {
    return new Response(`no artifact at ${requested} — generate it first`, { status: 404 });
  }
  const extension = target.split('.').pop()?.toLowerCase() ?? '';
  const stream = Readable.toWeb(createReadStream(target)) as ReadableStream;
  return new Response(stream, {
    headers: {
      'content-type': CONTENT_TYPES[extension] ?? 'application/octet-stream',
      'content-length': String(size),
      // Fixed paths + regeneration in place: a cached copy would be stale.
      'cache-control': 'no-store',
    },
  });
};
