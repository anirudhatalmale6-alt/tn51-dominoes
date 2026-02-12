#!/usr/bin/env python3
"""
Build V10_22b from V10_22:
Fix boneyard layout:
1. Right-align rows (doubles on left, suit tiles go right)
2. Shrink tiles ~15%
3. Each row indented one tile-width from the left
"""
import sys

SRC = "/var/lib/freelancer/projects/40101953/TN51_Dominoes_V10_22.html"
DST = "/var/lib/freelancer/projects/40101953/TN51_Dominoes_V10_22.html"  # overwrite in-place

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


# ===========================================================================
# PATCH 1: Replace entire renderBoneyard function with right-aligned, smaller layout
# ===========================================================================

patch("P1: Fix boneyard layout - right-align and shrink",
    """function renderBoneyard(){
  const canvas = document.getElementById('bonesCanvas');
  if(!canvas) return;

  const dpr = window.devicePixelRatio || 1;

  // Tile dimensions
  const tileW = 48;
  const tileH = 96;
  const gap = 4;

  // Layout: 8 rows, row N starts at column N and has (8-N) tiles
  // Row 0: 7-7, 7-6, 7-5, 7-4, 7-3, 7-2, 7-1, 7-0  (8 tiles)
  // Row 1: 6-6, 6-5, 6-4, 6-3, 6-2, 6-1, 6-0        (7 tiles)
  // ...
  // Row 7: 0-0                                         (1 tile)
  const rows = [];
  for(let high = 7; high >= 0; high--){
    const row = [];
    for(let low = high; low >= 0; low--){
      row.push([high, low]);
    }
    rows.push(row);
  }

  // Calculate canvas size
  const maxCols = 8;
  const numRows = 8;
  const canvasW = maxCols * (tileW + gap) + gap;
  const canvasH = numRows * (tileH + gap) + gap;

  canvas.width = canvasW * dpr;
  canvas.height = canvasH * dpr;
  canvas.style.width = canvasW + 'px';
  canvas.style.height = canvasH + 'px';

  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);

  // Background (dark green felt)
  ctx.fillStyle = 'rgba(0,40,0,0.6)';
  ctx.fillRect(0, 0, canvasW, canvasH);

  // Determine played tiles and trump state
  const playedTiles = new Set();

  // Build played set from tricks_team
  if(session && session.game){
    for(let team = 0; team < 2; team++){
      for(const record of (session.game.tricks_team[team] || [])){
        for(let seat = 0; seat < record.length; seat++){
          const t = record[seat];
          if(t) playedTiles.add(Math.min(t[0],t[1]) + ',' + Math.max(t[0],t[1]));
        }
      }
    }
    // Also add tiles currently in play (current trick)
    for(const play of (session.game.current_trick || [])){
      if(Array.isArray(play)){
        const t = play[1];
        if(t) playedTiles.add(Math.min(t[0],t[1]) + ',' + Math.max(t[0],t[1]));
      }
    }
  }

  const isTilePlayedBones = (a, b) => playedTiles.has(Math.min(a,b) + ',' + Math.max(a,b));

  const isTrumpTile = (tile) => {
    if(!session || !session.game) return false;
    return session.game._is_trump_tile(tile);
  };

  // Draw each tile
  for(let rowIdx = 0; rowIdx < rows.length; rowIdx++){
    const row = rows[rowIdx];
    // Offset: each row shifts right by rowIdx positions
    const xOffset = rowIdx * (tileW + gap) / 2;

    for(let colIdx = 0; colIdx < row.length; colIdx++){
      const tile = row[colIdx];
      const x = xOffset + colIdx * (tileW + gap) + gap;
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
}""",
    """function renderBoneyard(){
  const canvas = document.getElementById('bonesCanvas');
  if(!canvas) return;

  const dpr = window.devicePixelRatio || 1;

  // Tile dimensions — shrunk ~15% from original 48x96
  const tileW = 40;
  const tileH = 80;
  const gap = 3;

  // Layout: 8 rows, RIGHT-ALIGNED staircase
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
  }

  // Calculate canvas size
  const maxCols = 8;
  const numRows = 8;
  const canvasW = maxCols * (tileW + gap) + gap;
  const canvasH = numRows * (tileH + gap) + gap;

  canvas.width = canvasW * dpr;
  canvas.height = canvasH * dpr;
  canvas.style.width = canvasW + 'px';
  canvas.style.height = canvasH + 'px';

  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);

  // Background (dark green felt)
  ctx.fillStyle = 'rgba(0,40,0,0.6)';
  ctx.fillRect(0, 0, canvasW, canvasH);

  // Determine played tiles and trump state
  const playedTiles = new Set();

  // Build played set from tricks_team
  if(session && session.game){
    for(let team = 0; team < 2; team++){
      for(const record of (session.game.tricks_team[team] || [])){
        for(let seat = 0; seat < record.length; seat++){
          const t = record[seat];
          if(t) playedTiles.add(Math.min(t[0],t[1]) + ',' + Math.max(t[0],t[1]));
        }
      }
    }
    // Also add tiles currently in play (current trick)
    for(const play of (session.game.current_trick || [])){
      if(Array.isArray(play)){
        const t = play[1];
        if(t) playedTiles.add(Math.min(t[0],t[1]) + ',' + Math.max(t[0],t[1]));
      }
    }
  }

  const isTilePlayedBones = (a, b) => playedTiles.has(Math.min(a,b) + ',' + Math.max(a,b));

  const isTrumpTile = (tile) => {
    if(!session || !session.game) return false;
    return session.game._is_trump_tile(tile);
  };

  // Draw each tile — RIGHT-ALIGNED layout
  // Each row is indented from the LEFT by rowIdx tile-widths.
  // This means the rightmost tile of every row aligns at the same x position.
  for(let rowIdx = 0; rowIdx < rows.length; rowIdx++){
    const row = rows[rowIdx];
    // Indent from left: rowIdx tiles worth of space
    const xIndent = rowIdx * (tileW + gap);

    for(let colIdx = 0; colIdx < row.length; colIdx++){
      const tile = row[colIdx];
      const x = xIndent + colIdx * (tileW + gap) + gap;
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
}""")


# ===========================================================================
# Write output
# ===========================================================================

with open(DST, "w", encoding="utf-8") as f:
    f.write(code)

print(f"\nDone — {patches_applied} patches applied → {DST}")
print(f"Output size: {len(code):,} bytes")
