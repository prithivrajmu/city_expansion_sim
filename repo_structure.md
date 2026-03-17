# Repo Structure

```text
city_expansion_sim/
├── backend/
│   ├── app/
│   └── tests/
├── docs/
│   ├── architecture.md
│   └── rebuild_plan.md
├── frontend/
│   ├── public/
│   └── src/
├── legacy/
│   ├── chennai_abm_ca_hybrid.py
│   ├── chennai_expansion_model.py
│   ├── flask_backend_server.py
│   └── urban_sim_frontend.jsx
├── shared/
├── simulation/
│   ├── calibration/
│   ├── core/
│   └── scenarios/
├── .dockerignore
├── docker-compose.yml
├── TODO.md
└── readme.md
```

## Notes

- `legacy/` preserves the old prototype and should not be treated as the active architecture.
- `simulation/` is now the center of the rebuild.
- `backend/` and `frontend/` are intentionally empty scaffolds at this stage.
- top-level deployment files have been reset to planning placeholders until the runtime stack is chosen.
