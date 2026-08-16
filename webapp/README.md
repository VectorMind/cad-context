# cad-context preview app

Astro SSR preview-and-tweak surface for real `cadctx` artifacts. Start it only
through the repository CLI:

```powershell
uv run cadctx web
uv run cadctx --project "C:\models\my-part" web
```

The server snapshots the active project and calls `cadctx --json` per request.
It owns no geometry, parameter ranges, defaults, or output paths. Built-in
editable names live in `config/exposure.json`; project exposure comes through
the CLI from `project.yaml`.

Key routes:

- `/api/generators.json` — merged registry and editable names;
- `/api/schema/<generator>.json` — exposed schema;
- `POST /api/generate` — validated regeneration;
- `/api/artifact/<generator>/<file>` — confined artifact streaming;
- `/viewer/<generator>` — generic generator workbench;
- `/airfoil` — coordinated profile and maintained build123d wing preview.

Development checks:

```powershell
corepack pnpm check
corepack pnpm test
corepack pnpm build
```

Do not start the dev server directly for repository workflows; `cadctx web`
owns dependency checks, project propagation, URL reporting, and log routing.
