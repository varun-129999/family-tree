#!/usr/bin/env python3
"""Move engine for the 'Love Letters' word game.

Given the board state in board.json and the rack, enumerates every legal
placement and ranks it by score.

Legality rules enforced per play:
  1. New tiles go on empty squares, in one straight line, with no gaps
     (existing tiles may sit between/around them).
  2. The main word (the full contiguous line through the new tiles) must be
     in the dictionary when it is 2+ letters long.
  3. CROSS-WORDS: every new tile that touches existing tiles perpendicular to
     the main direction forms a second word (the whole perpendicular run),
     and EVERY one of those must also be in the dictionary. A play with even
     one invalid cross-word is rejected outright.
  4. The play must connect to the existing board (through a tile in the main
     word or through a cross-word).

Scoring: letter premiums (DL/TL) and word premiums (DW/TW) count only on
squares where a NEW tile lands, and apply to every word that tile is part of.
Score = main word + all cross-words.

Usage:
  python3 engine.py                 # top plays for board.json
  python3 engine.py --top 20
  python3 engine.py --rack IRRSSU   # override rack
  python3 engine.py --selftest      # verify scoring against known app data
"""
import argparse
import copy
import itertools
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# premium char -> (letter multiplier, word multiplier)
MULT = {".": (1, 1), "d": (2, 1), "t": (3, 1), "D": (1, 2), "T": (1, 3)}


def load_board(path):
    with open(path) as f:
        bd = json.load(f)
    bd["grid"] = [list(row) for row in bd["grid"]]
    bd["premiums"] = [list(row) for row in bd["premiums"]]
    n = bd["size"]
    assert len(bd["grid"]) == n and all(len(r) == n for r in bd["grid"])
    assert len(bd["premiums"]) == n and all(len(r) == n for r in bd["premiums"])
    return bd


def load_words(path):
    with open(path) as f:
        return {w.strip().lower() for w in f if w.strip()}


def evaluate(bd, words, placed, dr, dc):
    """Check one placement for legality and score it.

    placed: {(row, col): letter} for the NEW tiles, all on one line along
    direction (dr, dc). Returns (total, [(word, points, cells), ...]) or None
    if the play is illegal for any reason (including a bad cross-word).
    """
    grid, prem, val, n = bd["grid"], bd["premiums"], bd["letter_values"], bd["size"]

    def tile(r, c):
        if 0 <= r < n and 0 <= c < n:
            if (r, c) in placed:
                return placed[(r, c)]
            if grid[r][c] != ".":
                return grid[r][c]
        return None

    def run(r, c, dr, dc):
        while tile(r - dr, c - dc):
            r, c = r - dr, c - dc
        cells = []
        while tile(r, c):
            cells.append((r, c))
            r, c = r + dr, c + dc
        return cells

    def word_score(cells):
        word, pts, wmult = "", 0, 1
        for r, c in cells:
            lm, wm = MULT[prem[r][c]] if (r, c) in placed else (1, 1)
            word += tile(r, c)
            pts += val[tile(r, c)] * lm
            wmult *= wm
        return word, pts * wmult

    for r, c in placed:
        if grid[r][c] != ".":
            return None  # square already occupied

    formed = []
    r0, c0 = min(placed)
    main = run(r0, c0, dr, dc)
    if not all(p in main for p in placed):
        return None  # gap in the placement
    connected = any(p not in placed for p in main)
    if len(main) >= 2:
        w, pts = word_score(main)
        if w.lower() not in words:
            return None
        formed.append((w, pts, main))
    for r, c in sorted(placed):
        cross = run(r, c, dc, dr)  # perpendicular run through this new tile
        if len(cross) >= 2:
            w, pts = word_score(cross)
            if w.lower() not in words:
                return None  # invalid cross-word kills the whole play
            formed.append((w, pts, cross))
            connected = True
    if not formed or not connected:
        return None  # nothing formed, or floating placement
    return sum(p for _, p, _ in formed), formed


def all_plays(bd, words, rack):
    """Enumerate every legal play for the rack. Returns list of dicts."""
    grid, n = bd["grid"], bd["size"]
    rack = list(rack.upper())
    seen = {}
    for dr, dc in ((0, 1), (1, 0)):
        for r0 in range(n):
            for c0 in range(n):
                if grid[r0][c0] != ".":
                    continue
                # successive empty squares from (r0,c0) along the direction
                pos, r, c = [], r0, c0
                while 0 <= r < n and 0 <= c < n and len(pos) < len(rack):
                    if grid[r][c] == ".":
                        pos.append((r, c))
                    r, c = r + dr, c + dc
                for k in range(1, len(pos) + 1):
                    for perm in set(itertools.permutations(rack, k)):
                        placed = dict(zip(pos[:k], perm))
                        res = evaluate(bd, words, placed, dr, dc)
                        if res is None:
                            continue
                        key = frozenset(placed.items())
                        if key not in seen or seen[key]["score"] < res[0]:
                            seen[key] = {
                                "score": res[0],
                                "words": [(w, p) for w, p, _ in res[1]],
                                "placed": sorted(placed.items()),
                                "dir": "across" if dc else "down",
                            }
    return sorted(seen.values(), key=lambda p: (-p["score"], p["words"][0][0]))


def describe(play):
    tiles = ", ".join(f"{l}@({r + 1},{c + 1})" for (r, c), l in play["placed"])
    ws = " + ".join(f"{w} ({p})" for w, p in play["words"])
    return f"{ws} = {play['score']}  |  place {tiles} [{play['dir']}]"


def strip(bd, cells):
    out = copy.deepcopy(bd)
    for r, c in cells:
        out["grid"][r][c] = "."
    return out


def selftest(bd, words):
    prex = [(8, 3), (9, 3), (10, 3)]
    virus = [(8, 9), (9, 9), (10, 9)]
    wags = [(10, 6), (10, 7), (10, 8)]
    go = [(6, 4), (6, 5)]

    # Replay the four moves with known app scores, oldest first, each on the
    # board as it stood at the time.
    bd_go = strip(bd, go + virus + wags + prex)
    total, formed = evaluate(bd_go, words, {(6, 4): "G", (6, 5): "O"}, 0, 1)
    assert total == 30 and sorted(w for w, _, _ in formed) == ["GHI", "GOO", "POON"], (total, formed)

    bd_virus = strip(bd, virus + wags + prex)
    total, formed = evaluate(bd_virus, words, {(8, 9): "R", (9, 9): "U", (10, 9): "S"}, 1, 0)
    assert total == 18 and [w for w, _, _ in formed] == ["VIRUS"], (total, formed)

    bd_wags = strip(bd, wags + prex)
    total, formed = evaluate(bd_wags, words, {(10, 6): "W", (10, 7): "A", (10, 8): "G"}, 0, 1)
    assert total == 33 and [w for w, _, _ in formed] == ["WAGS"], (total, formed)

    bd_prex = strip(bd, prex)
    total, formed = evaluate(bd_prex, words, {(8, 3): "R", (9, 3): "E", (10, 3): "X"}, 1, 0)
    assert total == 53 and sorted(w for w, _, _ in formed) == ["PREX", "RINS"], (total, formed)

    # Cross-word validation on the current board: real main words that must be
    # rejected because the perpendicular word they create is not valid.
    assert evaluate(bd, words, {(8, 7): "E"}, 0, 1) is None  # RINSE, but EE down
    assert evaluate(bd, words, {(6, 8): "I"}, 1, 0) is None  # TIT down, but IV across
    assert evaluate(bd, words, {(4, 7): "I"}, 0, 1) is None  # ZIN, but FIU down
    assert evaluate(bd, words, {(9, 5): "A"}, 1, 0) is None  # POONA is not a word
    assert evaluate(bd, words, {(9, 8): "A"}, 1, 0) is None  # AG down, but AU across

    # Positive controls incl. cross-word scoring.
    total, formed = evaluate(bd, words, {(1, 8): "E"}, 1, 0)
    assert total == 10 and [w for w, _, _ in formed] == ["EVENT"], (total, formed)
    total, formed = evaluate(bd, words, {(1, 6): "T", (1, 7): "I", (1, 8): "E"}, 0, 1)
    assert total == 14 and sorted(w for w, _, _ in formed) == ["EVENT", "TIE"], (total, formed)
    print("selftest: all checks passed (GO=30, VIRUS=18, WAGS=33, PREX=53, cross-word rejections OK)")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--board", default=os.path.join(HERE, "board.json"))
    ap.add_argument("--dict", default=os.path.join(HERE, "enable1.txt"))
    ap.add_argument("--rack", default=None, help="override rack letters")
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    bd = load_board(args.board)
    words = load_words(args.dict)
    if args.selftest:
        selftest(bd, words)
        return
    rack = args.rack or bd["rack"]
    plays = all_plays(bd, words, rack)
    print(f"rack: {rack}   legal plays found: {len(plays)}")
    print("coordinates are (row,col), 1-based from the top-left of the board\n")
    for i, play in enumerate(plays[: args.top], 1):
        print(f"{i:3}. {describe(play)}")


if __name__ == "__main__":
    main()
