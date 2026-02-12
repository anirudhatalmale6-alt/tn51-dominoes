#!/usr/bin/env python3
"""
Build V10_22c from V10_22:
Rearrange boneyard layout:
- Top row: all 8 doubles (7-7, 6-6, 5-5, 4-4, 3-3, 2-2, 1-1, 0-0)
- Below: non-double tiles in columns by suit, each column headed by its double
- Column 0: 7-7 / 7-6 / 7-5 / 7-4 / 7-3 / 7-2 / 7-1 / 7-0
- Column 1: 6-6 / 6-5 / 6-4 / 6-3 / 6-2 / 6-1 / 6-0
- etc.
"""
import sys

SRC = "/var/lib/freelancer/projects/40101953/TN51_Dominoes_V10_22.html"
DST = "/var/lib/freelancer/projects/40101953/TN51_Dominoes_V10_22.html"

with open(SRC, "r", encoding="utf-8") as f:
    code = f.read()

patches_applied = 0

def patch(label, old, new):
    global code, patches_applied
    if old not in code:
        print(f"FAILED: {label} — old string not found")
        sys.exit(1)
    count = code.count(old)
    if count > 1:
        print(f"WARNING: {label} — old string found {count} times, replacing first only")
    code = code.replace(old, new, 1)
    patches_applied += 1
    print(f"OK: {label}")


patch("P1: Rearrange boneyard - doubles on top, suits in columns",
    """  // Layout: 8 rows, RIGHT-ALIGNED staircase
  // Doubles on the left of each row, suits extend to the right.
  // Going straight up or right from any tile shows all tiles in that suit.
  //
  // Row 0: 7-7, 7-6, 7-5, 7-4, 7-3, 7-2, 7-1, 7-0  (8 tiles, no indent)
  // Row 1:      6-6, 6-5, 6-4, 6-3, 6-2, 6-1, 6-0   (7 tiles, indented 1)
  // Row 2:           5-5, 5-4, 5-3, 5-2, 5-1, 5-0    (6 tiles, indented 2)
  // ...
  // Row 7:                                        0-0  (1 tile, indented 7)
  const rows = [];
  for(let high = 7; high >= 0; high--){
    const row = [];
    for(let low = high; low >= 0; low--){
      row.push([high, low]);
    }
    rows.push(row);
  }""",
    """  // Layout: Doubles on TOP ROW, suit tiles in columns below.
  // Each column shows a complete suit with the double at the top.
  //
  // Row 0: 7-7  6-6  5-5  4-4  3-3  2-2  1-1  0-0   (all doubles)
  // Row 1: 7-6  6-5  5-4  4-3  3-2  2-1  1-0         (7 tiles)
  // Row 2: 7-5  6-4  5-3  4-2  3-1  2-0               (6 tiles)
  // Row 3: 7-4  6-3  5-2  4-1  3-0                     (5 tiles)
  // Row 4: 7-3  6-2  5-1  4-0                          (4 tiles)
  // Row 5: 7-2  6-1  5-0                               (3 tiles)
  // Row 6: 7-1  6-0                                     (2 tiles)
  // Row 7: 7-0                                          (1 tile)
  //
  // Reading down column 0: 7-7, 7-6, 7-5, 7-4, 7-3, 7-2, 7-1, 7-0 (all 7s)
  // Reading down column 1: 6-6, 6-5, 6-4, 6-3, 6-2, 6-1, 6-0 (all 6s)
  // etc.

  // Build the grid: rows[rowIdx][colIdx] = [high, low]
  const rows = [];
  // Row 0: doubles
  const doublesRow = [];
  for(let pip = 7; pip >= 0; pip--){
    doublesRow.push([pip, pip]);
  }
  rows.push(doublesRow);

  // Rows 1-7: non-double tiles
  // Row r (1-based): each column c has tile [7-c, 7-c-r] (high=col's suit, low decreases)
  // Only include if low >= 0
  for(let r = 1; r <= 7; r++){
    const row = [];
    for(let col = 0; col <= 7; col++){
      const high = 7 - col;  // column 0 = suit 7, column 1 = suit 6, etc.
      const low = high - r;  // row 1 = high-1, row 2 = high-2, etc.
      if(low >= 0){
        row.push([high, low]);
      }
    }
    rows.push(row);
  }""")


# Also fix the drawing loop — no longer need right-indent since
# each row naturally has fewer tiles (the grid is already columnar)
patch("P2: Fix drawing loop for new columnar layout",
    """  // Draw each tile — RIGHT-ALIGNED layout
  // Each row is indented from the LEFT by rowIdx tile-widths.
  // This means the rightmost tile of every row aligns at the same x position.
  for(let rowIdx = 0; rowIdx < rows.length; rowIdx++){
    const row = rows[rowIdx];
    // Indent from left: rowIdx tiles worth of space
    const xIndent = rowIdx * (tileW + gap);

    for(let colIdx = 0; colIdx < row.length; colIdx++){
      const tile = row[colIdx];
      const x = xIndent + colIdx * (tileW + gap) + gap;
      const y = rowIdx * (tileH + gap) + gap;""",
    """  // Draw each tile — COLUMNAR layout
  // Row 0 (doubles) spans all 8 columns.
  // Row 1+ tiles are placed in their respective columns.
  // Each tile knows which column it belongs to based on its high pip.
  for(let rowIdx = 0; rowIdx < rows.length; rowIdx++){
    const row = rows[rowIdx];

    for(let colIdx = 0; colIdx < row.length; colIdx++){
      const tile = row[colIdx];
      // Column position: column = 7 - high pip (so 7s are col 0, 6s col 1, etc.)
      const col = 7 - Math.max(tile[0], tile[1]);
      const x = col * (tileW + gap) + gap;
      const y = rowIdx * (tileH + gap) + gap;""")


with open(DST, "w", encoding="utf-8") as f:
    f.write(code)

print(f"\nDone — {patches_applied} patches applied → {DST}")
print(f"Output size: {len(code):,} bytes")
