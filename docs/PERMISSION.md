# Fork Permission — Caves of Qud Expanded

Provenance record for the community fork of **Caves of Qud Expanded**
(Steam Workshop ID `1134036260`), originally by **Mura** (`@mura_raven`).

Captured 2026-08-15 by Grey (`VixyGrey13`).

---

## 1. General grant — Workshop description

From the mod's Workshop description (current as of capture):

> Despite my original apprehension, I've decided to make the mod open to the community to update,
> fork, and generally do with as they please, all I ask is that you give credit where due, which
> includes Noble Lark for the subclass sprites.

## 2. General grant — Popular Discussions

> It is indeed open for anyone to update, use, and fork as they want.

And, on the reasoning behind the change:

> I only just made the change, so I don't know that any updates or forks are out there yet. I
> reached a point where I realized I wasn't bothered anymore by the idea of someone else taking
> it over, so I figured it would be best to just open it up for everyone.

## 3. Explicit, individual grant to this fork

Workshop comment thread on the mod page.

**VixyGrey13:**

> @Mura: I'd like permission to fork Caves of Qud Expanded and continue work on it if that's ok?
> Full credit will be given as requested of course!

**Mura [author]** (replying ~5 minutes later):

> @VixyGrey13 it's open to the community now, so feel free to do so, feel free to DM me if you
> have any questions

Screenshot evidence: `permission-mura-workshop-comment.png` (see §5).

---

## 4. The condition attached

The grant is unconditional **except for credit**. Mura names one person explicitly —
**Noble Lark**, for the subtype sprites. The following credits should be carried forward in the
fork's Workshop description and in-repo documentation:

| Person | For |
|---|---|
| **Mura** (`@mura_raven`) | Original mod — creator, years of work |
| **Noble Lark** | All 18 psionic subtype sprites — *named explicitly in the grant* |
| **Scrolldier / Parzival** | Taught Mura to mod Caves of Qud |
| **Arendeth** | Population-table fixes (credited in `2.2 changelog.txt`) |
| **Tyrir** | Found the 2.2 typo batch and an invalid blueprint (credited in `2.2 changelog.txt`) |
| **Crow** | Helped with bug fixes — not a contributor to the mod's content (§8.3) |

> **Names and pronouns.** *chirps* was listed here as a separate contributor until Mura pointed out
> it is **Noble Lark's** Steam name — one person, credited twice. Corrected everywhere in §8.1.
>
> **Mura** uses **any/all pronouns**; this project writes *they/them* for them, which they have not
> asked for but which is the safest of the set to use in writing about someone. **Noble Lark** uses
> **he/him**, per his Discord profile. Getting these right is part of crediting someone properly,
> so they are recorded here rather than left to whoever writes the next paragraph.

Mura also offered an open line for questions via Steam DM, and gave `@mura_raven` on Discord as
the preferred contact in the mod description.

---

## 5. Scope of this fork

This fork will be **released as a separate Workshop item**. It does not take over, replace, or
modify Mura's original page (`1134036260`), which remains theirs. Full credit is given to
everyone listed in §4.

---

## 6. Evidence files

| File | Contents |
|---|---|
| `permission-mura-workshop-comment.png` | Screenshot of the Workshop comment thread showing the request and Mura's `[author]` reply |

Note: the screenshot shows relative timestamps ("56 minutes ago", "1 hour ago") rather than
absolute ones. The capture date at the top of this file is the anchor.

---

## 7. Action required before first upload

✅ **Done (#2).** `WorkshopId` was cleared, and the validation script fails the build if it is
ever set back to `1134036260`. The description, title and credits were rewritten for this fork.

> **Correction (#163).** This section read *"`WorkshopId` is now `0`, so the uploader creates a new
> item"* until the first upload proved otherwise: a zero is a lookup for item zero, not an absent
> id, and the uploader answers *Item not found*. The file was removed so the uploader could write
> it, and the fork's item is **3785441196**. Nothing about Mura's page was ever at risk — the
> danger this section was written against is the *upstream* id, and that guard held.

Original note, kept for the record:

`workshop.json` in this folder still carried `"WorkshopId": 1134036260` — Mura's original item.
Because this fork publishes separately (§5), **that field must be cleared before the first
upload**, or Qud's uploader will target Mura's page instead of creating a new item. The
`Description`, `Title`, and `ImagePath` fields all need replacing too; the description currently
holds Mura's pre-handoff text asking that the mod not be forked.

See `FEATURES.md` §10 row 0b.

---

## 8. Licence approval — Discord, 17 August 2026

This document is append-only, so this section records a later grant rather than editing §1–§3.

I asked Mura on Discord whether the informal grant could be formalised:

**VixyGrey:**

> Quick question for you: You said do as you please with credit. Can I formalise that as Apache-2.0
> license and CC BY 4.0 (creative commons license) so other modders have defined terms — and does it
> cover Noble Lark's sprites?

**Mura:**

> I think that would be fine, I don't know a lot about them but after a quick google search and some
> reading I don't see a problem with them

So **Mura's own work in this mod is licensed Apache-2.0 for code and CC BY 4.0 for content**, the
same terms as my contributions. That closes the gap §1–§3 left open: the earlier grants were broad
in substance but named no licence, so they gave no defined terms for anyone downstream to rely on.

### 8.1 Noble Lark is "chirps" — one person, not two

In the same conversation:

> Also chirps is Noble Lark's steam name, so you can put a.k.a. chirps on the Github, I just noticed
> that.

Every credit list in this project had named **Noble Lark** and **chirps** as separate contributors,
because Mura's original Workshop page listed both. They are the same person. Corrected everywhere,
including `mod/workshop.json`, which ships.

His pronouns are **he/him**, from his Discord profile.

### 8.2 The sprites still need his own confirmation

Mura was explicit that their approval does not settle this:

> I would reach out to them directly for confirmation just to be sure, but I don't think that will
> be an issue. If they don't answer just let me know and I'll reach out as well.
>
> @noblelark is their discord handle

That is the right instinct and I have taken it: Mura naming Noble Lark inside the original grant
shows Mura believed the sprites were theirs to open up, but Noble Lark has never said so himself.

**I have reached out to him.** Until he answers, the 18 subtype sprites in `mod/Textures/Subtypes/`
are *not* covered by the licences here — they remain his, used with credit, exactly as they have
been all along. Mura offered to follow up if Noble Lark does not reply.

### 8.3 Crow helped with bug fixes

After this fork's first release, Mura corrected one line of the credit list:

> Crow (in the credits) helped with bug fixes, they didn't contribute to the mod itself

Crow had been credited here, in `README.md`, in `NOTICE` and in the shipped Workshop description
as a contributor to the original mod, which claims more than they did. Corrected everywhere,
including `mod/workshop.json`, which ships to subscribers.

Mura writes **they** for Crow, so this project does too.

### 8.4 Mura has folded a sub-mod in before — the Saving Joppa precedent

Relevant to #174 and #175, which propose absorbing the Grand Bazaar and the Experience Curve.
Mura's own listing for **Caves of Qud Expanded - Saving Joppa Standalone** (Workshop item
`1461098960`) says:

> As a standalone mod, this mod does not require the base mod, in fact there's no point in
> installing both as it is already incorporated into the base mod.

So consolidation is the original author's own practice, not a departure from it. It is also
partly visible in this fork: four `Raven_` furniture blueprints are declared here identically to
the standalone's copies. The `JoppaRuins` terrain and map are not — see `docs/FEATURES.md` §10.

**This is precedent, not permission.** §8's licence grant is worded as *"their work in this
mod"*, and the Bazaar and the Experience Curve are separate Workshop items. Whether that grant
reaches them is Mura's to say, and the answer belongs in this file when it comes.
