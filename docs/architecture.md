# Architecture

## Goal

Build a city expansion simulator that feels closer to a simulation or strategy platform than a static geospatial demo.

The product should support:

- city-scale expansion over time
- policy, infrastructure, and market-driven change
- agent and system interactions
- saved scenarios and replayable runs
- a visual map or board-first client

## Architectural Reset

The previous prototype mixed together:

- hardcoded Chennai assumptions
- one-off model training scripts
- UI code in the wrong backend location
- docs that described files that did not exist

That is not a useful foundation for a serious rebuild.

The new architecture should separate:

1. scenario data
2. simulation engine
3. backend orchestration
4. frontend presentation
5. shared schemas

## Target Shape

### 1. Simulation Core

`simulation/core/`

Responsibilities:

- world state
- tile or region graph representation
- time stepping
- policy and infrastructure effects
- land-use transition rules
- economic signals
- population and migration dynamics

This layer should be framework-light and deterministic where possible.

### 2. Scenarios

`simulation/scenarios/`

Responsibilities:

- city presets
- terrain, districts, infrastructure, and zoning inputs
- parameter bundles
- scripted events or interventions

This is where Chennai can later return as one scenario among many, not as the architecture itself.

### 3. Calibration and Data Preparation

`simulation/calibration/`

Responsibilities:

- ingest historical GIS and tabular data
- normalize rasters and vector features
- fit or validate model parameters
- export scenario-ready assets

Training or calibration code belongs here, not inside the runtime engine.

### 4. Backend

`backend/app/`

Responsibilities:

- create and load simulation sessions
- advance simulation ticks or turns
- expose snapshots and metrics
- save and restore runs
- serve scenario catalogs

Suggested API surfaces:

- `GET /health`
- `GET /scenarios`
- `POST /sessions`
- `GET /sessions/:id/state`
- `POST /sessions/:id/tick`
- `POST /sessions/:id/commands`
- `GET /sessions/:id/metrics`

### 5. Frontend

`frontend/src/`

Responsibilities:

- map or board rendering
- overlays and filters
- time controls
- scenario setup
- inspector panels
- metrics, trend charts, and event logs

The UI should be built around simulation state, not around fetching raw `.npy` files.

### 6. Shared Contracts

`shared/`

Responsibilities:

- scenario schema
- simulation snapshot schema
- command payload definitions
- metric and event types

This prevents backend and frontend drift.

## Inspiration Mapping

Your requested direction is to rebuild around `MiroFish` and `OpenViking`.

Pinned references:

- `https://github.com/666ghj/MiroFish`
- `https://github.com/volcengine/OpenViking`

### What MiroFish Contributes

MiroFish is the stronger simulation-side reference. From the upstream repository, the grounded takeaways are:

- backend and frontend split around an interactive simulation product
- seed-material ingestion followed by world construction
- multi-agent simulation with memory and behavior
- report generation on top of simulated world state
- a user-facing interactive environment rather than a static model output

For `city_expansion_sim`, that suggests:

- scenario seeding from city data, plans, policy changes, or events
- a persistent simulation world that can be stepped and inspected
- agent groups such as residents, developers, institutions, and government
- derived reports and metrics generated from runtime state, not just raw overlays
- a frontend built for exploration and intervention, not only map display

### What OpenViking Contributes

OpenViking is not a city simulation engine. It is an agent-oriented context system. That means its value here is architectural, not domain-level. The relevant ideas are:

- filesystem-like organization of project knowledge
- hierarchical context delivery
- explicit separation of memory, resources, and skills
- observable retrieval and state organization

For `city_expansion_sim`, that suggests:

- explicit scenario assets and metadata
- structured simulation state snapshots
- clear separation between runtime state, calibration inputs, and shared contracts
- an orchestration layer that can evolve with the project instead of relying on ad hoc notes
