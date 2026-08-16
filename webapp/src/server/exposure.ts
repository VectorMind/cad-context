/**
 * Curated parameter exposure.
 *
 * A generator's parameter model is the full truth (`cadctx schema <id>`), but
 * the API deliberately publishes only a few knobs per generator, listed in
 * `config/exposure.json`. Two reasons: the panel stays a preview-and-tweak
 * surface instead of a form over every field, and `POST /api/generate` accepts
 * a small, checked set of names instead of forwarding whatever the browser
 * sent into a subprocess.
 *
 * No parameter metadata is defined here — only which names are editable. Types,
 * ranges, steps and units are always read from the schema
 * (`specifications/parameter-schema/spec.md`).
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  generatorSchema,
  type GeneratorInfo,
  type GeneratorSchema,
  type ParameterSpec,
} from './cadctx.ts';

export interface GeneratorExposure {
  editable: string[];
  preview?: string;
}

interface ExposureFile {
  generators: Record<string, GeneratorExposure>;
}

const configPath = join(
  dirname(fileURLToPath(import.meta.url)),
  '../../config/exposure.json',
);

/** Read on every call: the file is tiny, and editing it takes effect at once. */
function exposureFile(): ExposureFile {
  try {
    return JSON.parse(readFileSync(configPath, 'utf8')) as ExposureFile;
  } catch {
    return { generators: {} };
  }
}

export function exposureFor(generatorId: string): GeneratorExposure {
  return exposureFile().generators[generatorId] ?? { editable: [] };
}

export function effectiveExposure(
  generator: Pick<GeneratorInfo, 'id' | 'origin' | 'exposure'>,
): GeneratorExposure {
  if (generator.origin === 'project' && generator.exposure) {
    return {
      editable: generator.exposure.editable,
      preview: generator.exposure.preview ?? undefined,
    };
  }
  return exposureFor(generator.id);
}

/** Preview format: the configured one, else GLB for 3D and SVG for 2D. */
export function previewFormat(schema: GeneratorSchema, exposure: GeneratorExposure): string {
  const wanted = exposure.preview ?? (schema.kind === '2d' ? 'svg' : 'glb');
  return schema.formats.includes(wanted) ? wanted : schema.formats[0]!;
}

export interface ExposedSchema {
  generator: string;
  title: string;
  kind: '2d' | '3d';
  backend: string;
  description: string;
  preview: string;
  /** Editable knobs, with their metadata straight from the generator. */
  parameters: ParameterSpec[];
  /** Everything else, shown read-only at its default value. */
  fixed: { name: string; value: unknown; unit: string; description: string }[];
}

export async function exposedSchema(generatorId: string): Promise<ExposedSchema> {
  const schema = await generatorSchema(generatorId);
  const exposure = effectiveExposure({
    id: generatorId,
    origin: schema.origin,
    exposure: schema.exposure,
  });
  const editable = new Set(exposure.editable);
  const known = new Set(schema.parameters.map((p) => p.name));
  for (const name of editable) {
    if (!known.has(name)) {
      throw new Error(
        `config/exposure.json lists unknown parameter "${name}" for ${generatorId}`,
      );
    }
  }
  return {
    generator: schema.generator,
    title: schema.title,
    kind: schema.kind,
    backend: schema.backend,
    description: schema.description,
    preview: previewFormat(schema, exposure),
    parameters: schema.parameters.filter((p) => editable.has(p.name)),
    fixed: schema.parameters
      .filter((p) => !editable.has(p.name))
      .map((p) => ({
        name: p.name,
        value: p.default,
        unit: p.unit,
        description: p.description,
      })),
  };
}

/**
 * Validate a request's parameters against the exposed schema.
 *
 * Rejects unknown or non-exposed names, wrong types and out-of-range values
 * before anything is spawned. Returns only exposed names, so a value that
 * slipped past the panel can never reach the CLI.
 */
export function checkParameters(
  exposed: ExposedSchema,
  params: Record<string, unknown>,
): Record<string, number | string | boolean> {
  const byName = new Map(exposed.parameters.map((p) => [p.name, p]));
  const checked: Record<string, number | string | boolean> = {};
  for (const [name, raw] of Object.entries(params ?? {})) {
    const spec = byName.get(name);
    if (!spec) {
      throw new Error(
        `parameter "${name}" is not editable for ${exposed.generator}` +
          ` (editable: ${exposed.parameters.map((p) => p.name).join(', ') || 'none'})`,
      );
    }
    checked[name] = checkOne(spec, raw);
  }
  return checked;
}

function checkOne(spec: ParameterSpec, raw: unknown): number | string | boolean {
  if (spec.type === 'number' || spec.type === 'integer') {
    const value = typeof raw === 'string' ? Number(raw) : raw;
    if (typeof value !== 'number' || !Number.isFinite(value)) {
      throw new Error(`parameter "${spec.name}" must be a number, got ${JSON.stringify(raw)}`);
    }
    if (spec.type === 'integer' && !Number.isInteger(value)) {
      throw new Error(`parameter "${spec.name}" must be an integer, got ${value}`);
    }
    if (spec.minimum !== null && value < spec.minimum) {
      throw new Error(`parameter "${spec.name}" is below its minimum ${spec.minimum}`);
    }
    if (spec.maximum !== null && value > spec.maximum) {
      throw new Error(`parameter "${spec.name}" is above its maximum ${spec.maximum}`);
    }
    return value;
  }
  if (spec.type === 'boolean') {
    if (typeof raw !== 'boolean') {
      throw new Error(`parameter "${spec.name}" must be a boolean`);
    }
    return raw;
  }
  if (typeof raw !== 'string') {
    throw new Error(`parameter "${spec.name}" must be a string`);
  }
  if (spec.options && !spec.options.includes(raw)) {
    throw new Error(`parameter "${spec.name}" must be one of ${spec.options.join(', ')}`);
  }
  return raw;
}
