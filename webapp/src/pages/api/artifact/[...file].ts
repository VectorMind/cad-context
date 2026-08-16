/**
 * Serves generated geometry out of `.cache/cad/`.
 *
 * The directory is resolved from `cadctx paths`, never hardcoded, and a
 * request can only reach a file inside it.
 */
import { createReadStream } from 'node:fs';
import { realpath, stat } from 'node:fs/promises';
import { resolve, sep } from 'node:path';
import { Readable } from 'node:stream';

import type { APIRoute } from 'astro';

import { listGenerators } from '../../../server/cadctx.ts';

export const prerender = false;

const CONTENT_TYPES: Record<string, string> = {
  glb: 'model/gltf-binary',
  gltf: 'model/gltf+json',
  stl: 'model/stl',
  svg: 'image/svg+xml',
  dxf: 'image/vnd.dxf',
  json: 'application/json',
  step: 'application/step',
  scad: 'text/plain; charset=utf-8',
};

export const GET: APIRoute = async ({ params }) => {
  const requested = params.file ?? '';
  const [generatorId, ...relativeParts] = requested.split('/').filter(Boolean);
  const generator = (await listGenerators()).find((item) => item.id === generatorId);
  if (!generator || relativeParts.length !== 1) {
    return new Response('unknown artifact path', { status: 404 });
  }
  const declaredRoot = resolve(generator.artifact_root, generator.id);
  const target = resolve(declaredRoot, relativeParts[0]!);
  if (target !== declaredRoot && !target.startsWith(declaredRoot + sep)) {
    return new Response('forbidden', { status: 403 });
  }
  let size: number;
  try {
    const info = await stat(target);
    if (!info.isFile()) throw new Error('not a file');
    const [realRoot, realTarget] = await Promise.all([realpath(declaredRoot), realpath(target)]);
    if (realTarget !== realRoot && !realTarget.startsWith(realRoot + sep)) {
      return new Response('forbidden', { status: 403 });
    }
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
