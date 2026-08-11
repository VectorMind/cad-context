/**
 * The one island on a viewer page: parameter panel + preview + status.
 *
 * Controls are rendered from the generator's own schema (names, ranges, steps,
 * units are never restated here), restricted to the knobs `config/exposure.json`
 * exposes. Every change goes through the regeneration scheduler, so the panel
 * cannot outrun the Python side.
 */
import { Leva, useControls } from 'leva';
import { Suspense, lazy, useEffect, useMemo, useRef, useState } from 'react';

import { useRegeneration } from './useRegeneration.ts';

// Split so a 2D page never downloads three.js (and a 3D page never downloads
// the SVG stage). Both are viewport-sized, so the fallback is just the frame.
const ModelView = lazy(() => import('./ModelView.tsx'));
const SvgView = lazy(() => import('./SvgView.tsx'));

export interface ParameterSpec {
  name: string;
  type: 'number' | 'integer' | 'string' | 'boolean';
  default: number | string | boolean;
  minimum: number | null;
  maximum: number | null;
  step: number | null;
  unit: string;
  options: string[] | null;
  control: string;
  description: string;
}

export interface WorkbenchSchema {
  generator: string;
  title: string;
  kind: '2d' | '3d';
  backend: string;
  description: string;
  preview: string;
  parameters: ParameterSpec[];
  fixed: { name: string; value: unknown; unit: string; description: string }[];
}

const NUMBER_FORMAT = new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 });

export default function ShapeWorkbench({ schema }: { schema: WorkbenchSchema }) {
  const { state, request } = useRegeneration(schema.generator);
  const requestRef = useRef(request);
  requestRef.current = request;

  const values = useRef<Record<string, unknown>>(
    Object.fromEntries(schema.parameters.map((p) => [p.name, p.default])),
  );

  const [wireframe, setWireframe] = useState(false);
  const [showGrid, setShowGrid] = useState(true);
  const [fitToken, setFitToken] = useState(0);

  const controls = useMemo(() => {
    const entries: Record<string, unknown> = {};
    for (const parameter of schema.parameters) {
      const numeric = parameter.type === 'number' || parameter.type === 'integer';
      entries[parameter.name] = {
        value: parameter.default,
        label: parameter.unit ? `${parameter.name} (${parameter.unit})` : parameter.name,
        hint: parameter.description,
        ...(numeric
          ? {
              min: parameter.minimum ?? undefined,
              max: parameter.maximum ?? undefined,
              step: parameter.step ?? undefined,
            }
          : {}),
        ...(parameter.options ? { options: parameter.options } : {}),
        // Transient: leva does not re-render the page on every dragged frame;
        // the scheduler decides when a value becomes a generation request.
        transient: true,
        onChange: (value: unknown, _path: string, context: { initial: boolean }) => {
          if (context.initial) return;
          values.current[parameter.name] = value;
          requestRef.current({ ...values.current }, parameter.name);
        },
      };
    }
    return entries;
    // Built once: a page renders exactly one generator.
  }, [schema]);

  useControls(() => controls as never);

  useEffect(() => {
    // First render of the page: one request with the declared defaults.
    requestRef.current({ ...values.current }, null);
  }, [schema.generator]);

  const artifactUrl = state.artifacts[schema.preview] ?? null;
  const scalarMetrics = Object.entries(state.metrics).filter(
    ([, value]) => typeof value === 'number',
  ) as [string, number][];

  return (
    <div className="workbench">
      <section className="panel">
        <h2>Parameters</h2>
        <p className="panel-note">
          {schema.parameters.length} of {schema.parameters.length + schema.fixed.length} parameters
          are exposed; the rest stay at their generator defaults.
        </p>
        <div className="leva-host">
          <Leva fill flat titleBar={false} />
        </div>

        {schema.fixed.length > 0 && (
          <details className="fixed">
            <summary>fixed ({schema.fixed.length})</summary>
            <dl>
              {schema.fixed.map((parameter) => (
                <div key={parameter.name}>
                  <dt title={parameter.description}>{parameter.name}</dt>
                  <dd>
                    {String(parameter.value)} {parameter.unit}
                  </dd>
                </div>
              ))}
            </dl>
          </details>
        )}

        {scalarMetrics.length > 0 && (
          <div className="metrics">
            <h3>Measured</h3>
            <dl>
              {scalarMetrics.map(([key, value]) => (
                <div key={key}>
                  <dt>{key}</dt>
                  <dd>{NUMBER_FORMAT.format(value)}</dd>
                </div>
              ))}
            </dl>
          </div>
        )}
      </section>

      <section className="stage">
        <div className="stage-bar">
          <span className={state.busy ? 'badge busy' : 'badge idle'}>
            {state.busy ? 'regenerating…' : 'idle'}
          </span>
          <span className="timing">
            {state.lastMs === null ? '—' : `${state.lastMs} ms round-trip`}
            {state.cliMs !== null && ` · ${state.cliMs} ms cadctx`}
          </span>
          <span className="counters">
            {state.stats.dispatched} sent · {state.stats.coalesced} coalesced ·{' '}
            {state.stats.discarded} stale
          </span>
          <span className="spacer" />
          {schema.preview !== 'svg' && (
            <>
              <label>
                <input
                  type="checkbox"
                  checked={wireframe}
                  onChange={(event) => setWireframe(event.target.checked)}
                />
                wireframe
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={showGrid}
                  onChange={(event) => setShowGrid(event.target.checked)}
                />
                grid
              </label>
              <button type="button" onClick={() => setFitToken((n) => n + 1)}>
                fit view
              </button>
            </>
          )}
          {artifactUrl && (
            <a className="download" href={artifactUrl} download>
              {schema.preview}
            </a>
          )}
        </div>

        <Suspense fallback={<div className="viewport" />}>
          {schema.preview === 'svg' ? (
            <SvgView url={artifactUrl} />
          ) : (
            <ModelView
              url={artifactUrl}
              format={schema.preview}
              wireframe={wireframe}
              showGrid={showGrid}
              fitToken={fitToken}
            />
          )}
        </Suspense>

        {state.error && <p className="error banner">{state.error}</p>}
        {state.notes.map((note) => (
          <p className="note banner" key={note}>
            {note}
          </p>
        ))}
      </section>
    </div>
  );
}
