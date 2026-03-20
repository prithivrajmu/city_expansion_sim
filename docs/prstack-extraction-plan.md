# prstack Extraction Plan

`prstack` has now moved from repo-local helper to a reusable Codex-native workflow stack that other projects can adopt.

## Goal

Split `prstack` into its own publishable repository while keeping `city_expansion_sim` as the proving ground.

Status:

- standalone repo created at `github.com/prithivrajmu/prstack`
- `city_expansion_sim` now uses a local shim plus `.prstack/project.env`

## Scope

- codify `gstack`-style workflow modes for Codex
- keep Ralph as an optional bounded execution engine
- keep reports and templates file-based and inspectable
- support repo bootstrap, plan, review, QA, ship, specialist review, and loop flows

## Proposed Repository Shape

- `bin/prstack`
- `templates/`
- `roles/`
- `examples/`
- `docs/`
- `install/`

## Integration Model

- `prstack` installs into a project under `.prstack/` or `ops/prstack/`
- Ralph integration remains optional and is activated when a local `ralph` runner is present
- project-specific templates can extend or override the defaults

## Suggested Phases

1. Extract the generic CLI and templates from `city_expansion_sim`
2. Replace hardcoded project paths with relative project-root discovery
3. Move specialist roles and report templates into the standalone package
4. Add installer/bootstrap commands for Codex-managed repos
5. Publish examples, including `city_expansion_sim`, as reference integrations

## Near-Term Work

- remove app-specific assumptions from `review`, `qa`, and `ship`
- define a project config file for custom commands and reports
- decide whether distribution is `npm`, `git clone`, or both
- create a companion demo repo or example folder showing Ralph loop integration
