# External prstack Shim

`city_expansion_sim` no longer carries its own embedded `prstack` implementation.

This directory is now a compatibility shim:

- `bin/prstack` forwards to the standalone repo at `github.com/prithivrajmu/prstack`
- project-specific configuration lives in `.prstack/project.env`
- generated workflow state lives in `.prstack/state/`

Normal usage from this repo stays the same:

```bash
./ops/prstack/bin/prstack review
./ops/prstack/bin/prstack qa
./ops/prstack/bin/prstack ship
./ops/prstack/bin/prstack loop 1 --no-commit
```
