# gstack Adaptation Notes

## Upstream

- Repo: `https://github.com/garrytan/gstack`

## What `gstack` Is

From inspection, `gstack` is:

- a collection of Claude Code skills
- setup scripts for installing those skills into `.claude/`
- an opinionated workflow layer for planning, review, QA, shipping, and browser tasks

It is not primarily:

- a simulation framework
- a project runtime
- a portable orchestration daemon

## Relevant Upstream Pieces

The repo shape strongly suggests a workflow operating system:

- `plan-*` skills for planning modes
- `review/`, `qa/`, and `ship/` for execution and verification modes
- `browse/` and setup scripts for browser-assisted QA
- templates and scripts for skill generation and validation

## Adaptation Decision

For `city_expansion_sim`, the best move is:

- keep `prstack` as the local orchestration surface
- use `gstack` as a workflow reference
- translate good concepts into Codex-friendly commands and docs

## Proposed `prstack` Roadmap

### Near term

- add `prstack plan`
- add `prstack review`
- add `prstack qa`
- add `prstack ship`
- add structured state files for active slice, risks, and verification notes

### Medium term

- add branch naming helpers
- add session notes and handoff summaries
- add generated markdown templates for implementation slices
- add simple release and verification checklists

## Why Not Vendor `gstack` Directly

- it is designed around Claude Code conventions
- this repo is being driven by Codex
- direct vendoring would add workflow surface area that is not executable in this environment
- the concepts are more reusable than the implementation
