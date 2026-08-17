# What you may reuse, and from whom

Short version: **my work is Apache-2.0 (code) and CC BY 4.0 (content). Mura's inherited work and
Noble Lark's sprites are not mine to license — ask them.**

GitHub will show this repository as "Apache-2.0" because that's what `LICENSE` contains. That's
accurate for the parts I wrote and not for the whole tree, which is why this file exists and why
[`NOTICE`](NOTICE) carries the same scope statement. Apache-2.0 §4(d) makes `NOTICE` travel with any
redistribution, so the caveat can't get separated from the code.

## The split

| What | Licence | Where |
|---|---|---|
| C# in `mod/Scripting/`, and the tooling in `tools/` and `.github/` | **Apache-2.0** | [`LICENSE`](LICENSE) |
| XML data, map patches, documentation — my contributions | **CC BY 4.0** | [`LICENSE-CONTENT`](LICENSE-CONTENT) |
| Everything in the `upstream-2.2` tag | **Mura's** — permission to fork only | [`docs/PERMISSION.md`](docs/PERMISSION.md) |
| The 18 subtype sprites | **Noble Lark's** | not licensed here |
| `mod/preview.png`, `tools/preview-base.png` | **Mura's** artwork | not licensed here |

Code under Apache-2.0 rather than MIT deliberately: Apache has a `NOTICE` file that downstream
**must** reproduce, and MIT's attribution requirement only reaches the source. Credit that survives
into a redistribution is the whole point here.

## How to attribute

CC BY 4.0 §3(a) lets me specify how attribution is given, so:

> Qud Expanded Community Edition by VixyGrey, continuing Caves of Qud Expanded by Mura.
> Subtype sprites by Noble Lark.

Keep [`NOTICE`](NOTICE) intact and you've satisfied both licences at once.

## Why this isn't simpler

I can only license what I hold. `docs/PERMISSION.md` records Mura's grant — public, explicit, and
generous — but it's **permission to fork with a credit condition**, not a copyright licence with the
right to sublicense. It says nothing about copyright or licensing at all.

So I can't put a licence on their code, and I'm not going to imply otherwise to someone who might
rely on it.

Noble Lark's sprites are a step further removed again. Mura credited them and asked that the credit
carry forward, which I do — but Mura crediting them isn't Mura licensing them, and Noble Lark was
never party to my fork permission.

**This is the strongest position available to me without asking Mura**, and asking is on my list. If
they choose a licence for the original, the scope widens and both this file and `NOTICE` will say
so.

## Contributions

Anything you contribute is offered under the same terms — Apache-2.0 for code, CC BY 4.0 for
content — so the project stays consistently licensed. You keep your copyright; you're granting a
licence, not signing it away. You'll also be credited by name in `NOTICE`, the README and the
Workshop description, in the pull request that merges your work.

## Not legal advice

I'm a modder, not a lawyer. This is my honest description of what I can offer and what I can't. If
you need certainty for something that matters, get advice — and for the inherited work, ask Mura
directly.
