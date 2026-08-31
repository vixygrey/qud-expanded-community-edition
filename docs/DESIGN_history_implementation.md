# Implementation Notes, Recon Plan, and Open Questions

> Nothing here is settled. The game is not yet installed on the development machine, so
> every claim about internals is inference from public documentation. **Section 2 is the
> first work item of the project.**

---

## 1. Modding tiers

Qud supports three escalating levels of modification, with quite different risk profiles.

### Tier 1 — Data only (XML, wordlists)

Unbreakable across patches, merges cleanly with other mods given unique identifier
prefixes, no user approval prompt, near-zero maintenance.

Cannot change slot *structure* — only what fills the slots. For this project that means it
can plausibly deliver the plainness quota (`DESIGN_history_naming.md` §4) and nothing else. Whether even
that is reachable depends on recon question #1.

### Tier 2 — C# scripted types

`.cs` files shipped in the mod are **compiled at runtime**, and the type resolver prefers
mod assembly types over base-game types — so new types can be added and existing ones
overridden by naming convention, without Harmony. Scribed constructs (`IScribedPart`,
`IScribedEffect`, `IScribedSystem`) exist specifically so mods can migrate saves across their
own version changes, which matters when players are mid-playthrough and the mod updates.

**This is the intended home for most of this project.**

Costs: C# mods trigger an approval prompt that users must re-accept **every time the mod
changes** — recurring friction for an iterating Workshop mod, and a predictable source of
"mod stopped working" reports that are actually unaccepted prompts. There is also no
official API documentation; the assembly must be decompiled (ILSpy) to find anything.

### Tier 3 — Harmony

Bundled with the game, no external dependency. The only route to internals with no exposed
seam.

The wiki is blunt: Harmony patches are "more prone to incompatibility with other mods and
future updates" and harder to debug. Risk is not uniform —

- **Safest:** postfix patches, non-blocking prefixes
- **Risky:** blocking prefixes, transpilers

Two project-specific aggravators. First, worldgen is exactly the code other overhaul mods
want to patch, so this mod would compete for the same methods with whatever else a user has
installed. Second, failure occurs *during world generation* — the least recoverable moment
in a roguelike.

**Position:** postfix-only, and only where Tier 2 cannot reach. The wiki explicitly
encourages asking the developers to add proper hooks instead of patching around their
absence. A mod of this scope is a strong argument for such a hook — worth opening that
conversation early rather than after shipping.

> **⚠ Platform constraint:** primary development happens on macOS, where Harmony is
> unreliable or unavailable. A separate Windows machine is available for verification, so
> Tier 3 is **conditionally open — quarantined and release-gated**, not freely available.
> See §8, and §8.7 for the required workflow.

### Tier assignment by component

| Component | Expected tier | Confidence |
|---|---|---|
| Plainness quota / PLAIN lexicon | 1 if wordlists are XML, else 2 | low — gated on Q1 |
| Naming derivation (`DESIGN_history_naming.md`) | 2, else 3 (gated, §8.7) | low — gated on Q2 |
| Ledger + threads (`DESIGN_history_events.md`) | 2 | medium |
| Event pool extension | 2 if registrable, else 3 (gated) | low — gated on Q3 |
| Source divergence (`DESIGN_history_sources.md`) | 2 | low — gated on Q6 |
| Cross-sultan legacy | 2–3 | low — gated on Q5 |

Most confidences are low. That is the honest state of the project and the reason §2 exists.

---

## 2. Recon plan

Run once Caves of Qud is installed. Order matters — each answer changes the value of later
questions.

### Setup

1. Locate the install; on macOS Steam this is typically
   `Library/Application Support/Steam/steamapps/common/Caves of Qud`.
2. Inventory shipped data files. Qud ships its XML openly — establish what exists before
   assuming anything must be code.
3. Decompile the game assembly with ILSpy (or `ilspycmd`) and export `XRL.Annals` to source.

### The questions, in priority order

**Q0 — Does Harmony work at all on this machine?**
Run before everything else; it is a twenty-minute empirical test (§8.3) and it determines
whether the rest of the plan has a fallback tier or not.

**Q1 — Where does the text live?**
For each of the seventeen event types, is its prose in shipped XML or compiled into the
assembly? Determines whether *any* of this is Tier 1, and how the 128 authored fragments
(`DESIGN_history_catalog.md` §6) would actually be delivered.

**Q2 — Is there a naming seam?**
At the point a relic is named, is the originating event still in scope? This gates
`DESIGN_history_naming.md` entirely. If the answer is no, the fallback is rung 3 of the ladder — the
plainness quota applied to site-derived names — which is still a complete v0.1.

**Q3 — Can the event pool be extended by registration?**
Does `QudHistoryFactory` enumerate event generators dynamically (in which case new
`XRL.Annals.*`-shaped types may register themselves), or is the pool a hardcoded list? The
difference between Tier 2 and Tier 3 for the entire expansion.

**Q4 — Token or string substitution for the era vocabulary?**
If cosmic/earthen swapping operates on *tokens* inside a shared template, each new event
costs 2 fragments rather than 4 — **halving the authoring cost of the whole project**.
Highest value-per-minute question on this list.

**Q5 — Are the five sultans generated in chronological sequence, in one pass?**
Gates cross-sultan causality (`DESIGN_history_events.md` §7). If they are generated independently,
the dynastic ledger needs a different mechanism.

**Q6 — Do murals, gossip, and village descriptions read the history record, or generate
independently?**
Determines whether `DESIGN_history_sources.md` can reach beyond gospel and tomb, and would reveal how
much of the perceived incoherence comes from parallel generators rather than from history
generation at all.

**Q7 — Can biography generation be invoked headlessly?**
Needed for the instrumentation in §5. If histories can only be produced by generating a
world, the tuning loop is slow but workable; if they can be produced in isolation, corpus
generation becomes trivial and tuning gets dramatically easier.

### Deliverable

A `DESIGN_history_recon.md` in this folder answering all eight, with the tier table in §1
re-scored. **No implementation work should begin before that document exists** — the
sequencing risk (authoring in a format that later needs retrofitting) is exactly what
`DESIGN_history.md` P3 warns against.

---

## 3. Workshop and compatibility practice

Drawn from the wiki's compatibility and best-practices guidance.

- **Unique prefixes on every identifier.** `LX_` throughout — blueprints, event types,
  parts, systems.
- **Merge XML, never wholesale-copy.** Do not duplicate base-game blocks; merge onto them.
- **Scribed constructs** (`IScribedPart` / `IScribedSystem`) for anything persisted, so mod
  version bumps do not corrupt saves.
- **Seeded RNG throughout.** Required for reproducible worlds and for the tuning loop in §5.
- **Named function arguments** where calling into base-game code, for resilience against
  signature changes.
- **Fail toward vanilla** (P8). Any generation step that cannot satisfy constraints falls
  back rather than throwing. Worldgen is the worst place in the game to throw.
- **Config toggles** for the major subsystems — particularly source divergence, which some
  players will not want.

### Update fragility

Qud continues to receive patches post-1.0. Tier 2 overrides break loudly (compile errors,
visible at load); Harmony postfixes break quietly (patch silently fails to apply). Prefer
loud failure, and log a version check at load so a mismatch is visible in the mod's own
output rather than surfacing as "histories look vanilla again."

---

## 4. Repository layout

```
qud-mods/
└── lore-expansion/
    ├── docs/                    ← this folder
    │   ├── DESIGN_history.md
    │   ├── DESIGN_history_events.md
    │   ├── DESIGN_history_catalog.md
    │   ├── DESIGN_history_naming.md
    │   ├── DESIGN_history_sources.md
    │   ├── DESIGN_history_implementation.md
    │   └── DESIGN_history_recon.md    ← to be written (§2)
    ├── mod/                     ← the shippable mod
    │   ├── manifest.json
    │   ├── Scripts/
    │   └── XML/
    ├── tools/                   ← corpus generation, metrics, chain viewer (§5)
    └── corpus/                  ← generated histories for analysis (gitignored)
```

With the Harmony quarantine (§8.7 W1) and its surface log, `mod/` and `docs/` become:

```
    ├── docs/
    │   └── patched-surface.md    ← every Harmony patch, why Tier 2 couldn't reach it (W2)
    ├── mod/
    │   ├── Scripts/
    │   │   ├── Harmony/          ← ALL Harmony patches, nowhere else (W1)
    │   │   └── …                 ← Tier 2 types, no patches
    │   └── XML/
```

---

## 5. Instrumentation

`DESIGN_history.md` §6 sets numeric targets. They need a harness, and building it early is what
makes the tuning constants in `DESIGN_history_events.md` §5.2 adjustable rather than guessed.

**Corpus dump.** Generate *n* worlds with fixed seeds and dump every sultan biography as
structured data — events, roles, threads opened and closed, referents introduced, names
generated. Feasibility depends on Q7.

**Metrics to compute over the corpus:**

- Distinct event types per world; mean repeats per type
- Share of events participating in a chain of ≥ 2
- Distribution of thread lifespans (opened → closed, in events)
- Unresolved-thread rate at death — target ≈ ⅓
- Distinct cross-referenced proper nouns per world
- Plain-token share in generated names
- Share of names referencing a record fact
- Fallback rate (how often the generator hits `FALLBACK_POOL` — a pool-starvation alarm)
- Noun reuse frequency (the plainness-quota risk, `DESIGN_history_naming.md` §6)

**Chain viewer.** A small script rendering one biography as a graph — events as nodes,
threads as edges. Worth building early; most bugs in this design are *structural* and are
nearly invisible in prose but obvious in a graph.

**Baseline first.** Run the harness against **unmodded** worldgen before writing any mod
code. Every target in `DESIGN_history.md` §6 is currently an estimate inferred from published
descriptions. Measured baselines make the design falsifiable, and there is a real chance
they show the vanilla situation is better or worse than assumed — either of which should
change the plan.

---

## 6. Risk register

| Risk | Severity | Mitigation |
|---|---|---|
| Harmony unusable on the macOS dev machine | Medium | Windows machine available for verification; quarantine + release gate (§8.7) |
| **Harmony surface drifts between Windows verification passes** | **High** | W1 quarantine, W2 documented surface, W4 application logging, W5 release gate |
| No stateful seam in history generation (Q-blocking) | High | Tier 2 techniques first (§8.5); Harmony as gated fallback; else naming-only scope |
| No naming seam with event in scope | High | Fallback ladder rung 3 (`DESIGN_history_naming.md` §7) |
| Event pool not extensible without replacing the factory | Medium | Replace factory wholesale; accept higher update fragility |
| Authoring burden stalls the project | **High** | Ship 0.1 and 0.2 with zero new prose; expansion is optional upside |
| Game update breaks the mod | Medium | Prefer Tier 2 over 3; version-check logging; postfix-only Harmony |
| Mod approval prompt friction | Low | Document prominently on the Workshop page; batch releases |
| Conflicts with other worldgen overhauls | Medium | Postfix-only; unique prefixes; publish the patched surface |
| Tuning constants never converge | Medium | Build instrumentation before content (§5) |

The two **High** risks are both mitigated the same way: **v0.1 and v0.2 must be independently
shippable and must require no new prose.** If the project stalls after either, it has still
delivered a real mod.

---

## 7. Immediate next actions

1. Install Caves of Qud on **both** machines — the Mac for authoring, the Windows PC for
   verification and corpus runs (§8.7).
2. Run **Q0** on the Mac (§8.3). If Harmony works under Rosetta, the two-machine workflow
   becomes optional and everything gets easier.
3. Run the rest of the recon plan (§2); write `DESIGN_history_recon.md`.
4. Re-score the tier table (§1) and the risk register (§6) against actual findings.
5. Build the corpus harness on the Windows machine and measure the vanilla baseline (§5).
6. Only then: decide whether v0.1 is Tier 1 or Tier 2, and begin.

---

## 8. Platform constraint — Harmony on macOS

Development happens on macOS. This is a first-class constraint on the architecture, not a
tooling inconvenience, and it should be resolved before any implementation begins.

### 8.1 What is actually broken

Two related failure modes, both real and both documented:

**Memory protection / SIP.** Harmony patches by making executable memory writable at
runtime. On macOS this is exactly what System Integrity Protection and the platform's
W^X enforcement are designed to prevent. A modder working on *Caves of Qud mods
specifically* reports Harmony failing on macOS with a memory-protection error, with Full
Disk Access granted and no effect. Their listed workarounds were: avoid Harmony-dependent
mods, disable SIP (rightly rejected as unacceptable to ask of players), or use
reflection-based patching instead.

**arm64 detours.** Separately, `mprotect returned EACCES` on Apple Silicon under native
ARM Unity builds, originating in MonoMod's POSIX detour platform — Harmony's underlying
patch engine had no working ARM64 macOS path for a long stretch. Upstream MonoMod work has
since landed (visible downstream: a RimWorld community Harmony fork for Apple Silicon has
been *deprecated* on the grounds that upstream now supports it), so this specific gap is
narrowing.

**Relevant mitigating fact:** Caves of Qud on Apple Silicon is reported to run under
**Rosetta 2 rather than as a native arm64 build**. If that holds, Harmony would use its
well-trodden x86-64 detour path rather than the ARM64 path, and the arm64 problem may not
apply at all — leaving only the SIP/mprotect question. This is worth an empirical test
rather than an assumption (§8.3).

### 8.2 Why this matters more for a Workshop mod than for a personal one

The asymmetry is the important part, and it is worse than "the feature doesn't work."

Harmony failing on macOS does **not** mean the patch fails for the audience. Most Workshop
users are on Windows, where it would apply normally. So the failure mode is:

> Ship a Harmony patch → it silently does nothing on the dev machine → it *does* apply on
> thousands of Windows machines → bugs are reported that cannot be reproduced locally.

Shipping a code path that cannot be executed on the development machine is worse than not
shipping it. This applies with special force to worldgen, where a bad patch corrupts world
generation — the least recoverable moment in the game — and where the developer has no way
to see it happen.

**Rule for this project: no Harmony patch ships unless it has been executed and observed on
a machine where it actually applies.** A dedicated Windows machine is available, so this is
satisfiable — but only by an explicit release gate (§8.7), not by intention.

### 8.3 The test (Q0, do this first)

Twenty minutes, and it settles the tier table:

1. Install Caves of Qud.
2. Subscribe to any existing Workshop mod known to use Harmony.
3. Launch, approve the scripting mod, and check the player log for patch application versus
   a memory-protection error.
4. Confirm whether the running process is `arm64` or `x86_64` (Activity Monitor's Kind
   column, or `ps`), which distinguishes the Rosetta case from the native-ARM case.
5. If it works: note that Tier 3 is *conditionally* available, and re-test after every game
   and OS update, because this can regress silently.

### 8.4 Consequences for the design

The good news is that this design was already Tier 2 nearly everywhere, so the damage is
contained:

| Component | Prior tier | Revised |
|---|---|---|
| Plainness quota | 1–2 | Unaffected |
| Naming derivation | 2, possibly 3 for the call site | **At risk** — needs a Tier 2 seam or the fallback ladder |
| Ledger + threads | 2 | Unaffected |
| Event pool extension | 2 if registrable, else 3 | **At risk** — if not registrable, must replace the factory outright |
| Source divergence | 2 | Unaffected |
| Cross-sultan legacy | 2–3 | Prefer 2 |

Recon questions **Q2** (is there a naming seam?) and **Q3** (is the event pool extensible by
registration?) were previously about convenience. They are now **feasibility questions** —
if either answer is no, there is no Harmony fallback, and that component needs a different
approach or gets cut.

### 8.5 Tier-2 techniques that replace Harmony

Most of what modders reach for Harmony to do is reachable without it:

- **Type override via the resolver.** Qud's type resolver prefers mod assembly types over
  base-game ones. Subclassing or replacing a whole class is the single most powerful
  non-Harmony tool available and should be the first thing tried for both at-risk
  components.
- **Reflection.** Reading and writing private state does not require detouring and works
  fine under SIP. Slower, but generation runs once per world — performance is irrelevant
  here.
- **Wholesale factory replacement.** If `QudHistoryFactory` cannot be extended, providing a
  replacement is legitimate Tier 2. Cost: incompatibility with any other mod touching
  history, and a hard dependency on tracking upstream changes. Acceptable for an overhaul
  mod, which by nature expects to own its domain.
- **Request a hook.** The wiki explicitly encourages asking the developers for proper
  extension points rather than patching around their absence. Given that macOS has no
  Harmony fallback, this is a materially stronger request than it would otherwise be — a
  history-generation hook would unblock a whole class of mods for Mac developers. Worth
  raising early and framing exactly that way.

### 8.6 If Harmony turns out to be required

Options, in descending order of preference:

1. **Reach it from Tier 2 instead** (§8.5). Still first choice — the compatibility and
   update-fragility arguments against Harmony are independent of platform and did not go
   away when a Windows machine became available.
2. **Use Harmony, quarantined and release-gated** (§8.7). Now viable.
3. **Get a hook added upstream**, and ship when it lands. Slower, but permanently removes
   the problem and helps every other Mac-based modder.
4. **Cut the component.** v0.1 and v0.2 remain shippable without it (§6).
5. **Ask players to disable SIP.** Never. Not an option for a public Workshop mod.

### 8.7 Two-machine workflow

A dedicated Windows gaming PC is available for testing. This reopens Tier 3, but introduces
a different failure mode that needs managing explicitly.

**The new risk is drift, not incapability.** Code gets authored on the Mac in the fast loop
and verified on Windows in the slow one. Verification that requires walking to another
machine happens less often than verification that doesn't — so the Harmony surface silently
accumulates unverified changes between checks. This is a well-understood pattern and the
mitigation is equally well-understood: make the unverified surface small, and gate releases
on checking it.

**Q0 still matters.** Run the §8.3 test on the Mac anyway. If Harmony works under Rosetta
there, the fast loop covers everything and this whole section becomes a formality. Testing
on Windows is the fallback, not the plan.

#### Rules

**W1 — Quarantine.** All Harmony patches live in a single file or a single clearly-named
folder — `mod/Scripts/Harmony/` — and nowhere else. No patch is scattered into a feature
file. The point is that "what has not been verified on Windows" is answerable at a glance.

**W2 — Document the patched surface.** Maintain `docs/patched-surface.md`: every patched
method, its signature, patch type, and why Tier 2 could not reach it. This is the Windows
verification checklist, the update-breakage checklist after every Qud patch, and the
compatibility disclosure for the Workshop page. One file, three jobs.

**W3 — Postfix only, still.** Availability changes nothing about the wiki's advice or the
worldgen-contention argument (§1). Blocking prefixes and transpilers stay off the table.

**W4 — Every Harmony patch logs application.** On patch, log a line confirming it applied.
Harmony's characteristic failure is *silence* — the patch simply doesn't take. An explicit
log line turns a silent no-op into an observable one and makes the Windows pass a matter of
reading a log rather than inferring behaviour from worldgen output.

**W5 — Release gate.** No version ships without a Windows pass over the full §8.2 checklist:
patches applied per log, a generated world inspected, no exceptions. If the Harmony surface
is unchanged since the last verified release, note that and skip — but note it explicitly
rather than assuming.

**W6 — Feature flag the Harmony layer.** The mod must load and function with the Harmony
layer disabled, degrading to whatever Tier 2 can deliver. This gives Mac users (including
the developer) a working mod, isolates Harmony as the cause when something breaks, and means
a patch broken by a Qud update disables one feature instead of the whole mod.

#### Transport

Git is the obvious sync mechanism — repo on both machines, Windows clone pointed at (or
copied into) the Qud `Mods` folder. Avoid file-sync services for the mod folder; partial
syncs during a game launch produce failures that look like mod bugs.

Note that the scripting-mod approval prompt must be re-accepted on **both** machines every
time the code changes. Budget for it; it is a predictable source of "the Windows box says
the mod isn't working."

#### Unexpected upside

The Windows machine is the better host for the §5 instrumentation regardless of Harmony.
Corpus generation means generating many worlds, which is the slowest operation in the
project and the one most worth running on gaming hardware. Consider making the Windows box
the **canonical corpus and metrics host** — measure the vanilla baseline there, run tuning
sweeps there — with the Mac as the authoring environment. That splits the two machines along
the grain of what each is actually good at, and it gives the Windows trip a routine purpose
rather than making it a special occasion, which is exactly what keeps W5 from being skipped.

---

## 9. Sources

- [Modding:Overview — Caves of Qud Wiki](https://wiki.cavesofqud.com/wiki/Modding:Overview)
- [Modding:C Sharp Scripting](https://wiki.cavesofqud.com/wiki/Modding:C_Sharp_Scripting)
- [Modding:Harmony](https://wiki.cavesofqud.com/wiki/Modding:Harmony)
- [Modding:Compatibility](https://wiki.cavesofqud.com/wiki/Modding:Compatibility)
- [Modding:Worlds](https://wiki.cavesofqud.com/wiki/Modding:Worlds)
- [Sultan histories](https://wiki.cavesofqud.com/wiki/Sultan_histories)
- [Relic](https://wiki.cavesofqud.com/wiki/Relic)
- [Steam Workshop: Sultan's Names of Qud](https://steamcommunity.com/sharedfiles/filedetails/?id=3372513310)
- Grinblat & Bucklew, *Subverting historical cause & effect: generation of mythic
  biographies in Caves of Qud* — [ACM DL](https://dl.acm.org/doi/10.1145/3102071.3110574).
  Not yet read; **do so before finalising `DESIGN_history_events.md`**, as it states the designers'
  intent about deliberate non-causality.
- Grinblat, "Generating Histories," in *Procedural Storytelling in Game Design* (CRC Press).
