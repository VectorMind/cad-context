/**
 * 2D profile plot: inline SVG drawn from the generator's coordinate payload.
 *
 * The page never computes airfoil geometry. It fetches the `json` artifact the
 * Python generator wrote — outline, camber line, chord line, and the overlay
 * markers — and maps those millimetre coordinates straight into SVG paths. A
 * profile is a couple of hundred points, so SVG costs nothing next to canvas
 * and stays crisp at any zoom, with theming and hit-testing free from the DOM.
 *
 * Coordinates arrive Y-up on the airfoil datum; SVG is Y-down, so the geometry
 * sits in one flipped group and the labels in an unflipped one.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import {
  HOME,
  type Bounds,
  type Point,
  type View,
  panBy,
  pathData,
  plotFrame,
  plotWindow,
  zoomAt,
} from './profile.ts';

export interface ProfileCurve {
  id: string;
  role: string;
  closed: boolean;
  points: Point[];
}

export interface ProfileMarker {
  id: string;
  label: string;
  point?: Point;
  segment?: [Point, Point];
}

export interface ProfilePayload {
  kind: string;
  generator: string;
  units: string;
  designation: string;
  chord: number;
  bounds: Bounds;
  curves: ProfileCurve[];
  markers: ProfileMarker[];
}

export interface ProfileViewProps {
  url: string | null;
  /** Shown as a busy overlay while a regeneration is in flight. */
  busy?: boolean;
}

const TICK_FRACTIONS = [0, 0.25, 0.5, 0.75, 1];
const GRID_FRACTIONS = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9];
const FALLBACK_BOUNDS: Bounds = [0, -10, 100, 10];

export default function ProfileView({ url, busy = false }: ProfileViewProps) {
  const [payload, setPayload] = useState<ProfilePayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<View>(HOME);
  const [size, setSize] = useState({ width: 800, height: 400 });
  const frame = useRef<HTMLDivElement | null>(null);
  const drag = useRef<{ x: number; y: number; view: View } | null>(null);

  useEffect(() => {
    if (!url) return;
    let cancelled = false;
    fetch(url)
      .then((response) => {
        if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
        return response.json() as Promise<ProfilePayload>;
      })
      .then((next) => {
        if (cancelled) return;
        setError(null);
        setPayload(next);
      })
      .catch((cause: unknown) => {
        if (!cancelled) setError(cause instanceof Error ? cause.message : String(cause));
      });
    return () => {
      cancelled = true;
    };
  }, [url]);

  // The viewBox aspect is matched to the element, so there is no letterboxing
  // and one scale factor converts pixels to millimetres everywhere below.
  useEffect(() => {
    const element = frame.current;
    if (!element) return;
    const observer = new ResizeObserver(([entry]) => {
      const box = entry?.contentRect;
      if (box && box.width > 0 && box.height > 0) {
        setSize({ width: box.width, height: box.height });
      }
    });
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  const base = useMemo(
    () => plotFrame(payload?.bounds ?? FALLBACK_BOUNDS, size.width / Math.max(size.height, 1)),
    [payload, size],
  );
  const plot = useMemo(
    () => plotWindow(base, view, size.width),
    [base, view, size],
  );

  const onWheel = useCallback(
    (event: WheelEvent) => {
      event.preventDefault();
      const element = frame.current;
      if (!element) return;
      const box = element.getBoundingClientRect();
      const px = event.clientX - box.left;
      const py = event.clientY - box.top;
      setView((current) => zoomAt(base, current, size.width, px, py, event.deltaY));
    },
    [base, size],
  );

  // React attaches onWheel passively at the root, where preventDefault is a
  // no-op, so the zoom listener is registered natively instead.
  useEffect(() => {
    const element = frame.current;
    if (!element) return;
    element.addEventListener('wheel', onWheel, { passive: false });
    return () => element.removeEventListener('wheel', onWheel);
  }, [onWheel]);

  const onPointerDown = useCallback((event: React.PointerEvent<HTMLDivElement>) => {
    (event.target as Element).setPointerCapture?.(event.pointerId);
    setView((current) => {
      drag.current = { x: event.clientX, y: event.clientY, view: current };
      return current;
    });
  }, []);

  const onPointerMove = useCallback(
    (event: React.PointerEvent<HTMLDivElement>) => {
      const start = drag.current;
      if (!start) return;
      setView(
        panBy(
          base,
          start.view,
          plot.pixelsPerMm,
          event.clientX - start.x,
          event.clientY - start.y,
        ),
      );
    },
    [base, plot],
  );

  const endDrag = useCallback(() => {
    drag.current = null;
  }, []);

  const chord = payload?.chord ?? 100;
  const fontSize = plot.width / 55;
  const tickLength = plot.height / 45;

  return (
    <div className="viewport profile">
      <div
        className="profile-frame"
        ref={frame}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={endDrag}
        onPointerLeave={endDrag}
        onDoubleClick={() => setView(HOME)}
      >
        {payload && (
          <svg
            className="profile-plot"
            viewBox={plot.viewBox}
            preserveAspectRatio="none"
            role="img"
            aria-label={`${payload.designation} profile`}
          >
            <g transform="scale(1,-1)">
              <g className="profile-grid">
                {GRID_FRACTIONS.map((fraction) => (
                  <line
                    key={fraction}
                    x1={fraction * chord}
                    x2={fraction * chord}
                    y1={plot.centerY - plot.height / 2}
                    y2={plot.centerY + plot.height / 2}
                    vectorEffect="non-scaling-stroke"
                  />
                ))}
              </g>
              <g className="profile-axis">
                {TICK_FRACTIONS.map((fraction) => (
                  <line
                    key={fraction}
                    x1={fraction * chord}
                    x2={fraction * chord}
                    y1={-tickLength}
                    y2={tickLength}
                    vectorEffect="non-scaling-stroke"
                  />
                ))}
              </g>
              {payload.curves.map((curve) => (
                <path
                  key={curve.id}
                  className={`profile-curve ${curve.id}`}
                  d={pathData(curve.points, curve.closed)}
                  vectorEffect="non-scaling-stroke"
                />
              ))}
              {payload.markers.map((marker) =>
                marker.segment ? (
                  <line
                    key={marker.id}
                    className={`profile-marker ${marker.id}`}
                    x1={marker.segment[0][0]}
                    y1={marker.segment[0][1]}
                    x2={marker.segment[1][0]}
                    y2={marker.segment[1][1]}
                    vectorEffect="non-scaling-stroke"
                  />
                ) : marker.point ? (
                  <circle
                    key={marker.id}
                    className={`profile-marker ${marker.id}`}
                    cx={marker.point[0]}
                    cy={marker.point[1]}
                    r={plot.width / 220}
                    vectorEffect="non-scaling-stroke"
                  />
                ) : null,
              )}
            </g>
            <g className="profile-labels" fontSize={fontSize}>
              {TICK_FRACTIONS.map((fraction) => (
                <text
                  key={fraction}
                  x={fraction * chord}
                  y={tickLength * 2.6}
                  textAnchor="middle"
                >
                  {`${fraction * 100}%`}
                </text>
              ))}
            </g>
          </svg>
        )}
        {busy && <div className="stage-spinner" aria-label="regenerating" />}
      </div>

      <div className="viewport-toolbar">
        {payload && (
          <>
            <span className="designation">{payload.designation}</span>
            <span className="legend">
              <i className="swatch outline" /> surface
            </span>
            <span className="legend">
              <i className="swatch camber" /> camber line
            </span>
            {payload.markers.map((marker) => (
              <span className="legend" key={marker.id}>
                <i className={`swatch ${marker.id}`} /> {marker.label}
              </span>
            ))}
            <span className="hint">chord {payload.chord} {payload.units}</span>
          </>
        )}
        <span className="spacer" />
        <button type="button" onClick={() => setView(HOME)}>
          reset view
        </button>
        <span className="hint">drag to pan · wheel to zoom</span>
      </div>

      {!payload && !error && <p className="viewport-note">waiting for coordinates…</p>}
      {error && <p className="viewport-note error">{error}</p>}
    </div>
  );
}
