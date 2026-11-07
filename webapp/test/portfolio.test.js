import assert from 'node:assert/strict';
import test from 'node:test';
import { mkdtemp, mkdir, writeFile, symlink, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { portfolioFile } from '../src/server/portfolio.ts';

test('portfolio serves only declared files and confines resolved targets', async (t) => {
  const temp = await mkdtemp(join(tmpdir(), 'cadcon-portfolio-'));
  t.after(() => rm(temp, { recursive: true, force: true }));
  const root = join(temp, 'project');
  await mkdir(root);
  await writeFile(join(root, 'entry.html'), 'portfolio');
  await writeFile(join(temp, 'private.html'), 'private');
  assert.equal(await portfolioFile(root, 'entry.html', ['entry.html']), join(root, 'entry.html'));
  for (const path of ['../private.html', 'missing.svg', 'entry.html', 'a\\b.html']) {
    assert.equal(await portfolioFile(root, path, []), null);
  }
  assert.equal(await portfolioFile(root, '../private.html', ['../private.html']), null);
  try {
    await symlink(join(temp, 'private.html'), join(root, 'escape.html'));
    assert.equal(await portfolioFile(root, 'escape.html', ['escape.html']), null);
  } catch (error) {
    if (error.code !== 'EPERM') throw error;
    t.diagnostic('Symlink creation unavailable; lexical confinement still tested.');
  }
});
