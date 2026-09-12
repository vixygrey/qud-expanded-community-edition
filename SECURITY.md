# Security policy

This mod ships C#. Qud runs mods with **full process privileges**.
Any mod with a `Scripting/` directory asks each subscriber for approval before loading.
This creates a direct trust relationship.

## Reporting

**Use [private vulnerability reporting](https://github.com/vixygrey/qud-expanded-community-edition/security/advisories/new).**
The report stays private until a fix exists.

Do not open a public issue for a vulnerability that subscribers cannot safely receive before an update.
Use a normal issue for crashes, broken drop tables, and incorrect values.

This project has one maintainer, so no response time is guaranteed.
The maintainer will acknowledge each report and state the planned action.

## In scope

Anything in **`mod/`**, which is what's uploaded to the Steam Workshop and what actually runs on a
player's machine. Most of all `mod/Scripting/`.

Concretely, a report is in scope if this mod's shipped code:

- reads or writes files outside the mod's own directory
- makes any network request, or sends telemetry of any kind
- reads player files, environment variables, or anything about the machine
- shells out, or loads an external assembly
- uses reflection to reach into game internals, or bundles Harmony
- crashes or corrupts a save in a way another mod or a player could trigger deliberately

The first six are forbidden outright by
[`docs/CHARTER.md`](docs/CHARTER.md) rule 5. If you find one, the rule has been broken and I want to
know.

## What already enforces this

`tools/validate_mod.py` runs two checks on every pull request.
Both checks must pass:

- **`scripting-policy`** matches every banned API in rule 5 against `mod/Scripting/`.
  Each pattern names the clause that it enforces.
  The check strips comments because the scripts describe these APIs.
  It keeps string literals because `Type.GetType("System.IO.File")` can evade a token scan.
- **`serializable-shape`** flags every instance field on a `[Serializable]` type.
  That layout enters every player's save file.

These checks are not security boundaries.
The maintainer writes this code, and a determined actor can evade both checks.
They catch **drift**, such as a forgotten `File.ReadAllText` call or a dependency that adds Harmony.

**CodeQL does not cover the C#.** Every non-`System` dependency exists only in Freehold's
`Assembly-CSharp.dll`.
The proprietary assembly is absent from CI runners.
Call-target resolution therefore remains below CodeQL's threshold.
The two checks enforce project rules that CodeQL's generic queries cannot express.
See rule 5 in [`docs/CHARTER.md`](docs/CHARTER.md) for the full reasoning.

**The C# compiles locally, not in CI.** `tools/compile_scripting.py` builds `mod/Scripting/`
against the game's assemblies through a pre-commit hook.
The hook catches syntax errors before release.
The hook cannot run in CI because Freehold's proprietary `Assembly-CSharp.dll` is required.
The hook skips when the game is not installed.
No CI check compiles this C#.
A maintainer must review each scripting change.
The repository has no `.csproj` because the compile needs four DLLs from a Qud install.

## Supported versions

Support only the current release.
This project has one maintainer and does not backport fixes.

## Out of scope

- Report vulnerabilities in **Caves of Qud itself** to
  [Freehold Games](https://www.cavesofqud.com/).
  Tell the maintainer when a game vulnerability affects this mod.
  The maintainer will work around it and apply the `upstream-qud` label.
- Do not report vulnerabilities in **other mods**, including Mura's original and its split sub-mods.
- Do not report an issue that requires write access to a player's Qud install directory.
  At that point the mod is not the weak link.
