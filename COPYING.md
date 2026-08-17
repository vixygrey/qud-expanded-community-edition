# What you may reuse, and from whom

Short version: **my work is Apache-2.0 (code) and CC BY 4.0 (content). Mura's inherited work and
Noble Lark's sprites are open on Mura's own terms — do what you like, give credit, name Noble Lark
for the sprites.**

GitHub will show this repository as "Apache-2.0" because that's what `LICENSE` contains. That's
accurate for the parts I wrote and not for the whole tree, which is why this file exists and why
[`NOTICE`](NOTICE) carries the same scope statement. Apache-2.0 §4(d) makes `NOTICE` travel with any
redistribution, so the caveat can't get separated from the code.

## The split

| What | Licence | Where |
|---|---|---|
| C# in `mod/Scripting/`, and the tooling in `tools/` and `.github/` | **Apache-2.0** | [`LICENSE`](LICENSE) |
| XML data, map patches, documentation — my contributions | **CC BY 4.0** | [`LICENSE-CONTENT`](LICENSE-CONTENT) |
| Everything in the `upstream-2.2` tag | **Mura's**, opened to the community with credit as the condition | [`docs/PERMISSION.md`](docs/PERMISSION.md) |
| The 18 subtype sprites | **Noble Lark's**, named inside Mura's grant | [`docs/PERMISSION.md`](docs/PERMISSION.md) |
| `mod/preview.png`, `tools/preview-base.png` | **Mura's** artwork, same grant | [`docs/PERMISSION.md`](docs/PERMISSION.md) |

Code under Apache-2.0 rather than MIT deliberately: Apache has a `NOTICE` file that downstream
**must** reproduce, and MIT's attribution requirement only reaches the source. Credit that survives
into a redistribution is the whole point here.

## How to attribute

CC BY 4.0 §3(a) lets me specify how attribution is given, so:

> Qud Expanded Community Edition by VixyGrey, continuing Caves of Qud Expanded by Mura.
> Subtype sprites by Noble Lark.

Keep [`NOTICE`](NOTICE) intact and you've satisfied both licences at once.

## Why the licences stop where they do

Mura's grant is broad. From the Workshop description, recorded in full in
[`docs/PERMISSION.md`](docs/PERMISSION.md):

> I've decided to make the mod open to the community to **update, fork, and generally do with as
> they please**, all I ask is that you **give credit where due, which includes Noble Lark for the
> subclass sprites**.

Said again in the Popular Discussions — *"open for anyone to update, use, and fork as they want"* —
and a third time directly to me when I asked. In substance that's an attribution grant: do what you
like, give credit.

What it isn't is a **named licence**, so its edges are undefined. No warranty disclaimer, no patent
grant, and no explicit statement that I may *sublicense* it.

That last one is the whole reason the licences here cover my contributions and stop. If I put
Apache-2.0 over Mura's code, I'd be telling you that you get Apache rights **from me** — and I was
never explicitly given the power to pass those on. You getting them from Mura's own grant, which is
public and plainly worded, is both more accurate and no less useful to you.

So this is a scoping decision, not a warning. **Reusing the inherited work is almost certainly fine
on Mura's terms.** Read `docs/PERMISSION.md`, give credit, name Noble Lark for the sprites. If you
need certainty rather than "almost certainly", ask Mura — they invited questions and gave contact
details, both recorded there.

I've asked whether they'd like to put a named licence on the original work. If they do, this file
and `NOTICE` will say so and the scope widens.

## Contributions

Anything you contribute is offered under the same terms — Apache-2.0 for code, CC BY 4.0 for
content — so the project stays consistently licensed. You keep your copyright; you're granting a
licence, not signing it away. You'll also be credited by name in `NOTICE`, the README and the
Workshop description, in the pull request that merges your work.

## Not legal advice

I'm a modder, not a lawyer. This is my honest description of what I can offer and what I can't. If
you need certainty for something that matters, get advice — and for the inherited work, ask Mura
directly.
