# Guardrails

## Signs

### Sign: Bounded Loop Only
- **Trigger**: When using Ralph for implementation
- **Instruction**: Run only bounded iterations through `prstack loop`, never an open-ended autonomous loop
- **Added after**: Initial Ralph integration for city_expansion_sim

### Sign: prstack Owns Workflow
- **Trigger**: When choosing between direct Ralph usage and repo workflow
- **Instruction**: Keep `prstack` as the main workflow layer; Ralph is only an execution loop inside it
- **Added after**: Initial Ralph integration for city_expansion_sim

### Sign: Stay Out of Legacy
- **Trigger**: When selecting files to modify
- **Instruction**: Do not edit `legacy/` unless the selected story explicitly requires it
- **Added after**: Preserving the old prototype during the rebuild

### Sign: Verify Before Marking Done
- **Trigger**: Before completing a story
- **Instruction**: Run `./ops/prstack/bin/prstack review` and `./ops/prstack/bin/prstack qa`
- **Added after**: Establishing the repo-local workflow gates
