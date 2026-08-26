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
| [`docs/RELEASING.md`](docs/RELEASING.md) | How a release is cut. Two publications, and neither implies the other. |

## The things most likely to trip you

- **`mod/` is uploaded verbatim to the Steam Workshop.** Anything you put there ships to
  subscribers. Development tooling lives at the repo root, outside `mod/`.
- **There is no build step.** Qud loads the XML directly. Don't add one.
- **`Load="Merge"` on every touch of a vanilla record.** A redeclaration silently discards whatever
  future Qud patches add. The validator's `merge-discipline` check enforces it.
- **The C# is compiled by a local hook, not by CI.** `tools/compile_scripting.py` builds
  `mod/Scripting/` against the game's own assemblies in about half a second, and runs automatically on
  any commit touching it. But it needs Caves of Qud installed and skips where it isn't, CodeQL still
  can't cover the C#, and nothing on a runner ever compiles it. There's still no `.csproj` — the
  compile needs four DLLs from a Qud install and nothing else. If you changed C# and couldn't compile
  it, say so in the pull request.
- **`command -v` finding nothing does not mean a tool is missing.** The .NET installer puts the
  literal `~/.dotnet/tools` in `/etc/paths.d/dotnet-cli-tools` and `path_helper` never expands the
  `~`, so `ilspycmd` and friends are invisible while `$PATH` looks correct. `export
  PATH="$HOME/.dotnet/tools:$PATH"` first, then decide whether a tool is absent — see
  [`CONTRIBUTING.md`](CONTRIBUTING.md) for the full reason. Concluding "not installed" here has
  already sent one investigation down the wrong road.
- **Verify claims about Qud against the game's own files** rather than from memory — the installed
  mods under `steamapps/workshop/content/333640/` and the vanilla data under
  `StreamingAssets/Base`. `docs/LESSONS.md` explains where both are and which vanilla files aren't
  valid XML. When the claim is that two things are *related* — a scope, a tag, an `Inherits=` —
  count what's on the other end of it. Seven of the 36 cultures `Naming.xml` scopes on match nothing
  in the game, `Qudish` among them.

## Before you commit

```bash
python3 tools/validate_mod.py
```

Ten checks run on every pull request and all ten must pass. Never commit to `main` — branch, then
open a pull request.

## Writing

Write in whatever voice suits the person you're helping. The documents in this repository are in the
maintainer's first-person voice because she wrote them; that's a description of how she writes, not
a house style anyone else has to match.
