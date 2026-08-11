/**
 * Proof for the profile plot's coordinate math, without a browser.
 *
 * The plot draws generator coordinates directly, so the only thing between the
 * payload and the pixels is this framing math: the Y flip, the aspect match
 * that lets the SVG scale without distorting the profile, and the pan/zoom
 * anchoring. Each is checked against what a user would observe.
 *
 * Run with `pnpm test` (Node executes the TypeScript source by type stripping).
 */
import assert from 'node:assert/strict';
import test from 'node:test';

import { HOME, panBy, pathData, plotFrame, plotWindow, zoomAt } from '../src/components/profile.ts';

/** A 120 mm chord NACA 2412 has roughly this extent. */
const BOUNDS = [0, -5.08, 120, 9.5];
const PIXELS = 900;
const ASPECT = 900 / 300;

const viewBoxNumbers = (view) => view.viewBox.split(' ').map(Number);

test('a closed curve becomes one move, lines, and a Z', () => {
  assert.equal(pathData([[0, 0], [1, 2], [3, 4]], true), 'M 0 0 L 1 2 L 3 4 Z');
  assert.equal(pathData([[0, 0], [1, 2]], false), 'M 0 0 L 1 2');
  assert.equal(pathData([], true), '', 'an empty curve draws nothing');
});

test('the zoom-1 frame matches the element aspect so the profile is not distorted', () => {
  const frame = plotFrame(BOUNDS, ASPECT);
  assert.ok(
    Math.abs(frame.width / frame.height - ASPECT) < 1e-9,
    'frame aspect must equal the element aspect',
  );
  // An airfoil is far wider than it is tall, so the frame grows vertically.
  assert.ok(frame.height > BOUNDS[3] - BOUNDS[1]);
  assert.ok(frame.width >= frame.extentX);
});

test('the viewBox flips Y and contains the whole profile at zoom 1', () => {
  const frame = plotFrame(BOUNDS, ASPECT);
  const plot = plotWindow(frame, HOME, PIXELS);
  const [x, y, width, height] = viewBoxNumbers(plot);
  assert.ok(x < BOUNDS[0] && x + width > BOUNDS[2], 'profile fits horizontally');
  // Geometry is drawn inside scale(1,-1), so data y maps to -y on screen.
  assert.ok(y < -BOUNDS[3], 'the top of the profile is inside the box');
  assert.ok(y + height > -BOUNDS[1], 'the bottom of the profile is inside the box');
});

test('dragging moves the plot by exactly the dragged distance', () => {
  const frame = plotFrame(BOUNDS, ASPECT);
  const before = plotWindow(frame, HOME, PIXELS);
  const dragged = panBy(frame, HOME, before.pixelsPerMm, 90, -30);
  const after = plotWindow(frame, dragged, PIXELS);

  // Content follows the pointer: a point drawn at pixel p is now at p + drag.
  const millimetres = (view, pixel) => view.centerX - view.width / 2 + pixel / view.pixelsPerMm;
  assert.ok(Math.abs(millimetres(before, 0) - millimetres(after, 90)) < 1e-9);
  // Screen Y is inverted relative to data Y.
  const heights = (view, pixel) => view.centerY + view.height / 2 - pixel / view.pixelsPerMm;
  assert.ok(Math.abs(heights(before, 0) - heights(after, -30)) < 1e-9);
  assert.equal(after.width, before.width, 'panning does not change the scale');
});

test('the wheel scales about the pointer, pinning the millimetre under it', () => {
  const frame = plotFrame(BOUNDS, ASPECT);
  const px = 300;
  const py = 120;
  const pinned = (view) => [
    view.centerX - view.width / 2 + px / view.pixelsPerMm,
    view.centerY + view.height / 2 - py / view.pixelsPerMm,
  ];

  const before = plotWindow(frame, HOME, PIXELS);
  const zoomed = zoomAt(frame, HOME, PIXELS, px, py, -240);
  const after = plotWindow(frame, zoomed, PIXELS);

  assert.ok(zoomed.zoom > 1, 'scrolling up zooms in');
  const [x0, y0] = pinned(before);
  const [x1, y1] = pinned(after);
  assert.ok(Math.abs(x0 - x1) < 1e-9, 'the millimetre under the cursor stays put');
  assert.ok(Math.abs(y0 - y1) < 1e-9);

  // And back out again returns to where it started.
  const back = zoomAt(frame, zoomed, PIXELS, px, py, 240);
  assert.ok(Math.abs(back.zoom - 1) < 1e-9);
  assert.ok(Math.abs(back.panX) < 1e-9 && Math.abs(back.panY) < 1e-9);
});

test('zoom is clamped so the plot cannot be lost', () => {
  const frame = plotFrame(BOUNDS, ASPECT);
  let view = HOME;
  for (let i = 0; i < 200; i += 1) view = zoomAt(frame, view, PIXELS, 0, 0, -500);
  assert.equal(view.zoom, 80);
  for (let i = 0; i < 400; i += 1) view = zoomAt(frame, view, PIXELS, 0, 0, 500);
  assert.equal(view.zoom, 0.3);
});

test('a longer chord reframes the plot while keeping the zoom', () => {
  const zoomedIn = { zoom: 4, panX: 0, panY: 0 };
  const short = plotWindow(plotFrame(BOUNDS, ASPECT), zoomedIn, PIXELS);
  const long = plotWindow(plotFrame([0, -21, 500, 39], ASPECT), zoomedIn, PIXELS);
  assert.ok(long.width > short.width, 'the window grows with the profile');
  assert.ok(Math.abs(long.centerX - 250) < 1e-9, 'and stays centred on it');
});
