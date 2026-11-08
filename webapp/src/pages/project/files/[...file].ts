import type { APIRoute } from 'astro';
import { projectInfo } from '../../../server/cadcon.ts';
export const prerender = false;
/** Legacy bookmarks now lead to the explicit project page, never its source tree. */
export const GET: APIRoute = async () => {
  const project = await projectInfo().catch(() => null);
  return new Response(null, {status:302, headers:{location:project?.id ? `/projects/${encodeURIComponent(project.id)}` : '/projects'}});
};
