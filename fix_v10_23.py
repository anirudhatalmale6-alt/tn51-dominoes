#!/usr/bin/env python3
"""Fix duplicate maxCols declaration in V10_23"""

INPUT = '/var/lib/freelancer/projects/40101953/TN51_Dominoes_V10_23.html'

with open(INPUT, 'r', encoding='utf-8') as f:
    src = f.read()

old = """  // Draw each tile — ROW layout, RIGHT-ALIGNED
  // Row 0 (doubles) = 8 tiles, rows 1-7 have decreasing count.
  // Right-align: offset each row so its last tile aligns with column 7.
  const maxCols = 8;
  for(let rowIdx = 0; rowIdx < rows.length; rowIdx++){"""

new = """  // Draw each tile — ROW layout, RIGHT-ALIGNED
  // Row 0 (doubles) = 8 tiles, rows 1-7 have decreasing count.
  // Right-align: offset each row so its last tile aligns with column 7.
  for(let rowIdx = 0; rowIdx < rows.length; rowIdx++){"""

if old in src:
    src = src.replace(old, new, 1)
    print('OK: Removed duplicate maxCols declaration')
else:
    print('FAILED: old string not found')

with open(INPUT, 'w', encoding='utf-8') as f:
    f.write(src)
