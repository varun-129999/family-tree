# Love Letters — word game engine

Move generator + scorer for the ongoing "Love Letters" board game (Vaibhav vs
Shail). Finds every legal play for the current rack and ranks it by points.

## Usage

```bash
python3 engine.py               # ranked suggestions for board.json
python3 engine.py --top 25
python3 engine.py --rack IRRSSU # override the rack
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
   cross-word invalidates the whole play. Examples from the current board that
   get rejected for exactly this reason:
   - `S` in front of POUT would make SPOUT, but also S-G-H-I going down → dead.
   - `S` under VENT would make VENTS, but also "SV" next to the lone V → dead.
   - `U` above the P of PHONETIC would make UP, but also U-G-O-O across → dead.
4. Scoring: DL/TL/DW/TW premiums count only on squares where a **new** tile
   lands, and apply to the main word **and** any cross-word through that tile.
   Total score = main word + all cross-words.

## Where the data comes from

- Board, premiums, letter values and rack are transcribed from the 2026-08-18
  screenshot (11×11 board; words on board: VENT, FEAT, POUT, GOO, PHONETIC,
  INS, and verticals ZOONS, GHI, POON, VI).
- Scoring is calibrated against two known scores visible in the screenshot:
  - Opponent's last move: G,O placed to form GOO + GHI + POON for **30**
    → implies DL under the G and TL under the O (row 5, cols 5–6, 1-based).
  - The app's own hint: VIRUS for **18** → with the displayed tile values
    (V5 I1 R1 U2 S1) this only works if all three squares under the hint's
    R,U,S previews are TL (rows 7–9, col 10, 1-based). These three are
    **inferred**, not directly seen — the preview tiles cover them.
- `enable1.txt` is the public-domain ENABLE list (~173k words) that
  Words-With-Friends-style dictionaries are built on. The app's dictionary is
  not identical (the board contains "VI", which ENABLE lacks), so treat rare
  words with mild suspicion before playing them.

## Known unknowns

- Premiums on the bottom two rows (10–11, 1-based) were not visible; encoded
  as plain. Plays reaching there may score slightly more than reported.
- Rack read as I,R,R,S,S,U (3 tiles visible + R,U,S consumed by the app's
  VIRUS preview).
- Letters not yet seen on the board (B D J K L M Q W X Y) default to
  Words-With-Friends values in `board.json`; fix them as they appear.
- No bonus for using the whole rack is modeled (unknown whether the app has
  one).
