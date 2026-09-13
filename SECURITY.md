# Security policy

This mod ships C#. Qud runs mods with **full process privileges**, and any mod containing a
`Scripting/` directory makes the game ask each subscriber to approve it before loading. That's a
real trust relationship, and this document exists because of it rather than as boilerplate.

## Reporting

**Use [private vulnerability reporting](https://github.com/vixygrey/qud-expanded-community-edition/security/advisories/new).**
It's enabled on this repository, so the report stays between us until there's a fix.

Please don't open a public issue for anything that could be abused before subscribers can update.
For everything else — a crash, a broken drop table, a wrong number — a normal issue is perfect and I'd
rather have it that way.

I maintain this on my own, so I can't promise a response time. I will acknowledge a report and tell
you what I intend to do about it.

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

`tools/validate_mod.py` runs two checks on every pull request, and both must pass:

- **`scripting-policy`** — pattern-matches every banned API in rule 5's list against
  `mod/Scripting/`, with each pattern naming the clause it enforces. Comments are stripped first,
  since the scripts legitimately *describe* these APIs; string literals deliberately are not,
  because `Type.GetType("System.IO.File")` is how a token scan gets sidestepped.
- **`serializable-shape`** — flags any instance field on a `[Serializable]` type, because that
  layout is written into every player's save file.

Neither is a security boundary. I write this code, and anyone determined could evade both trivially.
They catch **drift** — the `File.ReadAllText` added while debugging and forgotten, or a dependency
that quietly pulls Harmony in.

**CodeQL does not cover the C#, and can't.** Every non-`System` dependency lives only in Freehold's
`Assembly-CSharp.dll`, which is proprietary and absent from CI runners, so call-target resolution
sat permanently below CodeQL's threshold. The two checks above are what stands in its place, and
they enforce a project policy CodeQL's generic queries could never express. `docs/CHARTER.md` rule 5
has the full reasoning.

**The C# is compiled locally, not here.** `tools/compile_scripting.py` builds `mod/Scripting/` against
the game's own assemblies as a pre-commit hook, so a syntax error is caught before it ships. It cannot
run in CI, though — compiling needs Freehold's proprietary `Assembly-CSharp.dll`, which is the same
wall CodeQL hit — and it skips where the game isn't installed. So no check on a runner ever compiles
this C#, and a review of a contributor's scripting change is still a human reading it. There remains
deliberately no `.csproj`: the compile needs four DLLs from a Qud install and nothing else.

## Supported versions

Only the current release. This is a single-maintainer hobby project and I don't backport.

## Out of scope

- Vulnerabilities in **Caves of Qud itself** — report those to
  [Freehold Games](https://www.cavesofqud.com/). If one affects how this mod behaves, do tell me and
  I'll work around it; issues like that get the `upstream-qud` label.
- Vulnerabilities in **other mods**, including Mura's original and the sub-mods split from it.
- Anything requiring an attacker to already have write access to a player's Qud install directory.
  At that point the mod is not the weak link.
