# TODO

## Immediate

- [x] Rename project to `city_expansion_sim`
- [x] Move Chennai-specific prototype files into `legacy/`
- [x] Replace scaffold documentation with rebuild documents
- [x] Pin orchestration reference repo: `github.com/garrytan/gstack`
- [x] Pin architecture reference repo: `github.com/volcengine/OpenViking`
- [x] Pin simulation reference repo: `github.com/666ghj/MiroFish`
- [x] Decide which `gstack` ideas belong in `prstack` and which do not

## Architecture

- [x] Choose the runtime stack for backend and frontend
- [x] Define shared simulation state and command schemas
- [x] Decide whether the world model is tile-based, district-based, or hybrid
- [x] Define turn/tick progression and save/load format
- [x] Map `MiroFish` concepts into a city-expansion domain model

## Backend

- [x] Create session lifecycle API
- [x] Add scenario catalog endpoints
- [x] Add campaign catalog and stage progression endpoints
- [x] Add scenario detail and validation endpoints for authoring
- [x] Add tick advancement endpoint
- [x] Add metrics and event log endpoints
- [x] Add command and report endpoints
- [x] Add save/load and replay endpoints

## Frontend

- [x] Build map or board viewport
- [x] Build scenario setup flow
- [x] Build campaign setup and progression flow
- [x] Build scenario dossier and authoring validation view
- [x] Build timeline and control panel
- [x] Build overlays for growth, price, and population pressure
- [x] Build intervention and report panels
- [x] Build saved-session and replay timeline controls

## Simulation

- [x] Define base world state
- [x] Implement first deterministic tick loop
- [x] Add infrastructure influence model
- [x] Add land value and housing pressure model
- [ ] Reintroduce Chennai as a scenario rather than a hardcoded app target
- [x] Add a second scenario for cross-scenario verification
- [x] Add session persistence and replay history
