# City Expansion Sim

`city_expansion_sim` is a reset of the earlier Chennai-specific prototype into a broader city-growth simulation platform.

The goal remains the same: model and visualize how a city expands under infrastructure, land value, policy, environmental risk, and population pressure. The difference is architectural: this rebuild is being reorganized around a game/simulation-oriented structure inspired by the external repos you named, rather than the previous one-off script scaffold.

## Current Status

This repository is now in rebuild mode.

- `legacy/` contains the original prototype files for reference only.
- `simulation/` will own the simulation engine, scenario definitions, and calibration logic.
- `backend/` will expose simulation state, runs, saves, and analytics APIs.
- `frontend/` will become the main simulation client and map or board interface.
- `shared/` is reserved for schemas and cross-layer contracts.

## Direction

The intended rebuild target is:

- more like a simulation product than a notebook export
- city-agnostic rather than Chennai-hardcoded
- driven by explicit scenario data and simulation rules
- structured so gameplay-style iteration and long-running simulation are possible

## Important Constraint

The local workspace did not contain copies of the referenced inspiration repos.

Pinned upstream references so far:

- orchestration reference: `github.com/garrytan/gstack`
- architecture reference: `github.com/volcengine/OpenViking`
- simulation reference: `github.com/666ghj/MiroFish`

These references serve different purposes:

- `gstack` informs workflow orchestration
- `OpenViking` informs context and project structure
- `MiroFish` informs simulation architecture, agent/world concepts, and interactive prediction flows

## Documents

- `docs/architecture.md` explains the target system shape
- `docs/rebuild_plan.md` breaks the revamp into phases
- `repo_structure.md` describes the new folder layout
- `TODO.md` tracks the immediate rebuild backlog

## First Vertical Slice

The repo now includes a runnable vertical slice:

- Flask backend session API on `http://localhost:5001`
- Vue/Vite frontend on `http://localhost:3000`
- deterministic city-growth simulation with scenario seeding
- district intervention commands, constrained by budget and political capital
- baseline-vs-run comparison views and intervention ROI reporting
- multiple scenarios for cross-scenario runs
- saved sessions and replayable timeline history
- `prstack` as the intended bootstrap and dev entrypoint

Run it with:

```bash
./ops/prstack/bin/prstack dev
```

Use the workflow stack with:

```bash
./ops/prstack/bin/prstack plan "Intervention Slice"
./ops/prstack/bin/prstack ceo-review
./ops/prstack/bin/prstack security-review
./ops/prstack/bin/prstack review
./ops/prstack/bin/prstack qa
./ops/prstack/bin/prstack ship
./ops/prstack/bin/prstack handoff
```
