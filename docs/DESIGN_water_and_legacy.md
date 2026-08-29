# Water-Siblings & Legacy — design doc

**Status:** deep scope, no code written
**Target:** Caves of Qud 2.0.211.x
**Two mods that are better together than apart.**

---

## 0. The connection

These started as separate ideas. They shouldn't be.

Qud is a game about **history and how it gets told**. Sultan histories are procedurally
generated, then mythologised — the wiki notes that tomb inscriptions present events
"with heightened reverence compared to gospel versions, occasionally omitting moral
shortcomings." The game already models the gap between what happened and what gets
remembered.

The water ritual makes NPCs your **water-siblings** — literal kin, who treat you as
family, and whose murder is the game's one true sin (Oathbreaker: −100 to −200
reputation with *every* faction simultaneously).

So:

> **Your water-siblings are the people who would remember you.**
> Kinship is the mechanism by which a dead wanderer becomes history.

That single sentence is the design. Part 1 builds the kinship. Part 2 builds the
remembering. Either works alone; together they close a loop the game has all the parts
for and has never joined up.

---

# PART 1 — The water ritual as a covenant

## 1.1 What it currently is

Verified. You approach a non-hostile legendary creature, say *"Your thirst is mine, my
water is yours,"* and give them their preferred liquid. Then you spend a reputation
budget on a menu:

| Category | Options |
|---|---|
| Social | share secrets, exchange gossip, receive faction secrets |
| Recruit | `12 × (their level − your level) + 200`, min 50 |
| Knowledge | faction skills (prerequisites waived), cooking recipes, tinkering recipes |
| Body | fungal infections, mental mutations (Seekers only), skill points |
| Items | their most valuable item (Consortium/Merchants only) |
| Quest | promises to hermits |

Max 150 reputation gained per creature. Then the interaction is **over, permanently**.

## 1.2 The gap

The ritual is framed as **kinship** and implemented as **a vending machine**.

You become someone's sibling, extract secrets, skills and gear, and never speak to them
again. The obligation runs one way: you can betray them (Oathbreaker), but you can
never be *asked* for anything, and you can never *ask* for anything either. The bond
has no second act.

The lore does enormous work here that the mechanics don't cash. Fixing that requires no
new fiction at all — only mechanics that take the existing fiction seriously.

## 1.3 Design: covenants run both ways

### A. They remember

Water-siblings track what you've done since the ritual and react on re-encounter.
Dialogue keyed to your actual history: factions you've since angered, sultans whose
tombs you've robbed, kin of theirs you've killed. Uses the reputation and kill data the
game already keeps.

Cheapest possible version, and it alone changes how the ritual feels.

### B. Kinship is a network

Water-siblings know each other. Being kin to one should give you standing with *their*
kin — a small reputation bonus with close associates of anyone you've bonded with, and
a matching penalty with their personal enemies.

This makes **who** you share water with a strategic decision instead of a completionist
checklist, and it slots directly into the faction-rivalry system from the difficulty doc.

### C. They ask things of you

Periodically, a water-sibling sends word. Their settlement is threatened; they need a
relic recovered; a rival kin-group has wronged them. Small, generated, optional
requests.

**Refusing has a cost** — not Oathbreaker-scale, but a real cooling of the bond. This is
what makes it a covenant rather than a subscription. Family that only ever gives is not
family.

### D. You can ask things of them

The reciprocal half, and the reason a player opts in:

- **Sanctuary.** Safe rest at their settlement (pairs with the sleep mod — guaranteed
  full rest quality, no ambush roll).
- **Aid.** Call a water-sibling to your location once per long cooldown.
- **Supply.** They'll part with water, food, or ammunition in need.
- **Word.** They tell you what they've heard — a lead on a historic site, a rumour about
  a nearby lair.

Each costs relationship weight. The bond is a resource you can spend down.

### E. Deepen over time

Sharing water with the same creature again strengthens the bond by a tier rather than
doing nothing. Gives long-lived characters a reason to return to people they know.

## 1.4 What this changes about play

Right now the optimal water-ritual strategy is **bond with everyone, extract everything,
never return**. Under this design, kinship becomes a network you maintain, with
obligations, favours, and enemies attached. It converts the game's most thematically
loaded mechanic from a menu into a relationship — and it does it entirely with fiction
the game already asserts.

---

# PART 2 — Legacy: the wanderer enters history

## 2.1 What Qud already has

This is the part that makes the idea viable rather than fantasy. Qud ships a full
**procedural mythic-biography engine** — there's an academic paper on it (Grinblat,
"Generation of Mythic Biographies in Caves of Qud").

Per playthrough it generates five random sultans plus Resheph, each with **10–22
events** in a fixed dramatic structure:

1. Origin (born heir, or found as an infant)
2. Eight core life events, drawn from **17 event types** — challenges, battles,
   marriages, crafted relics, faction dealings, chariot incidents
3. Ascension
4. Regional coverage events
5. Death

Vocabulary shifts between Early and Late sultanate periods. And it manifests
*physically* in the world:

- **Relics** crafted during events, lost and recoverable
- **Cities renamed** after sultans
- **Monuments** at event sites
- **Faction dispositions** — loved, favoured, hated — that shift reputation
- **Eight historic sites** per playthrough, tiered by period, each with a relic chest
- **Cults** inhabiting those sites
- **Murals and gospels** as the discovery mechanism

## 2.2 The gap

Permadeath, and **zero continuity of any kind**. You die and the world forgets
completely.

Meanwhile the game contains a bespoke engine for turning a life into myth, monuments,
relics and cults — pointed exclusively at six fictional sultans, and never at the
player.

## 2.3 Design: your dead character becomes a minor historical figure

On death, the mod records the run: notable kills, zones reached, water-siblings bonded,
factions loved and hated, items crafted or named, quests completed, and how you died.

In the **next** world, that character appears as a historical figure — not a sultan, but
a **wanderer**: a smaller, more recent, more disputed kind of legend.

### Manifestations, in ascending order of ambition

**Tier 1 — Gospel**
Text entries discoverable the same way sultan lore is: statues, inscriptions, and NPC
dialogue. Written in the game's existing register, mythologising what actually
happened. You killed a Girshling at level 3 and died to a snapjaw; the gospel records
that you "slew the beast of the deep places and fell to a horde without number."

**The exaggeration is the point.** Qud already models the gap between event and
retelling. Leaning into it is the most authentic thing this mod can do.

**Tier 2 — The grave**
A findable site where you died, in the same region. Contains your remains, and
*sometimes* one or two things you happened to be carrying. Not a cache — a haunting.
The rules governing what may and may not be there are in §2.4, and they are the most
important constraints in this document.

**Tier 3 — deliberately omitted**
An earlier draft had named or crafted items persisting as minor relics. **Cut** — see
§2.4. Authored objects cannot cross between worlds without damaging both.

**Tier 4 — Your kin remember you**
*This is where Part 1 and Part 2 join.* Water-siblings from your previous run — or, if
enough in-world time is asserted, their descendants — recognise your successor's
lineage. A small starting reputation with factions your previous character was loved
by, and hostility from those you wronged.

**Your legacy is carried by the people you shared water with.** That's how oral history
actually works, and it's exactly the fiction Qud already runs on.

**Tier 5 — A cult**
If the previous character was sufficiently notable, a small cult venerating them
appears. Directly parallel to sultan cults, which already exist as a content type.

### Guardrails

- **Legacy is almost pure lore.** The gospel is the deliverable. Material recovery is a
  rare, small garnish — never the reason to engage with the system.
- **Failure should be as interesting as success.** A character who died at level 2 in
  Joppa deserves a gospel too — a joke, a cautionary tale, a footnote. Arguably funnier
  and better than a heroic one.
- **Opt-in.** Some players want a clean slate. Mod option, and a per-character toggle.

---

## 2.4 Grave goods: the authored/incidental rule

This is the constraint the whole material side of the mod hangs on.

### The principle

> **Only *incidental* objects may cross between worlds. Never *authored* ones.**

An **authored** object carries a statement of intent by the previous character. Someone
chose to paint it, engrave it, name it. It means something *because a person made it
mean something*.

An **incidental** object is just what a body happened to be carrying. A dagger, a torch,
some rations, a waterskin. Archaeologically true, narratively mute.

Authored objects cannot cross worlds without breaking something, and they break it in
**two directions at once**:

1. **Forward.** The new world has its own generated history. An engraved object arrives
   with a provenance that history has no room for. It is a foreign authored claim
   sitting inside a world that already decided what it means.
2. **Backward.** Finding it retroactively rewrites the *previous* run in the player's
   head. That run is finished. Its meaning was settled when the character died. An
   object that forces reinterpretation vandalises a memory the player already owns.

The second is the subtler damage and the more serious one. The previous run's meaning
belongs to the player, not to the mod.

### The corollary

**The gospel is the only authored artifact the legacy system may produce.**

That's where the previous character's meaning is allowed to live. If the objects also
speak, there are two narrators competing over the same dead person, and the mute one
wins by accident because it's a thing you can hold. Keeping grave goods silent is what
lets the lore layer stay the single source of truth about who that character was.

### Exclusion list

Never eligible as grave goods:

| Excluded | Why |
|---|---|
| **Painted items** | Authored. A deliberate mark by the previous character. |
| **Engraved items** | Authored, and literally carries text asserting a history. |
| **Named items** (the level-up naming reward) | The most authored object in the game. Worst offender. |
| **Sultan relics / historic-site loot** | Indexed to a *specific generated history*. Its description references a sultan who does not exist in the new world. Same category error as an engraving, but it breaks the fiction louder. |
| **Unique artifacts** | Duplication risk — the new world may generate the same unique. Technical and narrative failure at once. |
| **Quest items** | Obviously. |
| **Installed cybernetics** | Identity-bearing, and a large power spike. |
| **Anything above a tier cap** | See below. |

The sultan-relic exclusion follows directly from the painted/engraved rule and is easy
to miss. Those items are the *most* history-bound objects in the game — they exist
precisely to encode a history that the next world does not have.

### Selection

When a grave is generated:

1. **Roll for goods at all.** Recommend **~40%** of graves contain anything. The other
   60% are bare remains — and the in-world reason is excellent: **Qud is full of
   scavengers.** Most bodies get picked over. That's not a balance excuse, it's just
   true of the setting.
2. If yes, take **1–2 items**, chosen **at random** from the previous inventory — never
   the best, never weighted toward value.
3. Filter the whole exclusion list above.
4. **Cap by tier**, relative to the region the grave sits in. A random pull from a
   late-game inventory could otherwise be a nuclear device sitting in a tier-1 zone.
5. Arrive **unidentified / unexamined**. You don't know what the corpse was carrying
   until you look, which is both truthful and prevents remains becoming a lookup table.
6. Arrive **degraded** where the item supports a damaged state — rusted, worn, low
   charge. Flavour and power limiter in the same stroke. Things left on a body in Qud's
   climate do not come back pristine.

### Why this can't gear you up

Worst case is one or two mid-tier, condition-degraded, randomly selected mundane items,
40% of the time, once per previous run. That is a nice moment, not a supply line. And
because selection is uniformly random rather than value-weighted, **farming is
actively irrational** — you cannot influence what comes back, and a deliberately
sacrificed character is no more likely to leave anything good than an unlucky one.

The system is designed so that the only reliable thing you inherit is the story.

## 2.5 Why this one is worth building

Every other idea in these docs adds a system to Qud. This one **turns Qud's own signature
system on the player**. It requires no new fiction, no balance risk, and no new art. It
takes the thing the game is most celebrated for — procedural mythmaking — and makes it
about you.

---

# 3. Technical feasibility

## 3.1 Cross-run persistence

Legacy needs state that survives character death. Qud mods run with **full privileges**
(the game warns users about this and requires mod approval), so writing a small JSON or
XML file alongside the save should be available — but **verify the sanctioned path and
whether a mod-data API exists** before designing around it.

Keep the file small and versioned. It will outlive several game updates.

## 3.2 Don't inject into the sultan engine

Strong recommendation: **do not** try to add the player as a sixth sultan.

The history generator is deep internal machinery with a fixed structure (five sultans
plus Resheph, tiered historic sites, period vocabulary). Injecting into it means
Harmony patches against exactly the kind of internals that move between builds.

Instead, generate a **parallel record** — "wanderer gospels" — that reuses the *style*
and the *delivery mechanisms* (statues, inscriptions, NPC dialogue) without touching the
generator. Same player-facing effect, a fraction of the fragility. If Qud's own
generator changes, your mod doesn't care.

## 3.3 Harmony exposure

| Feature | Likely needs Harmony? |
|---|---|
| Water-siblings remember / react | No — dialogue and conversation data |
| Kinship network reputation | Probably not, if a reputation hook exists (**unverified**) |
| Requests from kin | No — quest system |
| Calling on kin | No — new abilities |
| Legacy recording on death | Possibly, to hook the death event |
| Wanderer gospels | No, if built as parallel content |
| Grave site placement | No — zone-generation data |

The only likely patch point is the death hook. That's one small postfix, which is the
safest patch category Freehold documents.

## 3.4 Version context

Current release is **2.0.211.50** (July 2026) and the recent cadence is
maintenance-flavoured. A game in maintenance mode is a comparatively **safe** Harmony
target — internals move less than in a game shipping features monthly.

---

# 4. Build order

Both mods have a genuinely tiny viable first version. Start there.

1. **Water-siblings remember (1.3A).** Dialogue reacting to your history. No new systems.
   Ships in days and immediately changes how the ritual feels.
2. **Legacy Tier 1 — gospels.** Record the run on death; surface generated text in the
   next world. No mechanical effect whatsoever. This is the whole idea, proven, at
   minimum risk.
3. **Legacy Tier 2 — the grave.** Your remains, findable. Ship it *without* grave goods
   first — bare remains plus the gospel is already the whole emotional payload. Add the
   40% item roll only once the exclusion filter in §2.4 is written and tested.
4. **Water-sibling favours (1.3D).** Sanctuary first — it's the simplest and pairs with
   the sleep mod.
5. **Kinship network (1.3B)** — once the reputation hook is confirmed.
6. **Requests from kin (1.3C).**
7. **Legacy Tiers 4–5** — kin recognition, cults. (Tier 3, persisting relics, is cut —
   see §2.4.)

Step 2 alone is a complete, shippable, genuinely novel mod that no balance argument can
be made against, because it changes no numbers at all.

---

## Sources

- [Water ritual](https://wiki.cavesofqud.com/wiki/Water_ritual)
- [Sultan histories](https://wiki.cavesofqud.com/wiki/Sultan_histories)
- [Historic site](https://wiki.cavesofqud.com/wiki/Historic_site)
- [Sultan cult](https://wiki.cavesofqud.com/wiki/Sultan_cult)
- [World generation](https://wiki.cavesofqud.com/wiki/World_generation)
- [Grinblat, *Generation of Mythic Biographies in Caves of Qud*](https://www.pcgworkshop.com/archive/grinblat2017subverting.pdf)
- [Reputation](https://wiki.cavesofqud.com/wiki/Reputation)
- [Modding:Harmony](https://wiki.cavesofqud.com/wiki/Modding:Harmony)
- [Maintenance Patch – July 4, 2026](https://freeholdgames.itch.io/cavesofqud/devlog/1574536/maintenance-patch-july-4-2026)
