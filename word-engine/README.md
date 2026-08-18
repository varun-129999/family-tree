# Love Letters — word game engine

Move generator + scorer for the ongoing "Love Letters" board game (Vaibhav vs
Shail). Finds every legal play for the current rack and ranks it by points.

## Usage

```bash
python3 engine.py               # ranked suggestions for board.json
python3 engine.py --top 25
python3 engine.py --rack EEIITTA # override the rack
python3 engine.py --selftest    # re-verify scoring against known app scores
```

After each move, edit `board.json`: put the new letters into `grid` and set
`rack` to your current letters.

## Rules the engine enforces

1. New tiles go in one straight line on empty squares (existing tiles may be
   interleaved), and the play must connect to the board.
2. The main word must be in the dictionary.
3. **Cross-words:** every newly placed tile that ends up adjacent to existing
   tiles perpendicular to the main word forms a second word — the entire
   perpendicular run — and every one of those must be valid too. One bad
   cross-word invalidates the whole play. Examples from the current board:
   - `E` after RINS would make RINSE, but it sits under the E of PHONETIC and
     "EE" is not a word → rejected.
   - `I` between the two T columns (TIT going down) would also make "IV"
     across next to the lone V → rejected.
4. Scoring: DL/TL/DW/TW premiums count only on squares where a **new** tile
   lands, and apply to the main word **and** any cross-word through that tile.
   Total score = main word + all cross-words.

## Where the data comes from

- Board, premiums, letter values and rack are transcribed from the full-board
  screenshot of 2026-08-18 (11×11; all empty-square premiums directly
  visible). The board's premium layout is **asymmetric** — it does not follow
  the usual mirrored pattern, so nothing is assumed by symmetry.
- Scoring is calibrated against four known move scores, each replayed exactly
  by `--selftest`:
  | Move | Words | App score |
  |------|-------|-----------|
  | Shail: G,O | GOO + GHI + POON | 30 |
  | Vaibhav: R,U,S | VIRUS | 18 |
  | Shail: W,A,G | WAGS | 33 |
  | Vaibhav: R,E,X | PREX + RINS | 53 |
  These pin down the premiums now hidden under those tiles (recorded in
  `board.json` so the replays stay reproducible).
- Letter values are read off the tiles; this app inflates some values vs
  standard sets (F=5, X=9, Z=11). X=9 is confirmed by the PREX arithmetic.
- `enable1.txt` is the public-domain ENABLE list (~173k words) that
  Words-With-Friends-style dictionaries are built on. The app's dictionary is
  not identical (the board contains "VI", which ENABLE lacks), so treat rare
  words with mild suspicion before playing them.

## Known unknowns

- Letters not yet seen on the board (B D J K L M Q Y) default to
  Words-With-Friends values in `board.json`; fix them as they appear.
- No bonus for using the whole rack is modeled (unknown whether the app has
  one).
- Where the app's WAGS play scored 33, the TW could sit under the W or the G
  (both fit); it is consumed either way and cannot affect future plays.
