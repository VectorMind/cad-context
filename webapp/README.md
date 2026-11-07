# cad-context preview app

Astro SSR preview-and-tweak surface for real `cadcon` artifacts. Start it only
through the repository CLI:

```powershell
uv run cadcon web
uv run cadcon --project "C:\models\my-part" web
```

The server snapshots the active project and calls `cadcon --json` per request.
The default launcher is `uv run cadcon`; set `CADCON_COMMAND` to override it
(for example, `cadcon` when it is already on PATH).
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

Do not start the dev server directly for repository workflows; `cadcon web`
owns dependency checks, project propagation, URL reporting, and log routing.
