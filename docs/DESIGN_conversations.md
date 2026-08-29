# Living Conversations — design doc

**Status:** spec, no code written
**Target:** Caves of Qud 2.0.211.x
**Headline:** a large share of what you want is **pure XML**. The engine already
supports varying responses and conditional options — vanilla just uses them sparingly.

---

## 1. Why Tam feels static — measured

Tam's entire conversation, verbatim from `Conversations.xml`, is **four nodes**:

```xml
<conversation ID="Tam">
  <start ID="Welcome">
    <text>=player.apparentSpecies=? We are greeted! What do you desire?</text>
    <choice Target="WhoIsTam">I am =name=. Who are you?</choice>
    <choice Target="Joppa">Do you live here?</choice>
    <choice Target="AboutTheDromad">What kind of creature are you?</choice>
    <choice Target="End">I desire nothing. Live and drink.</choice>
  </start>
  <node ID="WhoIsTam" Inherits="Welcome"> … </node>
  <node ID="Joppa" Inherits="Welcome"> … </node>
  <node ID="AboutTheDromad"> … </node>
</conversation>
```

Nothing is conditional. Nothing varies. Of course it's identical at hour 60 — it's identical
by construction.

**But that's a content choice, not an engine limit**, and two vanilla mechanisms prove it.

### Mechanism A — `~` gives you random line variants, free

Warden Yrame's single `<text>` block holds **nine** alternatives separated by `~`:

```xml
<text>
  Welcome a-Joppa, friend. …~
  Elder's over my right shoulder, chemist a-left. …~
  Live and drink, yonderling.~
  {{emote|*Yrame grunts.*}}~
  {{emote|*Yrame nods.*}}~
  What follows, then?~
  Got an eyeful, heh?~
  Well. They en't ended you yet.
</text>
```

One of these is picked per visit. **This alone delivers "ask again next week, get a different
answer" with zero code.** Tam has one line where Yrame has nine.

### Mechanism B — conditionals are everywhere already

Counted across `Conversations.xml`:

| Condition | Uses | |
|---|---|---|
| `IfHaveActiveQuest` | 123 | `IfHaveState` | 94 |
| `IfFinishedQuest` | 78 | `IfHaveBlueprint` | 54 |
| `IfNotHaveQuest` | 48 | `IfFinishedQuestStep` | 48 |
| `IfHindriarch` | 45 | `IfHaveQuest` | 44 |
| `IfNotFinishedQuest` | 32 | `IfTestState` | 30 |
| `IfNotHaveState` | 27 | `IfLastChoice` | 11 |
| `IfHaveSecret` | 6 | `IfWearingBlueprint` | 3 |
| `IfNotHavePart` | 2 | `IfLevelLessOrEqual` | 2 |

`IfHaveState` / `IfNotHaveState` / `IfTestState` are the important trio — arbitrary
conversation state the mod can set and read. Combined with `Conversation.TryGetState` /
`HasState` in the assembly, that's a general-purpose flag system already wired up.

**Conclusion:** tier this mod. Most of it is XML. Only genuinely time-and-world-derived
content needs C#.

---

## 2. Design: three tiers, ship in order

### Tier 1 — variation (pure XML, no conditions)

Give thin NPCs the Yrame treatment: `~`-separated alternates on greetings and on every
existing answer. Tam saying something slightly different each visit fixes most of the
"frozen in amber" feeling for a fraction of the effort.

**This is the whole first release.** It is unglamorous and it is the highest ratio of
perceived improvement to work in the entire document.

### Tier 2 — conditional options (pure XML)

Add choices gated on state the game already tracks:

- `IfFinishedQuest` — Tam reacts to you having resolved Joppa's problems
- `IfHaveBlueprint` / `IfWearingBlueprint` — he notices what you're carrying or wearing
- `IfLevelLessOrEqual` — a different register for a novice than for someone dangerous
- `IfHaveSecret` — he responds to what you know

Still zero code. This is where NPCs start feeling like they can see you.

### Tier 3 — dynamic content (C#)

The part that actually needs code: **"have you heard anything?"** producing answers derived
from the live world rather than a fixed pool.

Sources already available:
- The player's kill and faction reputation data (see `API_VERIFICATION.md`)
- The historic record — `HistoricEntity`, and the player's own entity via
  `QudHistoryFactory.RequirePlayerEntity()`
- Zone and settlement state near the speaker
- Elapsed in-game time since the last conversation, stored as conversation state

Implemented as an `IConversationPart` — there are 61 shipped examples in
`XRL.World.Conversations.Parts`, and `IConversationElement` exposes `Prepare`,
`GetDisplayText`, `WantEvent` and `HandleEvent`. Adding a part that rewrites node text at
display time is the documented shape of this.

---

## 3. What "dynamic" should actually mean

A caution, because this is where the idea can go wrong.

**Rumours should be about things that are true.** If Tam says "traders were attacked near the
Rustwells" and nothing happened there, the mod has generated noise — and worse, it teaches
the player to ignore NPC dialogue, which is the opposite of the goal. Every generated line
should reference something real: a faction you have actually angered, a settlement that
actually exists, a creature you actually killed nearby.

That is the same **derive, don't sample** rule as `lore-expansion`'s ground rule G1, and it
applies here for the same reason.

Good sources, in rough order of how grounded they are:

1. **The player's own deeds** — "they say you put down the croc at the wells." Guaranteed
   true, and flattering in a way that lands.
2. **Faction standing** — "the Templar have been asking after someone of your description."
   True, checkable, and it makes reputation legible for once.
3. **Nearby settlements and their generated history** — villages already carry generated
   events via the same machinery as sultans.
4. **Time and weather** — cheapest, weakest, but fine as filler between the above.

**Avoid** inventing events wholesale. A rumour mill that fabricates is worse than silence.

---

## 4. Scope control

The temptation is to rewrite everyone. Don't. Pick a small cast and do them properly:

- **Tam** (four nodes, a merchant you revisit constantly) — the obvious pilot
- **Elder Irudad** — high narrative weight
- **Warden Yrame** — already has variant lines, so a good calibration reference
- **Mehmet** — early and frequently revisited

Four NPCs done well beats forty with one extra line each. If Tier 1 works on these, expanding
is mechanical.

---

## 5. File layout

```
QudLivingConversations/
├── manifest.json
├── Conversations.xml            # root <conversations>; Tier 1 + Tier 2
└── Scripts/                     # Tier 3 only - omit entirely for the first release
    ├── RumorPart.cs             # IConversationPart, rewrites text at display
    └── RumorSources.cs          # derive lines from deeds / reputation / history
```

Shipping Tier 1 with **no `Scripts/` directory at all** means no mod-approval prompt, same as
the naming and creature mods.

---

## 6. The blocking unknown

**Does a mod's `<conversation ID="Tam">` merge into vanilla Tam, or replace it?**

Qud's XML pipeline aggregates by root element and merges records by identity — that's how
`ObjectBlueprints.xml` works with `Name`. Conversations plausibly merge on `ID` the same way,
but I could not confirm it from metadata, and the two outcomes are very different:

- **Merges** → add nodes and choices surgically. Ideal.
- **Replaces** → you must restate Tam's whole conversation, and you now conflict with every
  other mod that touches Tam.

**Test this first, with one node on one NPC, before authoring anything.** It determines the
whole shape of the mod. If it replaces, the fallback is Tier 3-style parts injecting nodes
programmatically, which is more robust against conflicts anyway.

---

## 7. Build order

1. **Resolve §6** — one added line on Tam. Merge or replace?
2. Tier 1 on the four pilot NPCs — `~` variants everywhere.
3. Tier 2 — conditional choices on state that already exists.
4. Play for a while. Decide whether Tier 3 is still wanted; Tiers 1–2 may have solved it.
5. Tier 3, deeds-derived rumours first — the most grounded source and the most satisfying.

---

## Sources

- `StreamingAssets/Base/Conversations.xml` (647 KB), `HiddenConversations.xml` (105 KB)
- `Assembly-CSharp.dll` metadata — `XRL.World.Conversations.*` (61 parts,
  `IConversationPart`, `IConversationElement`, `Conversation.TryGetState/HasState`)
