# Notes for coding agents

If you're an AI assistant working in this repository, start here. This file is deliberately short
and carries no personal preferences — it points at the documents that already exist.

The maintainer's own instructions live in an untracked `CLAUDE.md` and are hers, not yours. Nothing
in them applies to a contribution you're helping someone else write.

## Read these first

| File | What it settles |
|---|---|
| [`docs/CHARTER.md`](docs/CHARTER.md) | The six rules this fork is maintained under. Rule 1 (merge, never replace) and rule 5 (what the C# may not do) are the two that will fail a review if you miss them. |
| [`docs/STYLEGUIDE.md`](docs/STYLEGUIDE.md) | Naming, layout, formatting. **§1 first** — several names are identifiers, and renaming one fails silently with no error anywhere. |
| [`docs/LESSONS.md`](docs/LESSONS.md) | Traps already hit, mostly about Qud itself. Reading it will save you rediscovering them. |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Workflow: issue first, conventional commits with repo-specific scopes, changelog entry required on every pull request. |
| [`docs/FEATURES.md`](docs/FEATURES.md) | What the mod does. §10 is the backlog, with a file and line per row. |

## The things most likely to trip you

- **`mod/` is uploaded verbatim to the Steam Workshop.** Anything you put there ships to
  subscribers. Development tooling lives at the repo root, outside `mod/`.
- **There is no build step.** Qud loads the XML directly. Don't add one.
- **`Load="Merge"` on every touch of a vanilla record.** A redeclaration silently discards whatever
  future Qud patches add. The validator's `merge-discipline` check enforces it.
- **The C# has no compile gate.** There's no `.csproj` and CodeQL can't cover it, so a syntax error
  surfaces as the mod failing to load in game. Be correspondingly careful.
- **Verify claims about Qud against the game's own files** rather than from memory — the installed
  mods under `steamapps/workshop/content/333640/` and the vanilla data under
  `StreamingAssets/Base`. `docs/LESSONS.md` explains where both are and which vanilla files aren't
  valid XML.

## Before you commit

```bash
python3 tools/validate_mod.py
```

Nine checks run on every pull request and all nine must pass. Never commit to `main` — branch, then
open a pull request.

## Writing

Write in whatever voice suits the person you're helping. The documents in this repository are in the
maintainer's first-person voice because she wrote them; that's a description of how she writes, not
a house style anyone else has to match.
