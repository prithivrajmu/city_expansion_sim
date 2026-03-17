# Inspiration Repos

## Pinned

- `gstack`: `https://github.com/garrytan/gstack`
- `OpenViking`: `https://github.com/volcengine/OpenViking`
- `MiroFish`: `https://github.com/666ghj/MiroFish`

## What OpenViking Contributes

OpenViking is an agent-oriented context database, not a city simulator.

The useful takeaways for this repo are structural:

- organize knowledge and assets explicitly
- separate layers of context and detail
- keep state and retrieval observable
- treat workflow support as first-class infrastructure

## What MiroFish Contributes

MiroFish is a multi-agent prediction and simulation product. The useful takeaways for this repo are:

- seed-driven world construction
- interactive simulation rather than static forecasting
- multi-agent world dynamics
- generated reports on top of evolving state
- a full product shape with backend and frontend separation

## Combined Interpretation

For `city_expansion_sim`, the current interpretation is:

- use `MiroFish` for simulation-product direction
- use `OpenViking` for structured context and state organization
- use `gstack` for workflow and operating modes, adapted through `prstack`
