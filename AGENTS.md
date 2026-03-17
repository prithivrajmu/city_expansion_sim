# AGENTS

## Project

`city_expansion_sim` is a simulation product with:

- Flask backend in `backend/`
- Vue/Vite frontend in `frontend/`
- simulation runtime in `simulation/`
- workflow stack in `ops/prstack/`
- optional Ralph loop in `.agents/ralph/`

## Normal Workflow

Prefer `prstack` as the operating surface:

```bash
./ops/prstack/bin/prstack review
./ops/prstack/bin/prstack qa
./ops/prstack/bin/prstack dev
./ops/prstack/bin/prstack loop 1 --no-commit
```

## Verification

Use these gates unless the selected story clearly does not require all of them:

- `./ops/prstack/bin/prstack review`
- `./ops/prstack/bin/prstack qa`

If frontend files changed, also ensure:

- `cd frontend && npm run build`

If backend or simulation files changed, ensure:

- `cd backend && uv run --with pytest pytest -q`

## Guardrails

- Do not rewrite legacy files in `legacy/` unless the story explicitly calls for it.
- Prefer changes in active runtime paths: `backend/`, `frontend/`, `simulation/`, `shared/`, `ops/prstack/`.
- Keep `prstack` as the main workflow layer. Ralph is an execution loop within that layer, not a replacement for it.
- Do not run unbounded loops. Use bounded Ralph iterations only.
