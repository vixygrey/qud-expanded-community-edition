# Notes for coding agents


If you are an AI assistant working in this repository, start here. This file is deliberately short
and points at the documents and house rules that apply to contributions.


## Read these first

| File | What it settles |
|---|---|
| [`docs/CHARTER.md`](docs/CHARTER.md) | The six rules this fork is maintained under. Rule 1 (merge, never replace) and rule 5 (what the C# may not do) are the two that will fail a review if you miss them. |
| [`docs/STYLEGUIDE.md`](docs/STYLEGUIDE.md) | Naming, layout, formatting. **§1 first**, because several names are identifiers and renaming one fails silently with no error anywhere. |
| [`docs/LESSONS.md`](docs/LESSONS.md) | Traps already hit, mostly about Qud itself. Reading it will save you rediscovering them. |
| [`CONVENTIONS.md`](CONVENTIONS.md) | Project conventions for engineering, delivery, specifications, and documentation. |
| [`specs/README.md`](specs/README.md) | Index of the active project specifications and their required structure. |
| [`docs/FEATURES.md`](docs/FEATURES.md) | What the mod does. §10 is the backlog, with a file and line per row. |
| [`docs/WIKI.md`](docs/WIKI.md) | An index of Freehold's official modding wiki: which page answers which question, and where the wiki and the game's assembly disagree. Check it before deriving Qud's behaviour from scratch. |
| [`docs/RELEASING.md`](docs/RELEASING.md) | How a release is cut. Two publications, and neither implies the other. |

## The things most likely to trip you

- **`mod/` ships verbatim to the Steam Workshop.** Anything in that directory reaches subscribers.
  Keep development tooling at the repository root.
- **The repository has no build step.** Qud loads XML directly. Do not add a build step.
- **Use `Load="Merge"` for every vanilla record that you touch.**
  A redeclaration discards future Qud patches.
  The `merge-discipline` validator check enforces this rule.
- **The C# compiles through a local hook, not CI.**
  `tools/compile_scripting.py` builds `mod/Scripting/` against the game's assemblies.
  The hook runs on commits that touch this directory.
  It needs Caves of Qud and skips when the game is unavailable.
  CodeQL does not cover the C#.
  The repository has no `.csproj` because compilation needs four DLLs from a Qud install.
  Report an unavailable local compile in the pull request.
- **Check tile names against the installed game.**
  Qud renders a missing `Tile=` as a solid colored block.
  `tools/check_tile_names.py` reads names from `Data/resources.assets`.
  Use an existing game tile or add a sprite under `mod/Textures/`.
  Sprites must use 16x24 RGBA pixels and exactly three values:
  transparent, white for `ColorString`, and black for `DetailColor`.
  Use the established naming pattern for each directory.
  `items/` uses `Vixy_PascalCase.png` with the same XML extension.
  `Subtypes/` writes `.bmp` against a `.png`.
  **Build sprites with `tools/make_tile.py`** from an ASCII map in `tools/tiles/`.
  The tool rejects a wrong size and a fourth color.
  Keep the maps outside `mod/`.
- **A missing `command -v` result does not prove that a tool is absent.**
  The .NET installer writes the literal `~/.dotnet/tools` to `/etc/paths.d/dotnet-cli-tools`.
  `path_helper` does not expand `~`.
  Add `export PATH="$HOME/.dotnet/tools:$PATH"` before deciding that `ilspycmd` is absent.
  See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the full explanation.
- **Do not use `rg -r` as a recursive search flag.**
  Ripgrep recurses by default.
  The `-r` option replaces matched text.
  See [`docs/LESSONS.md`](docs/LESSONS.md) for the failure record.
- **Check Qud claims against the game's files.**
  Read installed mods under `steamapps/workshop/content/333640/`.
  Read vanilla data under `StreamingAssets/Base`.
  [`docs/LESSONS.md`](docs/LESSONS.md) identifies vanilla files that are not valid XML.
  Resolve `Inherits=` before counting parts or tags.
  Treat `*noinherit` and `*delete` as tag sentinels.
  A `Tier` tag states an item's crafting cost, not its player encounter point.
  Use population tables to determine encounter point.

## Before you commit

```bash
python3 tools/validate_mod.py
```

Ten checks run on every pull request and all ten must pass. Never commit to `main`. Branch, then
open a pull request.

## Task tracking

Mark each TODO complete immediately after its work finishes.

Do not wait until the end of a section to mark completed TODOs.

Do not batch TODO updates after multiple tasks finish.

Keep the task list synchronized with the work in progress.


## Writing

Use clear, concise American English.

Use active voice and simple present or past tense in descriptive text.

Write instructions in the imperative.

Keep one topic per paragraph and one instruction per sentence.

Keep descriptive sentences to 25 words or fewer and procedural sentences to 20 words or fewer.

Use complete sentences with articles. Do not use contractions.

Use one consistent term for each concept.

Do not use em dashes, semicolons, filler words, Latin abbreviations, or unexplained jargon.

Put required conditions before commands.

Put a clear command before the risk in warnings and cautions.

Keep code, identifiers, file paths, quoted errors, and proper nouns unchanged.

Apply these rules to specifications, technical documentation, changelogs, release notes, error messages, CLI output, and UI copy.

Use the looser version for issues, comments, and chat. Keep those passages clear and free of filler.

The project-specific documentation rules are in [`CONVENTIONS.md`](CONVENTIONS.md).
