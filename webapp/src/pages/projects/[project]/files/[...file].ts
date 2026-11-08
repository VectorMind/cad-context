import { readFile } from 'node:fs/promises';
import { extname } from 'node:path';
import type { APIRoute } from 'astro';
import { publishedProject } from '../../../../server/cadcon.ts';
import { portfolioFile } from '../../../../server/portfolio.ts';
export const prerender = false;
export const GET: APIRoute = async ({params}) => {
  let data;
  try { data = await publishedProject(params.project ?? ''); }
  catch { return new Response('Unknown project', {status:404}); }
  const allowed = [
    ...(data.published?.models.map(m => `web/latest/${m.file}`) ?? []),
    ...(data.published?.references?.map(m => `web/latest/${m.file}`) ?? []),
    ...(data.presentation?.stages.flatMap(stage => stage.assets.map(asset => `web/gallery/latest/${asset.file}`)) ?? []),
    'web/gallery/latest/manifest.json',
    'web/latest/manifest.json', 'reference/source.zip', 'reference/source.json',
    ...data.releases.flatMap(r => [`3d-print/${r.date}/release.json`, ...Object.keys(r.files).map(n => `3d-print/${r.date}/${n}`)]),
  ];
  const target = await portfolioFile(data.publication_root, params.file ?? '', allowed);
  if (!target) return new Response('Unknown published file', {status:404});
  const types:Record<string,string> = {'.glb':'model/gltf-binary','.3mf':'model/3mf','.json':'application/json','.zip':'application/zip','.png':'image/png','.svg':'image/svg+xml','.jpg':'image/jpeg','.jpeg':'image/jpeg','.webp':'image/webp'};
  const headers:Record<string,string>={'content-type':types[extname(target)] ?? 'application/octet-stream','cache-control':'no-store','x-content-type-options':'nosniff'};
  if (extname(target)==='.svg') headers['content-security-policy']="sandbox; default-src 'none'; img-src data:; style-src 'unsafe-inline'";
  return new Response(new Uint8Array(await readFile(target)),{headers});
};
