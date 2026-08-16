/**
 * The airfoil page: one parameter panel driving two generators at once.
 *
 * The profile parameters belong to both the 2D generator and the 3D loft, so a
 * change is routed to whichever generators actually declare it — dragging
 * `thickness` regenerates the profile *and* the wing, dragging `twist` only the
 * wing. Each generator gets its own scheduler, so the fast 2D redraw is never
 * held up behind a B-rep loft.
 *
 * The loft implementation is discovered from the wing family. The maintained
 * built-in is build123d; the component still tolerates additional project
 * implementations without making a backend a shape parameter. There is
 * no faster approximate path behind it — the app renders real generator output
 * and shows a spinner while that takes its time.
 */
import { folder, Leva, useControls } from 'leva';
import { Suspense, lazy, useEffect, useMemo, useRef, useState } from 'react';

import type { WorkbenchSchema } from './ShapeWorkbench.tsx';
import { useRegeneration } from './useRegeneration.ts';

const ModelView = lazy(() => import('./ModelView.tsx'));
const ProfileView = lazy(() => import('./ProfileView.tsx'));

export interface WingOption {
  /** The backend's own name, used as the selector label. */
  backend: string;
  schema: WorkbenchSchema;
}

export interface AirfoilWorkbenchProps {
  profile: WorkbenchSchema;
  wings: WingOption[];
}

const NUMBER_FORMAT = new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 });

function readable(metrics: Record<string, unknown>): [string, string][] {
  return Object.entries(metrics).flatMap(([key, value]) => {
    if (typeof value === 'number') return [[key, NUMBER_FORMAT.format(value)]];
    if (typeof value === 'string') return [[key, value]];
    return [];
  });
}

export default function AirfoilWorkbench({ profile, wings }: AirfoilWorkbenchProps) {
  const [wingIndex, setWingIndex] = useState(0);
  const wing = wings[wingIndex]?.schema ?? wings[0]?.schema;

  const profileNames = useMemo(
    () => new Set(profile.parameters.map((p) => p.name)),
    [profile],
  );
  const wingNames = useMemo(
    () => new Set((wing?.parameters ?? []).map((p) => p.name)),
    [wing],
  );

  const values = useRef<Record<string, unknown>>(
    Object.fromEntries(
      [...profile.parameters, ...(wing?.parameters ?? [])].map((p) => [p.name, p.default]),
    ),
  );

  const profileLoop = useRegeneration(profile.generator);
  const wingLoop = useRegeneration(wing?.generator ?? profile.generator);

  const [wireframe, setWireframe] = useState(false);
  const [showGrid, setShowGrid] = useState(true);
  const [fitToken, setFitToken] = useState(0);

  // Held in a ref and refreshed every render: leva's transient handlers are
  // registered once, and this keeps them dispatching to the *current*
  // schedulers — which the backend selector replaces mid-session.
  const send = useRef<(changed: string | null) => void>(() => {});
  send.current = (changed: string | null) => {
    const only = (names: Set<string>) =>
      Object.fromEntries(
        Object.entries(values.current).filter(([name]) => names.has(name)),
      );
    if (changed === null || profileNames.has(changed)) {
      profileLoop.request(only(profileNames), changed);
    }
    if (changed === null || wingNames.has(changed)) {
      wingLoop.request(only(wingNames), changed);
    }
  };

  // Controls come from the two schemas, grouped by which shape they describe.
  // Nothing about a range, step or unit is written here.
  const controls = useMemo(() => {
    const entry = (parameter: WorkbenchSchema['parameters'][number]) => {
      const numeric = parameter.type === 'number' || parameter.type === 'integer';
      return {
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
        transient: true,
        onChange: (value: unknown, _path: string, context: { initial: boolean }) => {
          if (context.initial) return;
          values.current[parameter.name] = value;
          send.current(parameter.name);
        },
      };
    };
    const profileEntries = Object.fromEntries(
      profile.parameters.map((p) => [p.name, entry(p)]),
    );
    const wingEntries = Object.fromEntries(
      (wing?.parameters ?? [])
        .filter((p) => !profileNames.has(p.name))
        .map((p) => [p.name, entry(p)]),
    );
    // `as never`: leva's Schema type describes literal control declarations,
    // not a map built at runtime from a generator's schema — same escape hatch
    // ShapeWorkbench takes for `useControls`.
    return {
      profile: folder(profileEntries as never),
      wing: folder(wingEntries as never),
    };
    // Built once: the two schemas are fixed for the life of the page, and the
    // backend selector swaps the target generator, not the parameter set.
  }, [profile, wing, profileNames]);

  useControls(() => controls as never);

  useEffect(() => {
    // Mount, and every backend switch: one request with the current values so
    // the newly selected implementation renders the same shape.
    send.current(null);
  }, [profile.generator, wing?.generator]);

  const profileUrl = profileLoop.state.artifacts[profile.preview] ?? null;
  const wingUrl = wing ? (wingLoop.state.artifacts[wing.preview] ?? null) : null;

  return (
    <div className="workbench">
      <section className="panel">
        <h2>Parameters</h2>
        <p className="panel-note">
          Profile knobs drive both shapes; wing knobs only the loft. Ranges and units come
          from the generators' own schemas.
        </p>
        <div className="leva-host">
          <Leva fill flat titleBar={false} />
        </div>

        <div className="metrics">
          <h3>Profile</h3>
          <dl>
            {readable(profileLoop.state.metrics).map(([key, value]) => (
              <div key={key}>
                <dt>{key}</dt>
                <dd>{value}</dd>
              </div>
            ))}
          </dl>
          <h3>Wing · {wings[wingIndex]?.backend}</h3>
          <dl>
            {readable(wingLoop.state.metrics).map(([key, value]) => (
              <div key={key}>
                <dt>{key}</dt>
                <dd>{value}</dd>
              </div>
            ))}
          </dl>
        </div>

        {profile.fixed.length > 0 && (
          <details className="fixed">
            <summary>fixed ({profile.fixed.length})</summary>
            <dl>
              {profile.fixed.map((parameter) => (
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
      </section>

      <section className="stage stage-split">
        <div className="stage-half">
          <div className="stage-bar">
            <span className={profileLoop.state.busy ? 'badge busy' : 'badge idle'}>
              {profileLoop.state.busy ? 'regenerating…' : 'profile'}
            </span>
            <span className="timing">
              {profileLoop.state.lastMs === null ? '—' : `${profileLoop.state.lastMs} ms`}
            </span>
            <span className="counters">
              {profileLoop.state.stats.dispatched} sent ·{' '}
              {profileLoop.state.stats.coalesced} coalesced ·{' '}
              {profileLoop.state.stats.discarded} stale
            </span>
            <span className="spacer" />
            {profileUrl && (
              <a className="download" href={profileUrl} download>
                {profile.preview}
              </a>
            )}
          </div>
          <Suspense fallback={<div className="viewport" />}>
            <ProfileView url={profileUrl} busy={profileLoop.state.busy} />
          </Suspense>
          {profileLoop.state.error && (
            <p className="error banner">{profileLoop.state.error}</p>
          )}
        </div>

        <div className="stage-half">
          <div className="stage-bar">
            <span className={wingLoop.state.busy ? 'badge busy' : 'badge idle'}>
              {wingLoop.state.busy ? 'lofting…' : 'wing'}
            </span>
            <span className="timing">
              {wingLoop.state.lastMs === null ? '—' : `${wingLoop.state.lastMs} ms`}
              {wingLoop.state.cliMs !== null && ` · ${wingLoop.state.cliMs} ms cadctx`}
            </span>
            {wings.length > 1 && (
              <span className="backends" role="group" aria-label="loft backend">
                {wings.map((option, index) => (
                  <button
                    type="button"
                    key={option.schema.generator}
                    className={index === wingIndex ? 'selected' : ''}
                    onClick={() => setWingIndex(index)}
                  >
                    {option.backend}
                  </button>
                ))}
              </span>
            )}
            <span className="spacer" />
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
            {wingUrl && (
              <a className="download" href={wingUrl} download>
                {wing?.preview}
              </a>
            )}
          </div>
          <div className="stage-canvas">
            <Suspense fallback={<div className="viewport" />}>
              <ModelView
                url={wingUrl}
                format={wing?.preview ?? 'glb'}
                wireframe={wireframe}
                showGrid={showGrid}
                fitToken={fitToken}
              />
            </Suspense>
            {wingLoop.state.busy && (
              <div className="stage-spinner" aria-label="regenerating" />
            )}
          </div>
          {wingLoop.state.error && <p className="error banner">{wingLoop.state.error}</p>}
        </div>
      </section>
    </div>
  );
}
