# Orchestration

## Position

The pinned orchestration reference is `github.com/garrytan/gstack`.

After inspecting that repo, the important conclusion is that `gstack` is primarily a Claude Code skill suite with setup scripts and opinionated workflows, not a generic orchestration runtime. For `city_expansion_sim`, the practical path is a Codex-native orchestration layer called `prstack` that borrows the good workflow ideas without inheriting Claude-specific assumptions.

## Why `prstack`

- this repo is being rebuilt from scratch
- the current work is architecture-heavy and iteration-heavy
- the orchestration state needs to stay repo-local and easy to inspect
- agent assumptions should be explicit rather than hidden in external tooling
- `gstack` is optimized around Claude slash-command skills and `.claude/` installation patterns

## Design Goals

`prstack` should help with:

- mission definition
- task decomposition
- status visibility
- persistent notes for ongoing rebuild phases
- handoff between planning, implementation, and verification

It should not attempt to replace version control, issue tracking, or the simulation runtime.

## Initial Scope

Phase 1 `prstack` is intentionally small:

- bootstrap a local mission file
- create a task file
- show current status
- give the repo a standard place for orchestration state

## What To Borrow From `gstack`

The useful ideas to import are:

- explicit work modes instead of one generic assistant mode
- a stable workflow vocabulary for planning, review, QA, and shipping
- repo-local state that makes multi-session work easier to coordinate
- lightweight setup scripts and templates

## What Not To Copy Directly

These parts should stay out unless there is a strong reason:

- Claude-specific slash-command packaging
- `.claude/skills` installation assumptions
- browser and QA flows that depend on Claude-specific integration points
- skill prompts that assume Anthropic tool semantics

## Local Layout

```text
ops/prstack/
└── bin/
    └── prstack   # shim into the standalone prstack repo

.prstack/
├── project.env
└── state/
    ├── mission.md
    └── tasks.md
```

## Codex-First Workflow

Recommended loop:

1. define the current mission in `.prstack/state/mission.md`
2. maintain the active backlog in `.prstack/state/tasks.md`
3. use Codex to execute one slice at a time
4. update task state after each implemented slice
5. keep architecture notes in `docs/`

The command surface inside this repo stays `./ops/prstack/bin/prstack`, but the implementation now lives in the standalone `prstack` repo.

## Next Evolution

If you later provide the exact `gstack` repository, we can compare and selectively import ideas like:

- branch/task conventions
- agent handoff metadata
- PR planning scaffolds
- automation around status summaries

That upstream is now pinned. The next comparison pass should convert the portable ideas into `prstack` subcommands and state files.
