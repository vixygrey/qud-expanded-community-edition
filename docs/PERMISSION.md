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
| **Crow**, ***chirps*** | Contributors named on the Workshop page |

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

`workshop.json` in this folder still carries `"WorkshopId": 1134036260` — Mura's original item.
Because this fork publishes separately (§5), **that field must be cleared before the first
upload**, or Qud's uploader will target Mura's page instead of creating a new item. The
`Description`, `Title`, and `ImagePath` fields all need replacing too; the description currently
holds Mura's pre-handoff text asking that the mod not be forked.

See `FEATURES.md` §10 row 0b.
