# What you may reuse, and from whom

Short version: **the mod is Apache-2.0 (code) and CC BY 4.0 (content), inherited work included —
Mura agreed to those terms. The 18 subtype sprites are Noble Lark's and are not covered yet; I've
asked him.**

GitHub shows this repository as "Apache-2.0", which is now accurate for everything except the
sprites. [`NOTICE`](NOTICE) carries that one exception, and Apache-2.0 §4(d) makes `NOTICE` travel
with any redistribution — so the caveat can't get separated from the code it qualifies.

## The split

| What | Licence | Where |
|---|---|---|
| C# in `mod/Scripting/`, and the tooling in `tools/` and `.github/` | **Apache-2.0** | [`LICENSE`](LICENSE) |
| XML data, map patches, documentation — my contributions | **CC BY 4.0** | [`LICENSE-CONTENT`](LICENSE-CONTENT) |
| Everything in the `upstream-2.2` tag | **Apache-2.0 / CC BY 4.0** — Mura agreed on 17 Aug 2026 | [`docs/PERMISSION.md`](docs/PERMISSION.md) §8 |
| `mod/preview.png`, `tools/preview-base.png` | Same — Mura's artwork, Mura's grant | [`docs/PERMISSION.md`](docs/PERMISSION.md) §8 |
| **The 18 subtype sprites** | **Noble Lark's. Not covered.** Used with credit; ask him before reusing | [`docs/PERMISSION.md`](docs/PERMISSION.md) §8.2 |

Code under Apache-2.0 rather than MIT deliberately: Apache has a `NOTICE` file that downstream
**must** reproduce, and MIT's attribution requirement only reaches the source. Credit that survives
into a redistribution is the whole point here.

## How to attribute

CC BY 4.0 §3(a) lets me specify how attribution is given, so:

> Qud Expanded Community Edition by VixyGrey, continuing Caves of Qud Expanded by Mura.
> Subtype sprites by Noble Lark (a.k.a. chirps).

Keep [`NOTICE`](NOTICE) intact and you've satisfied both licences at once.

## Why the sprites are the one exception

Mura's grant was always broad — *"update, fork, and generally do with as they please, all I ask is
that you give credit where due"* — but it named no licence, so nobody downstream had defined terms.
I asked whether it could be formalised, and Mura agreed to Apache-2.0 and CC BY 4.0
([`docs/PERMISSION.md`](docs/PERMISSION.md) §8). That covers their work in this mod.

It doesn't cover Noble Lark's sprites, and Mura said as much:

> I would reach out to them directly for confirmation just to be sure, but I don't think that will
> be an issue.

That's the right instinct. Mura naming the sprites inside the original grant shows Mura believed
they were theirs to open up, but **Noble Lark has never said so himself**, and an artist's work
shouldn't be relicensed on someone else's say-so. I've asked Noble Lark directly; Mura offered to
follow up if he doesn't reply.

Until he answers, the sprites are his, used with credit. If you want to reuse them, ask him.

## Contributions

Anything you contribute is offered under the same terms — Apache-2.0 for code, CC BY 4.0 for
content — so the project stays consistently licensed. You keep your copyright; you're granting a
licence, not signing it away. You'll also be credited by name in `NOTICE`, the README and the
Workshop description, in the pull request that merges your work.

## Not legal advice

I'm a modder, not a lawyer. This is my honest description of what I can offer and what I can't. If
you need certainty for something that matters, get advice — and for the inherited work, ask Mura
directly.
