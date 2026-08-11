/**
 * Proof for the regeneration contract's client rules, without a browser:
 * one request in flight, latest-wins coalescing, stale responses discarded.
 *
 * Run with `pnpm test` (Node executes the TypeScript source by type stripping).
 */
import assert from 'node:assert/strict';
import test from 'node:test';

import { RegenerationScheduler } from '../src/components/regeneration.ts';

/** A transport whose responses are resolved by the test, one at a time. */
function controllableTransport() {
  const outstanding = [];
  let peak = 0;
  const send = (request) =>
    new Promise((resolve) => {
      outstanding.push({ request, resolve });
      peak = Math.max(peak, outstanding.length);
    });
  return {
    send,
    get peak() {
      return peak;
    },
    get requests() {
      return outstanding.map((entry) => entry.request);
    },
    /** Resolve the oldest outstanding request. */
    async settle(response) {
      const entry = outstanding.shift();
      assert.ok(entry, 'no request in flight to settle');
      entry.resolve({ seq: entry.request.seq, ...response });
      await new Promise((r) => setTimeout(r, 0));
      return entry.request;
    },
  };
}

const tick = () => new Promise((r) => setTimeout(r, 5));

test('a burst of changes costs one request plus one queued latest-value request', async () => {
  const transport = controllableTransport();
  let state;
  const scheduler = new RegenerationScheduler({
    generator: 'plate2d',
    send: transport.send,
    onState: (next) => {
      state = next;
    },
    debounceMs: 1,
  });

  scheduler.request({ width: 120 }, null);
  await tick();
  assert.equal(transport.requests.length, 1, 'first change dispatches');
  assert.equal(transport.requests[0].params.width, 120);

  // Slider drag: four more values while the first request is still running.
  for (const width of [130, 140, 150, 160]) scheduler.request({ width }, 'width');
  await tick();
  assert.equal(transport.requests.length, 1, 'still exactly one request in flight');
  assert.equal(state.stats.coalesced, 3, 'three changes folded into the pending one');

  await transport.settle({ artifacts: { svg: '/a.svg' } });
  await tick();
  assert.equal(transport.requests.length, 1, 'the queued request went out on settle');
  assert.equal(transport.requests[0].params.width, 160, 'it carries the latest value');
  assert.equal(transport.requests[0].changed, 'width', 'the single changed name is forwarded');
  assert.equal(transport.peak, 1, 'never more than one request in flight');

  await transport.settle({ artifacts: { svg: '/b.svg' } });
  await tick();
  assert.equal(state.stats.dispatched, 2, 'five changes produced two generations');
  assert.equal(state.busy, false);
  assert.equal(state.artifacts.svg, '/b.svg');
  scheduler.dispose();
});

test('a response older than the applied one is discarded', async () => {
  const transport = controllableTransport();
  let state;
  const scheduler = new RegenerationScheduler({
    generator: 'plate2d',
    send: transport.send,
    onState: (next) => {
      state = next;
    },
    debounceMs: 1,
  });

  scheduler.request({ width: 120 }, null);
  await tick();
  await transport.settle({ seq: 5, artifacts: { svg: '/fresh.svg' } });
  await tick();
  assert.equal(state.artifacts.svg, '/fresh.svg');

  scheduler.request({ width: 130 }, 'width');
  await tick();
  await transport.settle({ seq: 1, artifacts: { svg: '/stale.svg' } });
  await tick();
  assert.equal(state.stats.discarded, 1, 'the stale response was dropped');
  assert.equal(state.artifacts.svg, '/fresh.svg', 'the fresh render survived');
  scheduler.dispose();
});

test('a transport failure surfaces as an error and does not wedge the queue', async () => {
  const failures = [];
  let state;
  const scheduler = new RegenerationScheduler({
    generator: 'plate2d',
    send: (request) => {
      failures.push(request);
      return Promise.reject(new Error('cadctx exploded'));
    },
    onState: (next) => {
      state = next;
    },
    debounceMs: 1,
  });

  scheduler.request({ width: 120 }, null);
  await tick();
  assert.equal(state.error, 'cadctx exploded');
  assert.equal(state.busy, false);

  scheduler.request({ width: 130 }, 'width');
  await tick();
  assert.equal(failures.length, 2, 'the scheduler still accepts new changes');
  scheduler.dispose();
});
