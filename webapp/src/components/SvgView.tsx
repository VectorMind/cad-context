/**
 * 2D preview: the generated SVG inlined, with pan and zoom.
 *
 * The markup comes from this repository's own export layer over a same-origin
 * endpoint, so it is inlined rather than framed — that keeps it styleable and
 * measurable. Pan/zoom is a plain CSS transform; no dependency earns its place
 * for one drag handler and one wheel handler.
 */
import { useCallback, useEffect, useRef, useState } from 'react';

export interface SvgViewProps {
  url: string | null;
}

interface View {
  x: number;
  y: number;
  scale: number;
}

const IDENTITY: View = { x: 0, y: 0, scale: 1 };

export default function SvgView({ url }: SvgViewProps) {
  const [markup, setMarkup] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<View>(IDENTITY);
  const frame = useRef<HTMLDivElement | null>(null);
  const drag = useRef<{ x: number; y: number; view: View } | null>(null);

  useEffect(() => {
    if (!url) return;
    let cancelled = false;
    fetch(url)
      .then((response) => {
        if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
        return response.text();
      })
      .then((text) => {
        if (cancelled) return;
        setError(null);
        setMarkup(text);
      })
      .catch((cause: unknown) => {
        if (!cancelled) setError(cause instanceof Error ? cause.message : String(cause));
      });
    return () => {
      cancelled = true;
    };
  }, [url]);

  // React registers `onWheel` passively at the root, where preventDefault is a
  // no-op, so the zoom listener is attached natively instead.
  useEffect(() => {
    const element = frame.current;
    if (!element) return;
    const onWheel = (event: WheelEvent) => {
      event.preventDefault();
      const box = element.getBoundingClientRect();
      const px = event.clientX - box.left;
      const py = event.clientY - box.top;
      setView((current) => {
        const factor = Math.exp(-event.deltaY * 0.0015);
        const scale = Math.min(40, Math.max(0.1, current.scale * factor));
        const ratio = scale / current.scale;
        // Keep the point under the cursor fixed while zooming.
        return { scale, x: px - (px - current.x) * ratio, y: py - (py - current.y) * ratio };
      });
    };
    element.addEventListener('wheel', onWheel, { passive: false });
    return () => element.removeEventListener('wheel', onWheel);
  }, []);

  const onPointerDown = useCallback((event: React.PointerEvent<HTMLDivElement>) => {
    (event.target as Element).setPointerCapture?.(event.pointerId);
    setView((current) => {
      drag.current = { x: event.clientX, y: event.clientY, view: current };
      return current;
    });
  }, []);

  const onPointerMove = useCallback((event: React.PointerEvent<HTMLDivElement>) => {
    const start = drag.current;
    if (!start) return;
    setView({
      scale: start.view.scale,
      x: start.view.x + (event.clientX - start.x),
      y: start.view.y + (event.clientY - start.y),
    });
  }, []);

  const endDrag = useCallback(() => {
    drag.current = null;
  }, []);

  return (
    <div className="viewport">
      <div
        className="svg-frame"
        ref={frame}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={endDrag}
        onPointerLeave={endDrag}
        onDoubleClick={() => setView(IDENTITY)}
      >
        {markup && (
          <div
            className="svg-stage"
            style={{
              transform: `translate(${view.x}px, ${view.y}px) scale(${view.scale})`,
            }}
            // Same-origin markup produced by this repository's SVG exporter.
            dangerouslySetInnerHTML={{ __html: markup }}
          />
        )}
      </div>
      <div className="viewport-toolbar">
        <button type="button" onClick={() => setView(IDENTITY)}>
          reset view
        </button>
        <span className="hint">drag to pan · wheel to zoom · double-click to reset</span>
      </div>
      {!markup && !error && <p className="viewport-note">waiting for geometry…</p>}
      {error && <p className="viewport-note error">{error}</p>}
    </div>
  );
}
