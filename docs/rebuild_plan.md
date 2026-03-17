# Rebuild Plan

## Phase 1

Reset the repository shape.

- rename the project to `city_expansion_sim`
- move prototype files into `legacy/`
- replace misleading docs
- define the new module boundaries

## Phase 2

Create the runtime skeleton.

- choose backend stack
- choose frontend stack
- define shared schemas
- implement a minimal simulation state and tick loop

## Phase 3

Create the first playable vertical slice.

- load one scenario
- render the world
- step time forward
- show land-use and growth metrics
- allow a small set of interventions

## Phase 4

Bring back real data.

- Chennai as a calibrated scenario
- infrastructure layers
- flood risk and terrain
- land valuation and accessibility
- district-level population pressure

## Phase 5

Expand into a reusable platform.

- multiple city scenarios
- save files
- scenario editor
- parameter tuning
- replay and comparison tools
