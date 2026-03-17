# Context Engineering Reference

## Project Shape

- `backend/` exposes simulation sessions, commands, reports, replay, and persistence
- `frontend/` is the simulation console
- `simulation/` holds the runtime engine and scenario data
- `ops/prstack/` is the operating workflow layer
- `.agents/ralph/` is the bounded autonomous loop layer used through prstack

## Working Rules

- prefer one self-contained story per Ralph iteration
- keep changes in active runtime paths, not `legacy/`
- preserve the current visual style unless the story explicitly changes it
- route all final verification through `prstack review` and `prstack qa`
