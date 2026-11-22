#!/usr/bin/env python3
"""Draw a treemap of every game's Game units as a PNG, for the Discord progress post and the README.

Usage: treemap.py CUR_DIR OUT.png [PREV_DIR]
One box per file over all games (the units of each game's versions, each from the first version with code for it, Rat's
DEBUG before its other builds; the same file name in several games is one file), grouped by folder and sized by its code
bytes summed over the games that have it (tiny units raised to a minimum box; units without code left out): green is
complete in every game that has it, grey has nothing matched, and blue is partly matched, its brightness rising in a
straight line with the matched code over those games (a file done in one game only is blue by that game's share of its
bytes: about 64% for Rat's DEBUG beside RotU). With PREV_DIR, files whose match changed in any version of any game get
an outline, or a yellow fill when too small for one. Wide and short, with folder headings only, to stay readable on a
phone without filling the screen.
Each directory holds <VERSION>_report/report.json, as for progress.py. Needs Pillow; progress.py doesn't, so a failure
here only costs the post its image.
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from progress import GAMES, VERSIONS, is_game

WIDTH, HEIGHT = 1000, 420
MARGIN = 4
GAP = 2
FOLDER_GAP = 8
FOLDER_FONT = 26
HEADING = FOLDER_FONT + 6
OUTLINE = 4
MIN_BOX = 1  # the smallest unit box side, so that every unit shows as its own box
PHI = (1 + 5 ** 0.5) / 2
SURFACE = (0x1a, 0x1a, 0x19)
INK = (0xf0, 0xef, 0xec)
MATCHED = (0x1f, 0xa8, 0x4f)
PARTIAL = (0x39, 0x87, 0xe5)
UNMATCHED = (0x3c, 0x3c, 0x39)
CHANGED = (0xff, 0xd3, 0x3d)


def load(d, ver):
    """{unit path without the build's prefix: its measures and metadata} of the Game units, or None without a report."""
    path = Path(d) / f"{ver}_report" / "report.json"
    if not path.exists():
        return None
    units = {}
    for unit in json.loads(path.read_text())["units"]:
        if is_game(unit, ver):
            units[unit["name"].split("/", 1)[-1]] = unit
    return units


def match_state(unit):
    """What progress.py's list of changed units compares."""
    if unit is None:
        return "0.00", False
    fuzzy = float(unit.get("measures", {}).get("fuzzy_match_percent") or 0.0)
    return f"{fuzzy:.2f}", bool(unit.get("metadata", {}).get("complete"))


def changed_units(cur_dir, prev_dir):
    """The file names whose match changed in any version."""
    changed = set()
    for ver in VERSIONS if prev_dir else []:
        cur, prev = load(cur_dir, ver), load(prev_dir, ver)
        if cur and prev:
            changed |= {key.split("/")[-1] for key, unit in cur.items() if match_state(unit) != match_state(prev.get(key))}
    return changed


def squarify(values, x0, y0, x1, y1):
    """Rectangles for values sorted large to small: the squarified layout of d3.treemap."""
    boxes, total, i0, n = [], sum(values), 0, len(values)
    while i0 < n:
        dx, dy = x1 - x0, y1 - y0
        i1 = i0 + 1
        row = low = high = values[i0]
        alpha = max(dy / dx, dx / dy) / (total * PHI)
        beta = row * row * alpha
        best = max(high / beta, beta / low)
        while i1 < n:
            value = values[i1]
            beta = (row + value) * (row + value) * alpha
            ratio = max(max(high, value) / beta, beta / min(low, value))
            if ratio > best:
                break
            row, low, high, best, i1 = row + value, min(low, value), max(high, value), ratio, i1 + 1
        if dx < dy:  # a horizontal row across the top
            bottom = y0 + dy * row / total
            x = x0
            for value in values[i0:i1]:
                boxes.append((x, y0, x + dx * value / row, bottom))
                x += dx * value / row
            y0 = bottom
        else:  # a vertical column on the left
            right = x0 + dx * row / total
            y = y0
            for value in values[i0:i1]:
                boxes.append((x0, y, right, y + dy * value / row))
                y += dy * value / row
            x0 = right
        total -= row
        i0 = i1
    return boxes


def folder_boxes(sizes):
    """{folder: rectangle}: a column per top folder, its folders stacked, so that a byte takes the same area everywhere."""
    columns = {}
    for name, size in sizes.items():
        columns.setdefault(name.split("/")[0], {})[name] = size
    width, height = WIDTH - 2 * MARGIN, HEIGHT - 2 * MARGIN
    weights = {top: sum(c.values()) / (height - len(c) * HEADING) for top, c in columns.items()}
    boxes, x = {}, MARGIN
    for top, column in columns.items():
        right = x + width * weights[top] / sum(weights.values())
        y, room = MARGIN, height - len(column) * HEADING
        for name, size in column.items():
            bottom = y + HEADING + room * size / sum(column.values())
            boxes[name] = (x, y, right, bottom)
            y = bottom
        x = right
    return boxes


def unit_boxes(values, x0, y0, x1, y1):
    """Boxes for values sorted large to small, tiny values raised until every box is at least MIN_BOX on a side."""
    width, height = x1 - x0, y1 - y0
    if width <= 0 or height <= 0:
        return []
    cell = (MIN_BOX + GAP) ** 2
    for _ in range(12):  # squarify's last cells can be thin: raise the floor until they fit
        floor = 0
        for _ in range(8):  # the floor grows the total, which lowers the bytes per pixel
            floor = cell * sum(max(v, floor) for v in values) / (width * height)
        boxes = [(round(bx0), round(by0), round(bx1) - GAP - 1, round(by1) - GAP - 1)
                 for bx0, by0, bx1, by1 in squarify([max(v, floor) for v in values], x0, y0, x1, y1)]
        if all(min(r - l, b - u) + 1 >= MIN_BOX for l, u, r, b in boxes):
            break
        cell *= 2
    return [(l, u, max(l, r), max(u, b)) for l, u, r, b in boxes]


def code(unit):
    return int(unit.get("measures", {}).get("total_code", 0))


def matched(unit):
    if unit.get("metadata", {}).get("complete"):
        return code(unit)
    return min(code(unit), int(unit.get("measures", {}).get("matched_code") or 0))


def color(units):
    """Green when complete in every game, else grey to blue by how much is matched over the games, in a straight
    line."""
    if all(unit.get("metadata", {}).get("complete") for unit in units):
        return MATCHED
    share = sum(matched(unit) for unit in units) / sum(code(unit) for unit in units)
    return tuple(round(u + (p - u) * share) for u, p in zip(UNMATCHED, PARTIAL))


def main():
    cur_dir, out, prev_dir = sys.argv[1], sys.argv[2], (sys.argv[3] if len(sys.argv) > 3 else None)
    changed = changed_units(cur_dir, prev_dir)
    files = {}  # file name: [folder, [its unit in each game]]
    for vers in GAMES.values():
        seen = set()
        for ver in vers:
            for key, unit in (load(cur_dir, ver) or {}).items():
                if not code(unit) or key in seen:
                    continue
                seen.add(key)
                parts = key.split("/")[1:]  # without the game's source folder
                folder = "/".join([p for p in parts[:-1] if p != "Engine"][:2]) or "(top)"
                files.setdefault(parts[-1], [folder, []])[1].append(unit)
    groups = {}
    for name, (folder, units) in files.items():
        groups.setdefault(folder, []).append((sum(code(unit) for unit in units), name, units))
    groups = sorted(groups.items(), key=lambda g: -sum(u[0] for u in g[1]))

    image = Image.new("RGB", (WIDTH, HEIGHT), SURFACE)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=FOLDER_FONT)

    outlines = []
    folders = folder_boxes({name: sum(u[0] for u in units) for name, units in groups})
    for name, units in groups:
        gx0, gy0, gx1, gy1 = folders[name]
        draw.text((gx0, gy0), name, font=font, fill=INK)
        top, right, bottom = gy0 + HEADING, gx1 - FOLDER_GAP, gy1 - FOLDER_GAP
        units.sort(key=lambda u: -u[0])
        for (_, file, game_units), box in zip(units, unit_boxes([u[0] for u in units], gx0, top, right, bottom)):
            draw.rectangle(box, fill=color(game_units))
            if file in changed:
                outlines.append(box)
    for box in outlines:  # last, so that no neighbour covers one
        if min(box[2] - box[0], box[3] - box[1]) < 2 * OUTLINE + 1:  # too small for an outline around a 2 px hole
            draw.rectangle(box, fill=CHANGED)
        else:
            draw.rectangle(box, outline=CHANGED, width=OUTLINE)
    image.save(out)


if __name__ == "__main__":
    main()
