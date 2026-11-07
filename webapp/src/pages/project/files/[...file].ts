import { readFile } from 'node:fs/promises';
import { extname } from 'node:path';
import type { APIRoute } from 'astro';
import { projectInfo } from '../../../server/cadcon.ts';
import { portfolioFile } from '../../../server/portfolio.ts';

export const prerender = false;
const types: Record<string, string> = {
  '.html': 'text/html; charset=utf-8', '.svg': 'image/svg+xml',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp',
  '.json': 'application/json', '.pdf': 'application/pdf', '.glb': 'model/gltf-binary',
  '.stl': 'model/stl', '.step': 'application/step', '.3mf': 'model/3mf',
};
export const GET: APIRoute = async ({ params }) => {
  const project = await projectInfo();
  if (!project.project || !project.portfolio) return new Response('No portfolio', { status: 404 });
  const target = await portfolioFile(project.project, params.file ?? '', project.portfolio.files.map((f) => f.path));
  if (!target) return new Response('Unknown portfolio file', { status: 404 });
  const extension = extname(target).toLowerCase();
  const headers: Record<string, string> = {
    'content-type': types[extension] ?? 'application/octet-stream',
    'cache-control': 'no-store', 'x-content-type-options': 'nosniff',
  };
  if (extension === '.html' || extension === '.svg') {
    headers['content-security-policy'] = "sandbox allow-scripts allow-downloads; default-src 'none'; img-src 'self' data:; style-src 'unsafe-inline'; script-src 'unsafe-inline';";
  }
  return new Response(new Uint8Array(await readFile(target)), { headers });
};
