# prstack

`prstack` is a lightweight, repo-local orchestration layer for `city_expansion_sim`.

It is meant to give Codex a stable workflow surface while the project is being rebuilt:

- mission
- tasks
- status
- iteration notes
- mode-specific workflow reports

`prstack` is informed by `gstack`, but it is not a direct port. The intent is to keep the useful workflow ideas while staying native to this environment.

## Commands

From the repo root:

```bash
./ops/prstack/bin/prstack bootstrap
./ops/prstack/bin/prstack install
./ops/prstack/bin/prstack dev
./ops/prstack/bin/prstack plan "Intervention Slice"
./ops/prstack/bin/prstack slice "Intervention Slice"
./ops/prstack/bin/prstack ralph-ping
./ops/prstack/bin/prstack loop 1 --no-commit
./ops/prstack/bin/prstack ceo-review
./ops/prstack/bin/prstack security-review
./ops/prstack/bin/prstack review
./ops/prstack/bin/prstack qa
./ops/prstack/bin/prstack ship
./ops/prstack/bin/prstack handoff
./ops/prstack/bin/prstack status
```

## Workflow Modes

- `plan` updates the active implementation slice
- `slice` creates a named slice record and makes it current
- `ralph-ping` smoke-checks the local Ralph + Codex runner
- `loop` runs bounded Ralph build iterations, then returns through `review`, `qa`, and `handoff`
- `ceo-review` writes a product/founder review against the current slice
- `security-review` writes a deployment-risk review against the current stack
- `review` runs the automated build-and-test review gate
- `qa` runs API and simulation smoke verification
- `ship` bundles review, QA, CEO review, security review, and handoff into a local release packet
- `handoff` writes the current transfer summary

## Notes

- this is now a real local workflow stack, not just a launcher
- state is intentionally stored as markdown so it is easy to inspect and edit
- if you later want a richer workflow, we can add JSON schemas, branch helpers, or PR summaries
- `prstack dev` is the intended autorun entrypoint for local development
- Ralph is integrated as a bounded loop runner inside `prstack`, not as a replacement workflow
- specialist guidance now lives inside the stack instead of staying implicit in ad hoc prompts
