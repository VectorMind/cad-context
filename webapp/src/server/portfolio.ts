import { realpath, stat } from 'node:fs/promises';
import { resolve, sep } from 'node:path';

/** A second realpath check prevents a declared file from following an escaping symlink. */
export async function portfolioFile(root: string, requested: string, allowed: string[]): Promise<string | null> {
  if (!allowed.includes(requested) || requested.includes('\\') || requested.includes(':') ||
      requested.split('/').some((part) => !part || part === '.' || part === '..')) return null;
  try {
    const [base, target] = await Promise.all([realpath(root), realpath(resolve(root, requested))]);
    if (!target.startsWith(base + sep) || !(await stat(target)).isFile()) return null;
    return target;
  } catch {
    return null;
  }
}
