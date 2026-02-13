#!/usr/bin/env python3
"""Build V10_44 from V10_43:
1. Fix boneyard PP mode — show current player's hand, not always P1
2. Add Boneyard 2 — inline boneyard overlay on trick history with bone icon toggle
   - Same layout as current boneyard but tiles rotated 90° CCW (landscape)
   - Sized to match trick history area
   - Bone icon to toggle on/off
   - Hides trick history when visible
   - Controls: spacing, border sizes/radii/colors, in-hand opacity slider
"""
import re, sys

INPUT = 'TN51_Dominoes_V10_43.html'
OUTPUT = 'TN51_Dominoes_V10_44.html'

with open(INPUT, 'r', encoding='utf-8') as f:
    html = f.read()

patches_applied = 0

# ============================================================
# PATCH 1: Fix boneyard PP mode — show current player's hand
# ============================================================
old_boneyard_hand = """  // Build set of tiles in player's hand (seat 0)
  const handTiles = new Set();
  if(session && session.game && session.game.hands[0]){
    for(const t of session.game.hands[0]){
      if(t) handTiles.add(Math.min(t[0],t[1]) + ',' + Math.max(t[0],t[1]));
    }
  }"""

new_boneyard_hand = """  // Build set of tiles in current player's hand (PP-aware)
  const handSeat = PASS_AND_PLAY_MODE ? ppActiveViewSeat : 0;
  const handTiles = new Set();
  if(session && session.game && session.game.hands[handSeat]){
    for(const t of session.game.hands[handSeat]){
      if(t) handTiles.add(Math.min(t[0],t[1]) + ',' + Math.max(t[0],t[1]));
    }
  }"""

if old_boneyard_hand in html:
    html = html.replace(old_boneyard_hand, new_boneyard_hand, 1)
    patches_applied += 1
    print("PATCH 1 applied: Boneyard PP mode hand fix")
else:
    print("ERROR: Could not find boneyard hand detection code")
    sys.exit(1)

# ============================================================
# PATCH 2: Add Boneyard 2 CSS
# ============================================================
# Insert after #trickHistoryBg CSS block
old_css_anchor = """  #shadowLayer{position:absolute; inset:0; pointer-events:none; z-index:15;}"""

new_css = """  /* Boneyard 2 — inline overlay on trick history */
  #boneyard2Container{
    position:absolute;
    left: var(--th-left, 5%);
    top: var(--th-top, 16%);
    width: var(--th-width, 90%);
    pointer-events: none;
    z-index: 6;
    display: none;
  }
  #boneyard2Canvas{
    width: 100%;
    display: block;
  }
  #boneyard2Toggle{
    position:absolute;
    left: 1%;
    top: 16%;
    width: 24px;
    height: 24px;
    z-index: 7;
    cursor: pointer;
    font-size: 18px;
    line-height: 24px;
    text-align: center;
    opacity: 0.6;
    transition: opacity 0.2s;
    pointer-events: auto;
    user-select: none;
    -webkit-user-select: none;
  }
  #boneyard2Toggle:hover{ opacity: 1; }
  #boneyard2Toggle.active{ opacity: 1; }
  /* Boneyard 2 settings gear + panel */
  #by2SettingsBtn{
    position:absolute;
    right: 4px;
    top: 4px;
    background: none;
    border: none;
    color: rgba(255,255,255,0.15);
    font-size: 16px;
    cursor: pointer;
    padding: 2px;
    z-index: 8;
    pointer-events: auto;
  }
  #by2SettingsBtn:hover{ color: rgba(255,255,255,0.5); }
  #by2Controls{
    display: none;
    position: absolute;
    right: 0;
    top: 28px;
    background: rgba(0,20,0,0.92);
    border-radius: 8px;
    padding: 8px 10px;
    font-size: 11px;
    color: #fff;
    z-index: 9;
    pointer-events: auto;
    min-width: 220px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.5);
  }
  .by2Row{ display:flex; align-items:center; gap:6px; margin-bottom:4px; }
  .by2Row label{ min-width:70px; font-size:11px; }
  .by2Row input[type=range]{ flex:1; height:14px; }
  .by2Row input[type=color]{ width:30px; height:20px; border:none; background:none; cursor:pointer; }
  .by2Row span{ min-width:18px; text-align:right; font-size:10px; }
  """ + old_css_anchor

if old_css_anchor in html:
    html = html.replace(old_css_anchor, new_css, 1)
    patches_applied += 1
    print("PATCH 2 applied: Boneyard 2 CSS")
else:
    print("ERROR: Could not find CSS anchor")
    sys.exit(1)

# ============================================================
# PATCH 3: Add Boneyard 2 HTML elements
# ============================================================
# Insert after trickHistoryBg div
old_html_anchor = """  <!-- Trick History Background - darkened area for indentation effect -->
  <div id="trickHistoryBg"></div>"""

new_html = old_html_anchor + """
  <!-- Boneyard 2 — inline overlay -->
  <div id="boneyard2Container">
    <canvas id="boneyard2Canvas"></canvas>
    <button id="by2SettingsBtn" onclick="document.getElementById('by2Controls').style.display=document.getElementById('by2Controls').style.display==='none'?'block':'none';">&#9881;</button>
    <div id="by2Controls">
      <div class="by2Row"><label>Spacing</label><input type="range" id="by2Gap" min="0" max="8" value="2" oninput="updateBY2Style()"><span id="by2GapVal">2</span></div>
      <div class="by2Row"><label>Inner Size</label><input type="range" id="by2InnerSize" min="0" max="6" value="1" oninput="updateBY2Style()"><span id="by2InnerSizeVal">1</span></div>
      <div class="by2Row"><label>Inner Radius</label><input type="range" id="by2InnerRadius" min="0" max="12" value="4" oninput="updateBY2Style()"><span id="by2InnerRadiusVal">4</span></div>
      <div class="by2Row"><label>Outer Size</label><input type="range" id="by2OuterSize" min="0" max="6" value="2" oninput="updateBY2Style()"><span id="by2OuterSizeVal">2</span></div>
      <div class="by2Row"><label>Outer Radius</label><input type="range" id="by2OuterRadius" min="0" max="12" value="6" oninput="updateBY2Style()"><span id="by2OuterRadiusVal">6</span></div>
      <div class="by2Row"><label>Inner Color</label><input type="color" id="by2InnerColor" value="#beb6ab" oninput="updateBY2Style()"><span id="by2InnerColorVal" style="font-size:10px;">#beb6ab</span></div>
      <div class="by2Row"><label>Outer Color</label><input type="color" id="by2OuterColor" value="#00deff" oninput="updateBY2Style()"><span id="by2OuterColorVal" style="font-size:10px;">#00deff</span></div>
      <div class="by2Row"><label>Hand Opacity</label><input type="range" id="by2HandOpacity" min="30" max="100" value="70" oninput="updateBY2Style()"><span id="by2HandOpacityVal">70%</span></div>
    </div>
  </div>
  <!-- Boneyard 2 toggle icon -->
  <div id="boneyard2Toggle">&#129472;</div>"""

if old_html_anchor in html:
    html = html.replace(old_html_anchor, new_html, 1)
    patches_applied += 1
    print("PATCH 3 applied: Boneyard 2 HTML")
else:
    print("ERROR: Could not find HTML anchor")
    sys.exit(1)

# ============================================================
# PATCH 4: Add Boneyard 2 JavaScript (renderBoneyard2, controls, toggle)
# ============================================================
# Insert right before the existing renderBoneyard function
old_js_anchor = """function renderBoneyard(){"""

boneyard2_js = """// ============================================================
// BONEYARD 2 — Inline overlay on trick history area
// ============================================================
// Style state (separate from full boneyard modal)
window._by2Gap = 2;
window._by2InnerSize = 1;
window._by2InnerRadius = 4;
window._by2OuterSize = 2;
window._by2OuterRadius = 6;
window._by2InnerColor = '#beb6ab';
window._by2OuterColor = '#00deff';
window._by2HandOpacity = 70;
let boneyard2Visible = false;

function updateBY2Style(){
  const ids = ['by2Gap','by2InnerSize','by2InnerRadius','by2OuterSize','by2OuterRadius','by2InnerColor','by2OuterColor','by2HandOpacity'];
  const keys = ['_by2Gap','_by2InnerSize','_by2InnerRadius','_by2OuterSize','_by2OuterRadius','_by2InnerColor','_by2OuterColor','_by2HandOpacity'];
  for(let i = 0; i < ids.length; i++){
    const el = document.getElementById(ids[i]);
    if(!el) continue;
    if(el.type === 'color') window[keys[i]] = el.value;
    else window[keys[i]] = parseInt(el.value);
    const valEl = document.getElementById(ids[i] + 'Val');
    if(valEl){
      if(el.type === 'color') valEl.textContent = el.value;
      else if(ids[i] === 'by2HandOpacity') valEl.textContent = el.value + '%';
      else valEl.textContent = el.value;
    }
  }
  if(boneyard2Visible) renderBoneyard2();
}

function toggleBoneyard2(){
  boneyard2Visible = !boneyard2Visible;
  const container = document.getElementById('boneyard2Container');
  const thBg = document.getElementById('trickHistoryBg');
  const toggleBtn = document.getElementById('boneyard2Toggle');
  if(boneyard2Visible){
    // Hide trick history background and all trick history sprites
    if(thBg) thBg.style.display = 'none';
    hideTrickHistorySprites();
    container.style.display = 'block';
    toggleBtn.classList.add('active');
    renderBoneyard2();
  } else {
    container.style.display = 'none';
    // Close settings panel too
    document.getElementById('by2Controls').style.display = 'none';
    // Restore trick history
    if(thBg) thBg.style.display = '';
    showTrickHistorySprites();
    toggleBtn.classList.remove('active');
  }
}

function hideTrickHistorySprites(){
  // Hide domino sprites that are positioned in the trick history area
  const tableRect = document.getElementById('tableMain').getBoundingClientRect();
  const thLeft = 0.03;
  const thRight = 0.97;
  const thTop = 0.14;
  const thBottom = 0.40;

  const spriteEls = document.querySelectorAll('#spriteLayer .dominoSprite');
  spriteEls.forEach(el => {
    if(el._pose){
      const nx = el._pose.x / tableRect.width;
      const ny = el._pose.y / tableRect.height;
      if(nx >= thLeft && nx <= thRight && ny >= thTop && ny <= thBottom){
        el._by2Hidden = true;
        el.style.display = 'none';
      }
    }
  });
}

function showTrickHistorySprites(){
  const spriteEls = document.querySelectorAll('#spriteLayer .dominoSprite');
  spriteEls.forEach(el => {
    if(el._by2Hidden){
      el._by2Hidden = false;
      el.style.display = '';
    }
  });
}

function renderBoneyard2(){
  const canvas = document.getElementById('boneyard2Canvas');
  const container = document.getElementById('boneyard2Container');
  if(!canvas || !container) return;

  const dpr = window.devicePixelRatio || 1;

  // Read controls
  const gap = window._by2Gap;
  const handInnerSize = window._by2InnerSize;
  const handInnerRadius = window._by2InnerRadius;
  const handOuterSize = window._by2OuterSize;
  const handOuterRadius = window._by2OuterRadius;
  const handInnerColor = window._by2InnerColor;
  const handOuterColor = window._by2OuterColor;
  const handOpacity = window._by2HandOpacity / 100;

  // Use trick history grid positions to derive tile sizes and spacing
  // This ensures the boneyard perfectly overlays the trick history area
  const tableEl = document.getElementById('tableMain');
  if(!tableEl) return;
  const tableW = tableEl.offsetWidth;
  const tableH = tableEl.offsetHeight;
  const containerW = container.offsetWidth;
  if(containerW <= 0) return;

  // Trick history normalized positions (from LAYOUT.sections Trick_History):
  // Columns at xN: 0.106, 0.2171, 0.3282, 0.4393, 0.5504, 0.6616, 0.7727, 0.8838
  // Rows at yN: 0.197, 0.2281, 0.2592, 0.2904, 0.3215, 0.3526
  // These are CENTER positions of trick history tiles
  const thColXN = [0.106, 0.2171, 0.3282, 0.4393, 0.5504, 0.6616, 0.7727, 0.8838];
  const thRowYN = [0.197, 0.2281, 0.2592, 0.2904, 0.3215, 0.3526];

  // Calculate column spacing and row spacing from the grid
  const colSpacing = (thColXN[7] - thColXN[0]) / 7 * tableW;  // px between column centers
  const rowSpacing = (thRowYN[5] - thRowYN[0]) / 5 * tableH;  // px between row centers

  // Trick history tile size: scale 0.393 of 56x112, rotated 270° (landscape)
  // Rendered size: ~44px wide x ~22px tall
  const thScale = 0.393;
  const cellW = Math.round(BASE_H * thScale);  // 112 * 0.393 ≈ 44 (landscape width)
  const cellH = Math.round(BASE_W * thScale);   // 56 * 0.393 ≈ 22 (landscape height)

  // Container is positioned at --th-left (5%) inside tableMain
  // So we need to offset positions relative to the container's left edge
  const containerLeft = tableW * 0.05;  // container starts at 5% of table
  const containerTop = 0;  // container top IS the trick history top

  // Convert trick history center positions to container-relative positions
  // First column center X in container coords
  const col0X = thColXN[0] * tableW - containerLeft;

  // The trick history top (yN=0.197) is relative to tableMain
  // Container top = --th-top (16%) of tableMain
  const containerTopOffset = tableH * 0.16;  // container is at 16% of table height
  const row0Y = thRowYN[0] * tableH - containerTopOffset;

  // Now we know: boneyard rows 0-5 align with trick history rows 0-5
  // Rows 6-7 extend below with same rowSpacing
  const maxCols = 8;
  const numRows = 8;

  // Canvas height needs to accommodate all 8 rows
  const lastRowY = row0Y + (numRows - 1) * rowSpacing + cellH / 2;
  const canvasH = Math.max(lastRowY + gap + cellH, (numRows - 1) * rowSpacing + cellH + row0Y + 4);

  canvas.width = Math.round(containerW * dpr);
  canvas.height = Math.round(canvasH * dpr);
  canvas.style.width = containerW + 'px';
  canvas.style.height = canvasH + 'px';

  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);

  // Clear (transparent — natural green shows through)
  ctx.clearRect(0, 0, containerW, canvasH);

  // Build the grid: same layout as main boneyard
  const rows = [];
  const doublesRow = [];
  for(let pip = 7; pip >= 0; pip--) doublesRow.push([pip, pip]);
  rows.push(doublesRow);
  for(let suit = 7; suit >= 1; suit--){
    const row = [];
    for(let low = suit - 1; low >= 0; low--) row.push([suit, low]);
    rows.push(row);
  }

  // Determine played tiles and trump state
  const playedTiles = new Set();
  if(session && session.game){
    for(let team = 0; team < 2; team++){
      for(const record of (session.game.tricks_team[team] || [])){
        for(let seat = 0; seat < record.length; seat++){
          const t = record[seat];
          if(t) playedTiles.add(Math.min(t[0],t[1]) + ',' + Math.max(t[0],t[1]));
        }
      }
    }
    for(const play of (session.game.current_trick || [])){
      if(Array.isArray(play)){
        const t = play[1];
        if(t) playedTiles.add(Math.min(t[0],t[1]) + ',' + Math.max(t[0],t[1]));
      }
    }
  }
  const isTilePlayed = (a, b) => playedTiles.has(Math.min(a,b) + ',' + Math.max(a,b));
  const isTrumpTile = (tile) => {
    if(!session || !session.game) return false;
    return session.game._is_trump_tile(tile);
  };

  // Build hand tile set (PP-aware)
  const handSeat = PASS_AND_PLAY_MODE ? ppActiveViewSeat : 0;
  const handTiles = new Set();
  if(session && session.game && session.game.hands[handSeat]){
    for(const t of session.game.hands[handSeat]){
      if(t) handTiles.add(Math.min(t[0],t[1]) + ',' + Math.max(t[0],t[1]));
    }
  }
  const isTileInHand = (a, b) => handTiles.has(Math.min(a,b) + ',' + Math.max(a,b));

  // Apply gap as additional spacing between tiles (added to base grid spacing)
  // gap=0 means tiles use exact trick history positions, gap>0 adds extra padding
  // We reduce cellW/cellH to create visual spacing while keeping positions the same
  const effectiveCellW = Math.max(10, cellW - gap);
  const effectiveCellH = Math.max(5, cellH - gap);

  // Draw each tile — landscape orientation (rotated 90° CCW from portrait)
  for(let rowIdx = 0; rowIdx < rows.length; rowIdx++){
    const row = rows[rowIdx];
    const colOffset = maxCols - row.length;  // right-align within grid

    for(let colIdx = 0; colIdx < row.length; colIdx++){
      const tile = row[colIdx];
      const col = colOffset + colIdx;

      // Position: center of this cell aligns with trick history grid position
      const centerX = col0X + col * colSpacing;
      const centerY = row0Y + rowIdx * rowSpacing;
      const x = centerX - effectiveCellW / 2;
      const y = centerY - effectiveCellH / 2;

      const played = isTilePlayed(tile[0], tile[1]);
      const trump = isTrumpTile(tile);
      const inHand = isTileInHand(tile[0], tile[1]);

      ctx.save();
      ctx.translate(x, y);

      // Set opacity for in-hand tiles (ghost effect)
      if(inHand){
        ctx.globalAlpha = handOpacity;
      }

      // Draw the domino face rotated 90° CCW
      // Portrait canvas (effectiveCellH wide x effectiveCellW tall), draw face, then rotate
      const portraitW = effectiveCellH;
      const portraitH = effectiveCellW;

      const tileCanvas = document.createElement('canvas');
      tileCanvas.width = Math.round(portraitW * dpr);
      tileCanvas.height = Math.round(portraitH * dpr);
      const tctx = tileCanvas.getContext('2d');
      tctx.scale(dpr, dpr);
      drawFace(tctx, tile, portraitW, portraitH, trump, !played);

      // Rotate 90° CCW around cell center and draw
      ctx.translate(effectiveCellW / 2, effectiveCellH / 2);
      ctx.rotate(-Math.PI / 2);
      ctx.drawImage(tileCanvas, -portraitW / 2, -portraitH / 2, portraitW, portraitH);

      // Reset transform to cell origin for borders
      ctx.setTransform(dpr, 0, 0, dpr, x * dpr, y * dpr);

      // Reset alpha for borders
      ctx.globalAlpha = 1.0;

      // Border for tiles in player's hand
      if(inHand){
        if(handOuterSize > 0){
          ctx.strokeStyle = handOuterColor;
          ctx.lineWidth = handOuterSize;
          const ohw = handOuterSize / 2;
          roundRectPath(ctx, -ohw, -ohw, effectiveCellW + handOuterSize, effectiveCellH + handOuterSize, handOuterRadius);
          ctx.stroke();
        }
        if(handInnerSize > 0){
          ctx.strokeStyle = handInnerColor;
          ctx.lineWidth = handInnerSize;
          const ihw = handInnerSize / 2;
          roundRectPath(ctx, ihw, ihw, effectiveCellW - handInnerSize, effectiveCellH - handInnerSize, handInnerRadius);
          ctx.stroke();
        }
      }

      ctx.restore();
    }
  }
}

// Toggle button handler
document.getElementById('boneyard2Toggle').addEventListener('click', toggleBoneyard2);
document.getElementById('boneyard2Toggle').addEventListener('touchstart', (e) => {
  e.preventDefault();
  toggleBoneyard2();
}, { passive: false });

// Re-render on resize if visible
window.addEventListener('resize', () => {
  if(boneyard2Visible) renderBoneyard2();
});

// ============================================================
// END BONEYARD 2
// ============================================================

""" + old_js_anchor

if old_js_anchor in html:
    html = html.replace(old_js_anchor, boneyard2_js, 1)
    patches_applied += 1
    print("PATCH 4 applied: Boneyard 2 JavaScript")
else:
    print("ERROR: Could not find JS anchor for renderBoneyard")
    sys.exit(1)

# ============================================================
# PATCH 5: Update Boneyard 2 when trick completes (auto-refresh)
# ============================================================
# After autoSave() in collectToHistory, re-render boneyard2 if visible
old_autosave_collect = """  // Auto-save after each trick
  autoSave();

  playedThisTrick = [];
  currentTrick++;
}"""

new_autosave_collect = """  // Auto-save after each trick
  autoSave();

  // Refresh boneyard 2 if visible
  if(boneyard2Visible) renderBoneyard2();

  playedThisTrick = [];
  currentTrick++;
}"""

if old_autosave_collect in html:
    html = html.replace(old_autosave_collect, new_autosave_collect, 1)
    patches_applied += 1
    print("PATCH 5 applied: Boneyard 2 auto-refresh on trick complete")
else:
    print("ERROR: Could not find autoSave collect anchor")
    sys.exit(1)

# ============================================================
# PATCH 6: Also refresh Boneyard 2 after a tile is played (immediate feedback)
# ============================================================
# After a player plays a tile and autoSave is called in the main play handler
# Find the autoSave() call after tile play confirmation
old_play_autosave = """  autoSave();
}

// Find the current slot index for a sprite element"""

new_play_autosave = """  autoSave();
  // Refresh boneyard 2 if visible
  if(boneyard2Visible) renderBoneyard2();
}

// Find the current slot index for a sprite element"""

if old_play_autosave in html:
    html = html.replace(old_play_autosave, new_play_autosave, 1)
    patches_applied += 1
    print("PATCH 6 applied: Boneyard 2 refresh after tile play")
else:
    print("WARNING: Could not find play autoSave anchor for patch 6 (non-critical)")

# ============================================================
# PATCH 7: Hide Boneyard 2 when starting a new hand
# ============================================================
old_start_hand = """function startNewHand(){"""

new_start_hand = """function startNewHand(){
  // Hide boneyard 2 overlay when new hand starts
  if(boneyard2Visible){
    boneyard2Visible = false;
    const by2c = document.getElementById('boneyard2Container');
    const thBg = document.getElementById('trickHistoryBg');
    const toggleBtn = document.getElementById('boneyard2Toggle');
    if(by2c) by2c.style.display = 'none';
    if(thBg) thBg.style.display = '';
    if(toggleBtn) toggleBtn.classList.remove('active');
    document.getElementById('by2Controls').style.display = 'none';
  }"""

if old_start_hand in html:
    html = html.replace(old_start_hand, new_start_hand, 1)
    patches_applied += 1
    print("PATCH 7 applied: Hide Boneyard 2 on new hand")
else:
    print("ERROR: Could not find startNewHand anchor")
    sys.exit(1)

# ============================================================
# Update version string
# ============================================================
old_version = 'V10_43'
new_version = 'V10_44'
# Replace version in the title and any version display
html = html.replace('TN51 Dominoes V10_43', 'TN51 Dominoes V10_44')
html = html.replace("'V10_43'", "'V10_44'")
html = html.replace('"V10_43"', '"V10_44"')
print(f"Version updated: {old_version} -> {new_version}")

# Write output
with open(OUTPUT, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\nTotal patches applied: {patches_applied}")
print(f"Output: {OUTPUT} ({len(html):,} bytes)")
