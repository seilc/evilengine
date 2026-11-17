#!/usr/bin/env python3
"""Print a Discord message (JSON payload) with per-version Game progress from objdiff reports.

Usage: progress.py CUR_DIR [PREV_DIR]
       progress.py --badges OUT_DIR CUR_DIR
A line for the shared engine (files two or more games have) and one for each game's own code (fuzzy-matched code,
objdiff's fuzzy_match_percent, over each game's first version as treemap.py draws them, with its change since
PREV_DIR when it moved, a 🎉 when it passed a multiple of 10% since PREV_DIR, and its matched and total files),
then, with PREV_DIR, the Game files whose match changed in any version, each tagged with its game (and the builds,
when not all of that game's), with the changed functions of the files not yet complete.
A game's Game units are those in the game category plus those under its source folder (ROOTS): a version other than
Rat's lists only its completed objects in configure.py, so the others are in the report without a category.
Files come newly matched first, then rising, then falling, each group by bytes changed (biggest first); more than
COLLAPSE functions of one file now at 100.00% become one count line. The message stops after the last whole file
that fits in MAX_CONTENT, with a count of the files left out.
Optional environment, for the line naming who pushed what: PUSHER (GitHub login), REPO (owner/name), HEAD_SHA,
PREV_SHA, COMMITS (the number of commits pushed).
Prints nothing when nothing changed since PREV_DIR.
With --badges, writes instead a shields.io endpoint badge for each of those lines (shared engine, each game's own
code), OUT_DIR/<line name>.json (`shared-engine.json`, `rat-only-code.json`), for the README (published to GitHub
Pages with treemap.py's image).
Each directory holds <VERSION>_report/report.json, as downloaded from the Build workflow's artifacts.
"""
import json
import os
import sys
from pathlib import Path

GAMES = {"Rat": ["RAT_DEBUG", "RAT_RELEASE", "RAT_MASTERDEBUG", "RAT_MASTER"], "RotU": ["ROTU"]}
ROOTS = {"Rat": "rt", "RotU": "in2"}  # each game's source folder in the unit names (configure.py's game_root)
VERSIONS = [ver for vers in GAMES.values() for ver in vers]
GAME_OF = {ver: game for game, vers in GAMES.items() for ver in vers}
USERNAME = "EvilEngine"
CATEGORY = "game"
ABBREVS = {"RAT_DEBUG": "D", "RAT_RELEASE": "R", "RAT_MASTERDEBUG": "MD", "RAT_MASTER": "M"}
MAX_CONTENT = 1000  # kept short (Discord's own limit is 2000)
COLLAPSE = 3  # more functions of one file now at 100.00% than this become one count line
BADGE_COLORS = ("3987e5", "1fa84f")  # treemap.py's PARTIAL and MATCHED


def func_name(name):
    """A demangled name without its argument list."""
    if name.endswith(" const"):
        name = name[:-len(" const")]
    if not name.endswith(")"):
        return name
    depth = 0
    for i in range(len(name) - 1, -1, -1):
        depth += {")": 1, "(": -1}.get(name[i], 0)
        if depth == 0:
            return name[:i]
    return name


def is_game(unit, ver):
    """A Game unit of ver's game: in the game category, or under the game's source folder."""
    return (CATEGORY in unit.get("metadata", {}).get("progress_categories", [])
            or unit["name"].split("/")[1:2] == [ROOTS[GAME_OF[ver]]])


def load(d, ver):
    p = Path(d) / f"{ver}_report" / "report.json"
    if not p.exists():
        return None
    r = json.loads(p.read_text())
    units = {}
    total = fuzzy = 0.0
    for u in r.get("units", []):
        if not is_game(u, ver):
            continue
        meta = u.get("metadata", {})
        key = u["name"].split("/", 1)[-1]  # without the build's prefix (main/)
        um = u.get("measures", {})
        units[key] = {"name": Path(meta.get("source_path") or key).name, "complete": bool(meta.get("complete")),
                      "fuzzy": float(um.get("fuzzy_match_percent") or 0.0), "size": int(um.get("total_code", 0)),
                      "functions": int(um.get("total_functions", 0)),
                      "funcs": {f["name"]: (f.get("metadata", {}).get("demangled_name") or f["name"],
                                            float(f.get("fuzzy_match_percent") or 0.0), int(f["size"]))
                                for f in u.get("functions", [])}}
        total += units[key]["size"]
        fuzzy += units[key]["size"] * units[key]["fuzzy"] / 100
    if not units:
        return None
    return {"total_code": int(total), "fuzzy_code": round(fuzzy)}, units


def parts(d):
    """{line name: fuzzy_code, total_code, files, matched_files} for the shared engine (files in two or more games) and
    each game's own code, from each game's first version (Rat's DEBUG) as treemap.py draws them; units without code
    left out. A file is matched when it is complete in every game that has it (green in the treemap)."""
    files = {}  # file name: [(size, fuzzy %, complete) in each game that has it], [those games]
    for game, vers in GAMES.items():
        loaded = load(d, vers[0])
        for key, unit in (loaded[1] if loaded else {}).items():
            if unit["size"]:
                entry = files.setdefault(key.split("/")[-1], ([], []))
                entry[0].append((unit["size"], unit["fuzzy"], unit["complete"]))
                entry[1].append(game)
    out = {name: {"fuzzy_code": 0.0, "total_code": 0, "files": 0, "matched_files": 0}
           for name in ["Shared engine"] + [f"{game}-only code" for game in GAMES]}
    for units, games in files.values():
        part = out["Shared engine" if len(games) > 1 else f"{games[0]}-only code"]
        part["fuzzy_code"] += sum(size * fuzzy / 100 for size, fuzzy, _ in units)
        part["total_code"] += sum(size for size, _, _ in units)
        part["files"] += 1
        part["matched_files"] += all(complete for _, _, complete in units)
    for part in out.values():
        part["fuzzy_code"] = round(part["fuzzy_code"])
    return out


def pct(m, key, total):
    return 100.0 * m.get(key, 0) / m[total] if m.get(total) else 0.0


def step(name, before, after, prev_size, size):
    """OK's `name -> (+pct%, +bytes) -> pct%`, bytes as the fuzzy-matched share of the code."""
    gained = round(size * after / 100) - round(prev_size * before / 100)
    return f"`{name} -> ({after - before:+.2f}%, {gained:+,}) -> {after:.2f}%`"


def unit_change(p, c):
    """(rank, bytes changed, line, function lines) for a unit whose match changed, else None."""
    p = p or {"fuzzy": 0.0, "size": c["size"], "complete": False, "funcs": {}}
    label = f" matched, {c['functions']} function{'s' if c['functions'] != 1 else ''}" if c["complete"] and not p["complete"] else \
        " unmatched" if p["complete"] and not c["complete"] else ""
    if f"{p['fuzzy']:.2f}" == f"{c['fuzzy']:.2f}" and not label:
        return None
    funcs = []
    if not c["complete"]:
        for key, (name, after, size) in c["funcs"].items():
            _, before, prev_size = p["funcs"].get(key, (name, 0.0, size))
            if f"{before:.2f}" != f"{after:.2f}":
                funcs.append((name, before, after, prev_size, size))
    done = sum(1 for f in funcs if f"{f[2]:.2f}" == "100.00")
    if done > COLLAPSE:
        funcs = [f for f in funcs if f"{f[2]:.2f}" != "100.00"]
    short = [func_name(f[0]) for f in funcs]
    funcs = ["- " + step(s if short.count(s) == 1 else f[0], *f[1:]) for s, f in zip(short, funcs)]
    if done > COLLAPSE:
        funcs.append(f"- {'and ' if funcs else ''}{done} functions now at 100.00%")
    rank = 0 if c["complete"] and not p["complete"] else 2 if p["complete"] else 1 if c["fuzzy"] >= p["fuzzy"] else 2
    gained = round(c["size"] * c["fuzzy"] / 100) - round(p["size"] * p["fuzzy"] / 100)
    return rank, gained, step(c["name"], p["fuzzy"], c["fuzzy"], p["size"], c["size"]) + label, funcs


def contributor():
    env = os.environ.get
    repo, head, prev, pusher = env("REPO"), env("HEAD_SHA"), env("PREV_SHA"), env("PUSHER")
    if not (repo and head):
        return "Changes:"
    url = f"https://github.com/{repo}"
    commits = int(env("COMMITS")) if (env("COMMITS") or "").isdigit() else 0
    if prev and commits != 1:
        ref = f"[{prev[:7]}..{head[:7]}](<{url}/compare/{prev}...{head}>)" + (f" ({commits} commits)" if commits else "")
    else:
        ref = f"[{head[:7]}](<{url}/commit/{head}>)"
    if not pusher:
        return f"Changes in {ref}:"
    return f"[{pusher}](<https://github.com/{pusher}>) just contributed the following in {ref}:"


def badges(out_dir, cur_dir):
    """Write OUT_DIR/<line name>.json for each line of parts(): the percentage the post shows, labelled with the
    line's name."""
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    for name, cur in parts(cur_dir).items():
        cur_pct = f"{pct(cur, 'fuzzy_code', 'total_code'):.2f}"
        badge = {"schemaVersion": 1, "label": name, "message": f"{cur_pct}%",
                 "color": BADGE_COLORS[cur_pct == "100.00"]}
        (Path(out_dir) / f"{name.lower().replace(' ', '-')}.json").write_text(json.dumps(badge) + "\n")


def main():
    args = sys.argv[1:]
    if args[0] == "--badges":
        badges(args[1], args[2])
        return
    cur_dir, prev_dir = args[0], (args[1] if len(args) > 1 else None)
    rows = []
    changes = {}
    changed = False
    for ver in VERSIONS:
        cur = load(cur_dir, ver)
        if cur is None:
            continue
        cur, cur_units = cur
        prev = load(prev_dir, ver) if prev_dir else None
        if prev is None:
            changed = True
        else:
            prev, prev_units = prev
            changed |= cur.get("fuzzy_code", 0) != prev.get("fuzzy_code", 0)
            for key, u in cur_units.items():
                change = unit_change(prev_units.get(key), u)
                if change:
                    changes.setdefault(key, []).append((ver, change))
        rows.append((ver, cur, prev))
    if not changed and not changes:
        return

    lines = []
    prev_parts = parts(prev_dir) if prev_dir else {}
    for name, cur in parts(cur_dir).items():
        prev = prev_parts.get(name)
        stats = f"{cur['fuzzy_code']:,} / {cur['total_code']:,}"
        cur_pct, end = pct(cur, "fuzzy_code", "total_code"), ""
        if prev and cur["fuzzy_code"] != prev["fuzzy_code"]:
            prev_pct = pct(prev, "fuzzy_code", "total_code")
            gained = cur["fuzzy_code"] - prev["fuzzy_code"]
            stats = f"({cur_pct - prev_pct:+.2f}% {gained:+,}), " + stats
            if round(cur_pct, 2) // 10 > round(prev_pct, 2) // 10:
                end = " 🎉"
        lines.append(f"**{name}** {cur_pct:.2f}%{end} `{stats}` {cur['matched_files']} / {cur['files']} files")

    vers = [ver for ver, _, prev in rows if prev]
    items = []
    for key, per_ver in changes.items():
        rank, gained, line, funcs = per_ver[-1][1]  # the latest build with the change
        builds = [ver for ver, _ in per_ver]
        game = GAME_OF[builds[0]]
        if builds == [ver for ver in vers if GAME_OF[ver] == game]:
            line += f" ({game})"
        else:
            line += f" ({game} {', '.join(ABBREVS.get(b, b) for b in builds)})"
        items.append((rank, -abs(gained), line.lower(), [line] + funcs))
    groups = [group for *_, group in sorted(items)]
    if not groups:
        print(json.dumps({"username": USERNAME, "content": "\n".join(lines)}))
        return
    lines += ["", contributor()]

    def message(shown, more):
        return "\n".join(lines + shown + ([f"... and {more} more file{'s' if more != 1 else ''}"] if more else []))

    shown = []
    for i, group in enumerate(groups):
        more = len(groups) - i - 1
        if len(message(shown + group, more)) <= MAX_CONTENT:
            shown += group
            continue
        if not shown:  # the first file alone is too long: as many of its lines as fit
            for k in range(len(group) - 1, 0, -1):
                part = group[:k] + [f"- and {len(group) - k} more line{'s' if len(group) - k != 1 else ''}"]
                if len(message(part, more)) <= MAX_CONTENT:
                    shown = part
                    break
            if shown:
                break
        more += 1
        break
    else:
        more = 0
    print(json.dumps({"username": USERNAME, "content": message(shown, more)}))


if __name__ == "__main__":
    main()
