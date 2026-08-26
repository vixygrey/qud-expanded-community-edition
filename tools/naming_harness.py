#!/usr/bin/env python3
"""Resolve Qud's name generation against a candidate `Naming.xml` fragment, without the game.

Every claim this repository makes about name generation was read out of `Assembly-CSharp.dll`.
Reading control flow is not the same as watching it run, and #146 is what that costs — three
routes looked equally live until something measured settled it. This tool is the measurement.

It reimplements the three pieces of `XRL.Names` that decide what a creature is called:

1. **The loader** (`NameStyles.LoadNamingNode` and below). `Load="Merge"` is read off `<naming>`
   and inherited downward by every level via `Reader.GetAttribute("Load") ?? LoadMode`. Without
   it, `LoadNameStylePrefixesNode` calls `style.Prefixes.Clear()` — a fragment that forgets the
   attribute does not add to vanilla's 29 prefixes, it **deletes them**. That is charter rule 1's
   failure mode, and `--fragment` will show it as a pool that shrank.

2. **Scope matching** (`NameScope.ApplyTo`). Every field is an exact-equality filter, `Type`
   included, which is why a `Type="Site"` call can never reach a person-name scope.

3. **Style selection** (`NameStyles.Generate`). Combining styles are drawn by Priority weight,
   and entries at Priority <= 0 are **skipped entirely**. If every combining style sits at
   Priority 0, the total is zero and the game returns the literal string `NameGenFail<n>` as the
   creature's name. Vanilla survives this only because Qudish is the sole `General`-scope
   namestyle in the file, which takes a different branch.

What it does not do: templates, honorifics, epithets, hyphenation, two-name rolls, or `Base=`
delegation beyond noting it. Those do not affect which pool a name is drawn from, which is the
question this tool exists to answer.

Usage:
    python3 tools/naming_harness.py                        # vanilla baseline
    python3 tools/naming_harness.py --fragment PATH        # baseline + fragment, with pool deltas
    python3 tools/naming_harness.py --fragment PATH --check # run the scenario battery, exit 1 on failure
    python3 tools/naming_harness.py --fragment PATH --sample "Species=human,Gender=female"
"""

from __future__ import annotations

import argparse
import os
import random
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

# Steam on macOS. The game data is under CoQ.app/Contents/Resources/Data — NOT under
# CoQ_Data/StreamingAssets, which contains only DLC and is an easy wrong turn.
DEFAULT_GAME_PATHS = [
    "~/Library/Application Support/Steam/steamapps/common/Caves of Qud/CoQ.app/Contents/Resources/Data/StreamingAssets/Base",
    "~/.steam/steam/steamapps/common/Caves of Qud/CoQ_Data/StreamingAssets/Base",
    "C:/Program Files (x86)/Steam/steamapps/common/Caves of Qud/CoQ_Data/StreamingAssets/Base",
]

# NameScope fields, in ApplyTo's own order. All are exact equality against the context EXCEPT
# Mutation, which ApplyTo tests as membership of the creature's mutation list:
#     if (!Mutation.IsNullOrEmpty() && (Mutations == null || !Mutations.Contains(Mutation)))
# Omitting it is not a harmless simplification. `Two-Headed` is scoped Mutation="Two-Headed" at
# Priority 300 with Combine="false", so a harness that never applies the filter has it win every
# single lookup.
SCOPE_FILTERS = (
    "Type",
    "Special",
    "Tag",
    "Gender",
    "Genotype",
    "Subtype",
    "Species",
    "Culture",
    "Faction",
    "Region",
    "Mutation",
)

# Context key holding the creature's mutations, as a comma-separated list.
MUTATIONS = "Mutation"

NAMEGENFAIL = "<NameGenFail>"


class _Always:
    """An rng whose rolls always succeed, for asking 'would this match if Chance passed?'"""

    @staticmethod
    def randrange(_n):
        return 0


_ALWAYS = _Always()


def find_game(explicit: str | None) -> Path | None:
    for candidate in ([explicit] if explicit else []) + DEFAULT_GAME_PATHS:
        if not candidate:
            continue
        p = Path(os.path.expanduser(candidate))
        if (p / "Naming.xml").is_file():
            return p
    return None


@dataclass
class Scope:
    name: str = ""
    priority: int = 0
    chance: int = 100
    combine: bool = False
    filters: dict[str, str] = field(default_factory=dict)

    def applies(
        self, ctx: dict[str, str | None], rng: random.Random | None = None
    ) -> bool:
        """Mirror of NameScope.ApplyTo.

        `Type` is compared even when both sides are None. `Chance` is the last thing ApplyTo
        evaluates (`return Chance.in100()`); with `rng` None a scope below 100 is treated as not
        applying, so the deterministic report describes the ordinary case rather than a coin
        flip. `select` records those separately so they are never silently dropped.
        """
        if self.filters.get("Type") != ctx.get("Type"):
            return False
        special = self.filters.get("Special")
        if (special or ctx.get("Special")) and special != ctx.get("Special"):
            return False
        for key in SCOPE_FILTERS:
            if key in ("Type", "Special", MUTATIONS):
                continue
            want = self.filters.get(key)
            if want and ctx.get(key) != want:
                return False
        want = self.filters.get(MUTATIONS)
        if want:
            have = (ctx.get(MUTATIONS) or "").split(",")
            if want not in [m.strip() for m in have]:
                return False
        if self.chance < 100:
            return rng is not None and rng.randrange(100) < self.chance
        return True


@dataclass
class Style:
    name: str
    fmt: str = "AsIs"
    base: str | None = None
    scopes: list[Scope] = field(default_factory=list)
    # Each pool is an ordered list of [syllable, weight], mirroring List<NameElement>.
    prefixes: list[list] = field(default_factory=list)
    infixes: list[list] = field(default_factory=list)
    postfixes: list[list] = field(default_factory=list)
    prefix_amount: str = "0"
    infix_amount: str = "0"
    postfix_amount: str = "0"

    def check_apply(
        self, ctx: dict[str, str | None], rng: random.Random | None = None
    ) -> Scope | None:
        """Mirror of NameStyle.CheckApply — highest-priority matching scope within this style."""
        best = None
        for s in self.scopes:
            if s.applies(ctx, rng) and (best is None or s.priority > best.priority):
                best = s
        return best

    def chancy(self, ctx: dict[str, str | None]) -> list[Scope]:
        """Scopes that would match but for a Chance below 100 — reported, never hidden."""
        return [
            s for s in self.scopes if s.chance < 100 and s.applies(ctx, rng=_ALWAYS)
        ]


def _pool_node(style: Style, tag: str) -> tuple[list, str]:
    return {
        "prefixes": (style.prefixes, "prefix_amount"),
        "infixes": (style.infixes, "infix_amount"),
        "postfixes": (style.postfixes, "postfix_amount"),
    }[tag]


def load_naming(
    path: Path, styles: dict[str, Style], order: list[str], is_mod: bool
) -> None:
    """Mirror of NameStyles.ProcessNamingXmlFile. Mutates `styles` and `order` in place.

    `order` matters: NameStyleList is iterated in load order, and selection's `flag` bookkeeping
    is order-sensitive. Base data sorts before mods (DataFile.CompareTo), always.
    """
    root = ET.parse(path).getroot()
    if root.tag != "naming":
        raise SystemExit(f"{path}: root is <{root.tag}>, expected <naming>")
    inherited = root.get("Load") if is_mod else None

    for styles_node in root:
        if styles_node.tag != "namestyles":
            continue
        mode = (styles_node.get("Load") if is_mod else None) or inherited
        for node in styles_node:
            if node.tag != "namestyle":
                continue
            _load_style(
                node,
                styles,
                order,
                is_mod,
                (node.get("Load") if is_mod else None) or mode,
            )


def _load_style(node, styles, order, is_mod, mode) -> None:
    name = node.get("Name")
    if name is None:
        raise SystemExit("namestyle tag had no Name attribute")

    style = styles.get(name)
    if style is not None:
        if not is_mod:
            # MetricsManager.LogError("duplicate name style") — vanilla's second one is dropped.
            return
        if mode != "Merge":
            # LoadNameStyleNode's replacement branch removes the old style from _NameStyleList,
            # builds a fresh one, and puts it in _NameStyleTable — but never adds it back to the
            # list. Generate iterates the LIST. So a redeclaration without Load="Merge" does not
            # merely clear a vanilla style's pools: it removes the style from name generation
            # entirely, surviving only for `Base=` lookups. Doing this to Qudish takes every
            # procedurally named human in the game with it.
            order.remove(name)
            style = Style(name=name)
            styles[name] = style
    else:
        style = Style(name=name)
        styles[name] = style
        order.append(name)

    if node.get("Base"):
        style.base = node.get("Base")
    if node.get("Format"):
        style.fmt = node.get("Format")

    for child in node:
        child_mode = (child.get("Load") if is_mod else None) or mode
        if child.tag in ("prefixes", "infixes", "postfixes"):
            pool, amount_attr = _pool_node(style, child.tag)
            if is_mod and child_mode != "Merge":
                pool.clear()
            if child.get("Amount"):
                setattr(style, amount_attr, child.get("Amount"))
            for el in child:
                _load_element(
                    el, pool, is_mod, (el.get("Load") if is_mod else None) or child_mode
                )
        elif child.tag == "scopes":
            for el in child:
                if el.tag != "scope":
                    continue
                style.scopes.append(
                    Scope(
                        name=el.get("Name", ""),
                        priority=int(el.get("Priority", "0")),
                        chance=int(el.get("Chance", "100")),
                        combine=el.get("Combine") == "true",
                        filters={
                            k: v for k, v in el.attrib.items() if k in SCOPE_FILTERS
                        },
                    )
                )


def _load_element(el, pool: list, is_mod: bool, mode: str | None) -> None:
    """Mirror of LoadNameStylePrefixNode. A merged element already present is updated, not re-added."""
    name = el.get("Name")
    if name is None:
        raise SystemExit(f"{el.tag} tag had no Name attribute")
    existing = next((e for e in pool if e[0] == name), None)
    in_place = False
    if is_mod and existing is not None:
        if mode != "Merge":
            pool.remove(existing)
            existing = None
        else:
            in_place = True
    entry = existing if existing is not None else [name, 1]
    if el.get("Weight"):
        entry[1] = int(el.get("Weight"))
    if not in_place:
        pool.append(entry)


def select(
    styles: dict[str, Style],
    order: list[str],
    ctx: dict[str, str | None],
    rng: random.Random | None = None,
):
    """Mirror of NameStyles.Generate's style selection. Returns (candidates, winner, chancy).

    A winner of NAMEGENFAIL means every combining candidate sat at Priority <= 0, so the
    weighted draw had nothing to pick and the game falls through to "NameGenFail<n>".

    `chancy` lists (style name, scope) pairs held back only by a Chance below 100 — vanilla's
    Two-Headed sits at Priority 300 Chance 15, and a report that omitted it would be describing
    a game that does not exist.
    """
    chosen: list[tuple[Style, Scope]] = []
    chancy: list[tuple[str, Scope]] = []
    flag = True
    for name in order:
        style = styles[name]
        chancy += [(name, sc) for sc in style.chancy(ctx)]
        scope = style.check_apply(ctx, rng)
        if scope is None:
            continue
        if scope.combine and flag:
            chosen.append((style, scope))
            continue
        ok = True
        for _, other in chosen:
            if (
                not scope.combine or not other.combine
            ) and other.priority > scope.priority:
                ok = False
                break
        if ok:
            chosen = [(style, scope)]
            flag = scope.combine

    if len(chosen) == 1:
        return chosen, chosen[0][0].name, chancy
    if not chosen:
        # Generate's `case 0: break;` falls through to the same return as an empty weighted draw.
        # Callers passing FailureOkay get null instead, but the default path — and everything a
        # player sees — gets the literal string.
        return chosen, NAMEGENFAIL, chancy
    total = sum(s.priority for _, s in chosen if s.priority > 0)
    if total <= 0:
        return chosen, NAMEGENFAIL, chancy
    return chosen, None, chancy  # >1 live candidate; see `shares()` for the split


def shares(chosen: list[tuple[Style, Scope]]) -> dict[str, float]:
    """The Priority-weighted split among candidates. Priority <= 0 is skipped, not weighted."""
    if len(chosen) == 1:
        return {chosen[0][0].name: 1.0}
    total = sum(s.priority for _, s in chosen if s.priority > 0)
    if total <= 0:
        return {}
    return {st.name: sc.priority / total for st, sc in chosen if sc.priority > 0}


def roll(amount: str, rng: random.Random) -> int:
    """Qud's "1", "0-2" amount spec."""
    if "-" in amount:
        lo, hi = amount.split("-", 1)
        return rng.randint(int(lo), int(hi))
    return int(amount)


def draw(style: Style, rng: random.Random) -> str:
    def pick(pool):
        live = [e for e in pool if e[1] > 0]
        if not live:
            return ""
        total = sum(e[1] for e in live)
        n = rng.randrange(total)
        acc = 0
        for syl, w in live:
            acc += w
            if n < acc:
                return syl
        return ""

    out = "".join(pick(style.prefixes) for _ in range(roll(style.prefix_amount, rng)))
    out += "".join(pick(style.infixes) for _ in range(roll(style.infix_amount, rng)))
    out += "".join(
        pick(style.postfixes) for _ in range(roll(style.postfix_amount, rng))
    )
    return out.title() if style.fmt == "TitleCase" else out


def parse_ctx(spec: str) -> dict[str, str | None]:
    ctx: dict[str, str | None] = {k: None for k in SCOPE_FILTERS}
    for pair in filter(None, (p.strip() for p in spec.split(","))):
        key, _, value = pair.partition("=")
        key = key.strip()
        if key not in SCOPE_FILTERS:
            raise SystemExit(
                f"unknown context field {key!r}; expected one of {', '.join(SCOPE_FILTERS)}"
            )
        ctx[key] = value.strip() or None
    return ctx


def ascii_violations(styles: dict[str, Style]) -> list[tuple[str, str]]:
    """Vanilla is 3,074 syllables for 3,074 ASCII. Diacritics risk Qud's tileset font."""
    bad = []
    for style in styles.values():
        for pool in (style.prefixes, style.infixes, style.postfixes):
            for syl, _ in pool:
                if any(ord(c) > 127 for c in syl):
                    bad.append((style.name, syl))
    return bad


# The claims this repository makes about #184's design, as executable assertions. Each is a
# (label, context, expected winning namestyle) triple. NAMEGENFAIL means the game would return
# a literal "NameGenFail<n>" as the name.
#
# There is no player scenario here, and that is the finding rather than an omission.
# GenerateRandomPlayerName calls NameMaker.MakeName(null, null, Type) -- For is null, so
# Generate never populates Gender, Species or Tag, and the player's random name is drawn
# gender-blind from Qudish no matter what these namestyles say. Reaching it needs a handler on
# BOOTEVENT_GENERATERANDOMPLAYERNAME, which is separate work.
SCENARIOS = [
    ("female human villager", "Species=human,Gender=female", "Vixy_Qudish Feminine"),
    ("male human villager", "Species=human,Gender=male", "Qudish"),
    ("nonspecific villager", "Species=human,Gender=nonspecific", "Vixy_Qudish Neutral"),
    (
        "neuterperson villager",
        "Species=human,Gender=neuterperson",
        "Vixy_Qudish Neutral",
    ),
    ("female snapjaw", "Species=snapjaw,Gender=female,Faction=Snapjaws", "Snapjaw"),
    ("female Templar", "Species=human,Gender=female,Faction=Templar", "Templar"),
    (
        "female Barathrumite",
        "Species=human,Gender=female,Faction=Barathrumites",
        "Barathrumite",
    ),
    ("female bear", "Species=bear,Gender=female,Faction=Beasts", "Animal"),
    ("hindren third gender", "Species=human,Gender=hartind", "Qudish"),
    ("a site name", "Type=Site,Culture=Qudish", "Qudish Site"),
]

VANILLA_POOLS = {"Qudish": (29, 20, 24)}


def pools_of(style: Style) -> tuple[int, int, int]:
    return len(style.prefixes), len(style.infixes), len(style.postfixes)


def report_pools(styles, base_pools, fragment: bool) -> list[str]:
    lines, problems = [], []
    watch = sorted(
        set(list(VANILLA_POOLS) + [n for n in styles if n.startswith("Vixy_")])
    )
    lines.append(
        f"  {'namestyle':28} {'prefixes':>18} {'infixes':>16} {'postfixes':>18}"
    )
    for name in watch:
        if name not in styles:
            continue
        now = pools_of(styles[name])
        was = base_pools.get(name)
        cells = []
        for i in range(3):
            if was is None:
                cells.append(f"{now[i]:>10}")
            else:
                delta = now[i] - was[i]
                mark = "!!" if delta < 0 else "  "
                cells.append(f"{was[i]:>5} -> {now[i]:<4}{mark}")
                if delta < 0:
                    problems.append(
                        f"{name}: {('prefixes', 'infixes', 'postfixes')[i]} SHRANK "
                        f'{was[i]} -> {now[i]} — the fragment is missing Load="Merge"'
                    )
        lines.append(f"  {name:28} " + " ".join(f"{c:>16}" for c in cells))
    return lines, problems


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--game", help="path to StreamingAssets/Base")
    ap.add_argument(
        "--fragment", help="candidate mod Naming.xml to load on top of vanilla"
    )
    ap.add_argument(
        "--check",
        action="store_true",
        help="run the scenario battery; exit 1 on failure",
    )
    ap.add_argument(
        "--sample",
        help='context to draw sample names for, e.g. "Species=human,Gender=female"',
    )
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    game = find_game(args.game)
    if game is None:
        print(
            "error: could not find Caves of Qud. Pass --game PATH to StreamingAssets/Base\n"
            "       (on macOS this lives inside CoQ.app/Contents/Resources/Data, not under\n"
            "        CoQ_Data/StreamingAssets, which holds only DLC).",
            file=sys.stderr,
        )
        return 2

    styles: dict[str, Style] = {}
    order: list[str] = []
    load_naming(game / "Naming.xml", styles, order, is_mod=False)
    base_pools = {n: pools_of(s) for n, s in styles.items()}
    print(
        f"vanilla: {len(styles)} namestyles, "
        f"{sum(sum(pools_of(s)) for s in styles.values()):,} syllables  [{game}]"
    )

    for name, expected in VANILLA_POOLS.items():
        if base_pools.get(name) != expected:
            print(
                f"  note: {name} pools are {base_pools.get(name)}, not the {expected} this "
                f"repository documents — vanilla has changed."
            )

    if args.fragment:
        load_naming(Path(args.fragment), styles, order, is_mod=True)
        print(f"\nafter {args.fragment}:")
        lines, problems = report_pools(styles, base_pools, fragment=True)
        print("\n".join(lines))
    else:
        problems = []

    bad = ascii_violations(styles)
    if bad:
        problems += [f"non-ASCII syllable {syl!r} in {name}" for name, syl in bad]

    failures = list(problems)
    if args.check:
        print("\nscenarios:")
        for label, spec, expected in SCENARIOS:
            ctx = parse_ctx(spec)
            chosen, winner, chancy = select(styles, order, ctx)
            split = shares(chosen)
            if winner is None and split:
                winner = max(split, key=split.get)
            got = winner or "(none)"
            ok = got == expected
            detail = ""
            if len(split) > 1:
                detail = "   split: " + ", ".join(
                    f"{k} {v:.0%}" for k, v in sorted(split.items())
                )
            print(f"  {'PASS' if ok else 'FAIL'}  {label:24} -> {got}{detail}")
            for cname, sc in chancy:
                print(
                    f"        ...unless {cname} fires ({sc.chance}% chance, "
                    f"Priority {sc.priority})"
                )
            if not ok:
                failures.append(f"{label}: expected {expected}, got {got}")

    if args.sample:
        ctx = parse_ctx(args.sample)
        chosen, winner, _ = select(styles, order, ctx)
        split = shares(chosen)
        rng = random.Random(args.seed)
        print(f"\nsamples for {args.sample}:")
        if not chosen:
            print("  (no style matches this context)")
        for name, share in sorted(split.items(), key=lambda kv: -kv[1]):
            names = ", ".join(draw(styles[name], rng) for _ in range(8))
            print(f"  {name:28} {share:>5.0%}  {names}")

    if failures:
        print("\nFAILURES:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("\nok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
