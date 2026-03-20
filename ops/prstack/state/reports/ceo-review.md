# CEO Review

## Date

2026-03-20

## Product Position

- The sim has a working city-systems sandbox with scenarios, interventions, replay, save/load, and reports.
- The current experience is still a systems demo, not yet a sticky strategy product loop.
- The strongest product angle is "urban strategy lab": compare policy choices, district strategies, and long-horizon tradeoffs.

## What Is Working

- Fast setup through `prstack dev`
- Clear simulation verbs: transit, upzoning, flood barriers
- Scenario-driven structure with event timelines
- Replay and save/load strong enough for experimentation

## Missing To Reach A Real Product

- No explicit win/loss or score model for player decisions
- No side-by-side comparison run for "what changed because of my intervention"
- No budget, political capital, or resource constraints on commands
- No campaign or scenario progression that teaches the system over time
- Long-term world model is still unresolved: district abstraction works, but tile or hybrid detail is still undecided

## Direction

- Keep the district model as the shipping core and defer tile detail until a stronger game loop exists
- Build a comparison panel next: baseline versus current run, delta by district, and intervention ROI
- Add resource constraints so each intervention becomes a tradeoff instead of a free action
- Introduce scenario objectives and failure pressure so reports become decisions, not just telemetry

## Immediate Priorities

- Build baseline-vs-run comparison UX and API output
- Add budget and policy-capital costs to interventions
- Define scenario objectives, success metrics, and end-of-horizon evaluation
- Decide whether district-only remains the production model or becomes a layer over future tiles
