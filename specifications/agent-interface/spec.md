# Agent And Human Interface

How every capability of this repository is reached. The rule is one interface,
documented in plain files, usable by a person and by an agent without any
special integration.

## The CLI Is The Interface

`cadctx` is the single documented entry point for humans and agents alike.

- Every capability is a `cadctx` subcommand. A capability that is not reachable
  through a documented command is not delivered.
- Every command is documented in `README.md` with a usage line and a runnable
  example, sufficient to drive the repository from documentation alone.
- Commands are non-interactive: no prompts, no TTY assumptions. Options carry
  defaults that make the bare command useful.
- Every command reports through the result-file contract in
  `specifications/workspace-layout/spec.md`, so its outcome is inspectable
  after the fact without re-running it.

## No Skills, No Bespoke Integrations

Routing lives in documentation, not in packaged agent skills, plugins, or
tool-specific manifests:

- `README.md` — the human entry point and the command reference.
- `AGENTS.md` — the agent entry point: rules, surfaces, and worked recipes.
- `WORKFLOW.md` — the spec/plan workflow.

Any agent that can read files and run commands is fully equipped. Adding a
capability means adding a command plus its documentation in the same pass.

## The Python API Is The Second Surface

Agents and scripts may bypass the CLI and call `cad_context.api` directly —
this is expected for exploration, measurement and one-off experiments:

- The API returns data and live kernel objects. It writes no files, prints
  nothing, and touches no workspace directory.
- Anything the API can do about a shape, the CLI can do too; the API adds
  direct access to backend-native objects, not extra capability.
- Throwaway scripts belong in `.cache/scratch/`.
- When a script needs artifacts on disk, it calls the export layer explicitly
  or runs the CLI. Writing files is never a side effect of asking a question.

## Machine-Readable Discovery

An agent discovers the repository at runtime, without reading source:

- `cadctx generators` — what can be generated, on which backend, in which
  formats, and whether that backend is installed.
- `cadctx schema <generator>` — the parameter contract for one generator.
- `cadctx info` — backend and external-binary availability.
- `cadctx paths` — the workspace layout and the fixed artifact paths.

Each of these writes a result file whose `data` object is the machine-readable
form of the answer.
