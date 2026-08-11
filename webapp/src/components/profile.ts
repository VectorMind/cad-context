/**
 * The profile plot's coordinate math, kept framework-free so a test can drive
 * it without a browser.
 *
 * Two frames are in play. Payload coordinates are millimetres, Y **up**, on the
 * airfoil's datum. SVG user space is Y **down**, so the geometry is drawn
 * inside a `scale(1,-1)` group and only the viewBox has to know about the flip.
 *
 * The view is stored as a zoom factor plus a pan expressed in *fractions of the
 * payload's own extent*, not in millimetres: dragging the chord slider then
 * reframes the plot around the new size while keeping how far in the user had
 * zoomed. Storing millimetres would send the profile off-screen instead.
 */

export type Point = [number, number];
export type Bounds = [number, number, number, number];

export interface View {
  zoom: number;
  panX: number;
  panY: number;
}

export const HOME: View = { zoom: 1, panX: 0, panY: 0 };

export const MIN_ZOOM = 0.3;
export const MAX_ZOOM = 80;

/** Fraction of the content added around it before anything is zoomed. */
const PAD_X = 0.08;
const PAD_Y = 0.45;

export interface Frame {
  /** The viewBox extent at zoom 1, already matched to the element's aspect. */
  width: number;
  height: number;
  centerX: number;
  centerY: number;
  /** The padded content extent — the unit pan is measured in. */
  extentX: number;
  extentY: number;
}

export interface PlotWindow {
  width: number;
  height: number;
  centerX: number;
  centerY: number;
  viewBox: string;
  /** One scale factor for the whole plot: there is no letterboxing. */
  pixelsPerMm: number;
}

export function pathData(points: Point[], closed: boolean): string {
  if (points.length === 0) return '';
  const [head, ...tail] = points;
  const body = tail.map(([x, y]) => `L ${x} ${y}`).join(' ');
  return `M ${head![0]} ${head![1]}${body ? ` ${body}` : ''}${closed ? ' Z' : ''}`;
}

/**
 * The zoom-1 frame around `bounds`, grown on its shorter axis until it matches
 * the element's aspect ratio. Matching here is what lets the SVG use
 * `preserveAspectRatio="none"` without distorting the profile — and what makes
 * a single pixels-per-millimetre factor valid for pan and zoom alike.
 */
export function plotFrame(bounds: Bounds, aspect: number): Frame {
  const [minx, miny, maxx, maxy] = bounds;
  const contentWidth = Math.max(maxx - minx, 1e-6);
  const contentHeight = Math.max(maxy - miny, 1e-6);
  const extentX = contentWidth * (1 + 2 * PAD_X);
  const extentY = contentHeight + 2 * Math.max(contentHeight * PAD_Y, contentWidth * 0.04);
  const safeAspect = aspect > 0 && Number.isFinite(aspect) ? aspect : 1;
  const fitted =
    extentX / extentY > safeAspect
      ? { width: extentX, height: extentX / safeAspect }
      : { width: extentY * safeAspect, height: extentY };
  return {
    ...fitted,
    centerX: (minx + maxx) / 2,
    centerY: (miny + maxy) / 2,
    extentX,
    extentY,
  };
}

export function plotWindow(frame: Frame, view: View, pixelWidth: number): PlotWindow {
  const width = frame.width / view.zoom;
  const height = frame.height / view.zoom;
  const centerX = frame.centerX + view.panX * frame.extentX;
  const centerY = frame.centerY + view.panY * frame.extentY;
  return {
    width,
    height,
    centerX,
    centerY,
    viewBox: `${centerX - width / 2} ${-(centerY + height / 2)} ${width} ${height}`,
    pixelsPerMm: pixelWidth / width,
  };
}

/** Drag: the millimetre under the pointer follows it exactly. */
export function panBy(frame: Frame, view: View, pixelsPerMm: number, dx: number, dy: number): View {
  return {
    zoom: view.zoom,
    panX: view.panX - dx / pixelsPerMm / frame.extentX,
    // +dy: screen Y grows downward while data Y grows upward, and the viewBox
    // is expressed in the flipped frame, so the two negations cancel.
    panY: view.panY + dy / pixelsPerMm / frame.extentY,
  };
}

/** Wheel: scale about the pointer, leaving the millimetre under it pinned. */
export function zoomAt(
  frame: Frame,
  view: View,
  pixelWidth: number,
  px: number,
  py: number,
  deltaY: number,
): View {
  const zoom = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, view.zoom * Math.exp(-deltaY * 0.0015)));
  const before = plotWindow(frame, view, pixelWidth);
  const anchorX = before.centerX - before.width / 2 + px / before.pixelsPerMm;
  const anchorY = before.centerY + before.height / 2 - py / before.pixelsPerMm;
  const after = plotWindow(frame, { ...view, zoom }, pixelWidth);
  const centerX = anchorX - px / after.pixelsPerMm + after.width / 2;
  const centerY = anchorY + py / after.pixelsPerMm - after.height / 2;
  return {
    zoom,
    panX: (centerX - frame.centerX) / frame.extentX,
    panY: (centerY - frame.centerY) / frame.extentY,
  };
}
