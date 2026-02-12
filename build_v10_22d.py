#!/usr/bin/env python3
"""
V10_22d Build Script — Boneyard: suits in ROWS, right-aligned + blue border for hand tiles
"""
import re

INPUT  = '/var/lib/freelancer/projects/40101953/TN51_Dominoes_V10_22.html'
OUTPUT = INPUT  # in-place

with open(INPUT, 'r', encoding='utf-8') as f:
    src = f.read()

patches = []

# ─── P1: Replace boneyard grid layout — suits in ROWS, right-aligned ───
old_layout = """  // Layout: Doubles on TOP ROW, suit tiles in columns below.
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
  }"""

new_layout = """  // Layout: Doubles on TOP ROW, each suit in its OWN ROW below.
  // Right-aligned staircase (tiles pushed to the right).
  //
  // Row 0: 7-7  6-6  5-5  4-4  3-3  2-2  1-1  0-0   (all doubles)
  // Row 1: 7-6  7-5  7-4  7-3  7-2  7-1  7-0         (7-suit, 7 tiles)
  // Row 2: 6-5  6-4  6-3  6-2  6-1  6-0               (6-suit, 6 tiles)
  // Row 3: 5-4  5-3  5-2  5-1  5-0                     (5-suit, 5 tiles)
  // Row 4: 4-3  4-2  4-1  4-0                          (4-suit, 4 tiles)
  // Row 5: 3-2  3-1  3-0                               (3-suit, 3 tiles)
  // Row 6: 2-1  2-0                                     (2-suit, 2 tiles)
  // Row 7: 1-0                                          (1-suit, 1 tile)

  // Build the grid: rows[rowIdx] = array of [high, low] tiles
  const rows = [];
  // Row 0: doubles (7-7 through 0-0)
  const doublesRow = [];
  for(let pip = 7; pip >= 0; pip--){
    doublesRow.push([pip, pip]);
  }
  rows.push(doublesRow);

  // Rows 1-7: each row is one suit (non-double tiles only)
  // Row 1 = 7-suit: [7,6],[7,5],[7,4],[7,3],[7,2],[7,1],[7,0]
  // Row 2 = 6-suit: [6,5],[6,4],[6,3],[6,2],[6,1],[6,0]
  // ...etc
  for(let suit = 7; suit >= 1; suit--){
    const row = [];
    for(let low = suit - 1; low >= 0; low--){
      row.push([suit, low]);
    }
    rows.push(row);
  }"""

patches.append(('P1: Boneyard layout — suits in rows, right-aligned', old_layout, new_layout))

# ─── P2: Replace tile drawing code — right-aligned + blue border for hand tiles ───
old_draw = """  // Draw each tile — COLUMNAR layout
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
      const y = rowIdx * (tileH + gap) + gap;

      const played = isTilePlayedBones(tile[0], tile[1]);
      const trump = isTrumpTile(tile);

      // Save context and draw the tile
      ctx.save();
      ctx.translate(x, y);

      // Create a small offscreen canvas for this tile to reuse drawFace
      const tileCanvas = document.createElement('canvas');
      tileCanvas.width = Math.round(tileW * dpr);
      tileCanvas.height = Math.round(tileH * dpr);
      const tctx = tileCanvas.getContext('2d');
      tctx.scale(dpr, dpr);
      drawFace(tctx, tile, tileW, tileH, trump, !played);

      // Draw the tile canvas onto the main canvas
      ctx.drawImage(tileCanvas, 0, 0, tileW, tileH);

      ctx.restore();
    }
  }
}"""

new_draw = """  // Build set of tiles in player's hand (seat 0)
  const handTiles = new Set();
  if(session && session.game && session.game.hands[0]){
    for(const t of session.game.hands[0]){
      if(t) handTiles.add(Math.min(t[0],t[1]) + ',' + Math.max(t[0],t[1]));
    }
  }
  const isTileInHand = (a, b) => handTiles.has(Math.min(a,b) + ',' + Math.max(a,b));

  // Draw each tile — ROW layout, RIGHT-ALIGNED
  // Row 0 (doubles) = 8 tiles, rows 1-7 have decreasing count.
  // Right-align: offset each row so its last tile aligns with column 7.
  const maxCols = 8;
  for(let rowIdx = 0; rowIdx < rows.length; rowIdx++){
    const row = rows[rowIdx];
    const colOffset = maxCols - row.length;  // push right

    for(let colIdx = 0; colIdx < row.length; colIdx++){
      const tile = row[colIdx];
      const col = colOffset + colIdx;
      const x = col * (tileW + gap) + gap;
      const y = rowIdx * (tileH + gap) + gap;

      const played = isTilePlayedBones(tile[0], tile[1]);
      const trump = isTrumpTile(tile);
      const inHand = isTileInHand(tile[0], tile[1]);

      // Save context and draw the tile
      ctx.save();
      ctx.translate(x, y);

      // Create a small offscreen canvas for this tile to reuse drawFace
      const tileCanvas = document.createElement('canvas');
      tileCanvas.width = Math.round(tileW * dpr);
      tileCanvas.height = Math.round(tileH * dpr);
      const tctx = tileCanvas.getContext('2d');
      tctx.scale(dpr, dpr);
      drawFace(tctx, tile, tileW, tileH, trump, !played);

      // Draw the tile canvas onto the main canvas
      ctx.drawImage(tileCanvas, 0, 0, tileW, tileH);

      // Blue border for tiles in player's hand
      if(inHand){
        ctx.strokeStyle = '#4A9EFF';
        ctx.lineWidth = 2;
        ctx.strokeRect(1, 1, tileW - 2, tileH - 2);
      }

      ctx.restore();
    }
  }
}"""

patches.append(('P2: Right-aligned drawing + blue border for hand tiles', old_draw, new_draw))

# ─── Apply patches ───
ok = 0
for name, old, new in patches:
    if old in src:
        src = src.replace(old, new, 1)
        print(f'OK: {name}')
        ok += 1
    else:
        print(f'FAILED: {name} — old string not found')

with open(OUTPUT, 'w', encoding='utf-8') as f:
    f.write(src)

print(f'\nApplied {ok}/{len(patches)} patches.')
