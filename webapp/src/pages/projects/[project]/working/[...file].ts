import { readFile } from 'node:fs/promises';
import { extname } from 'node:path';
import type { APIRoute } from 'astro';
import { projectInfo } from '../../../../server/cadcon.ts';
import { portfolioFile } from '../../../../server/portfolio.ts';
export const prerender = false;
export const GET: APIRoute = async ({params}) => {
  const project = await projectInfo();
  if (project.id !== params.project || !project.working_root) return new Response('Unknown local project', {status:404});
  const target = await portfolioFile(project.working_root, params.file ?? '', project.working_files ?? []);
  if (!target) return new Response('Unknown local review file', {status:404});
  const types:Record<string,string>={'.svg':'image/svg+xml','.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.json':'application/json','.pdf':'application/pdf'};
  const headers:Record<string,string>={'content-type':types[extname(target)] ?? 'application/octet-stream','cache-control':'no-store','x-content-type-options':'nosniff'};
  if(extname(target)==='.svg') headers['content-security-policy']="sandbox; default-src 'none'; img-src data:; style-src 'unsafe-inline'";
  return new Response(new Uint8Array(await readFile(target)),{headers});
};
