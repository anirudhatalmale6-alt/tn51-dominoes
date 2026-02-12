#!/usr/bin/env python3
"""
V10_26 Build Script — Add outside border for hand tiles + separate color control
"""

INPUT  = '/var/lib/freelancer/projects/40101953/TN51_Dominoes_V10_25.html'
OUTPUT = '/var/lib/freelancer/projects/40101953/TN51_Dominoes_V10_26.html'

with open(INPUT, 'r', encoding='utf-8') as f:
    src = f.read()

patches = []

# ─── P1: Add outer color control to HTML ───
old_html = """        <div style="display:flex;align-items:center;gap:8px;">
          <label style="min-width:80px;">Color</label>
          <input type="color" id="bonesColor" value="#4A9EFF" style="width:40px;height:28px;border:none;background:none;cursor:pointer;" oninput="updateBonesStyle()">
          <span id="bonesColorVal" style="font-size:11px;">#4A9EFF</span>
        </div>"""

new_html = """        <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
          <label style="min-width:80px;">Inner Color</label>
          <input type="color" id="bonesColor" value="#4A9EFF" style="width:40px;height:28px;border:none;background:none;cursor:pointer;" oninput="updateBonesStyle()">
          <span id="bonesColorVal" style="font-size:11px;">#4A9EFF</span>
        </div>
        <div style="display:flex;align-items:center;gap:8px;">
          <label style="min-width:80px;">Outer Color</label>
          <input type="color" id="bonesOuterColor" value="#2563EB" style="width:40px;height:28px;border:none;background:none;cursor:pointer;" oninput="updateBonesStyle()">
          <span id="bonesOuterColorVal" style="font-size:11px;">#2563EB</span>
        </div>"""

patches.append(('P1: Add outer color control to boneyard controls HTML', old_html, new_html))

# ─── P2: Add outer color to global state + localStorage init ───
old_init = """window._bonesColor = localStorage.getItem('tn51_bonesColor') || '#4A9EFF';"""

new_init = """window._bonesColor = localStorage.getItem('tn51_bonesColor') || '#4A9EFF';
window._bonesOuterColor = localStorage.getItem('tn51_bonesOuterColor') || '#2563EB';"""

patches.append(('P2: Add outer color to global state init', old_init, new_init))

# ─── P3: Add outer color to updateBonesStyle function ───
old_update = """  const gapEl = document.getElementById('bonesGap');
  const borderEl = document.getElementById('bonesBorder');
  const colorEl = document.getElementById('bonesColor');
  if(gapEl) window._bonesGap = parseInt(gapEl.value);
  if(borderEl) window._bonesBorder = parseInt(borderEl.value);
  if(colorEl) window._bonesColor = colorEl.value;
  // Update display values
  const gv = document.getElementById('bonesGapVal');
  const bv = document.getElementById('bonesBorderVal');
  const cv = document.getElementById('bonesColorVal');
  if(gv) gv.textContent = window._bonesGap;
  if(bv) bv.textContent = window._bonesBorder;
  if(cv) cv.textContent = window._bonesColor;
  // Persist
  localStorage.setItem('tn51_bonesGap', window._bonesGap);
  localStorage.setItem('tn51_bonesBorder', window._bonesBorder);
  localStorage.setItem('tn51_bonesColor', window._bonesColor);"""

new_update = """  const gapEl = document.getElementById('bonesGap');
  const borderEl = document.getElementById('bonesBorder');
  const colorEl = document.getElementById('bonesColor');
  const outerColorEl = document.getElementById('bonesOuterColor');
  if(gapEl) window._bonesGap = parseInt(gapEl.value);
  if(borderEl) window._bonesBorder = parseInt(borderEl.value);
  if(colorEl) window._bonesColor = colorEl.value;
  if(outerColorEl) window._bonesOuterColor = outerColorEl.value;
  // Update display values
  const gv = document.getElementById('bonesGapVal');
  const bv = document.getElementById('bonesBorderVal');
  const cv = document.getElementById('bonesColorVal');
  const ocv = document.getElementById('bonesOuterColorVal');
  if(gv) gv.textContent = window._bonesGap;
  if(bv) bv.textContent = window._bonesBorder;
  if(cv) cv.textContent = window._bonesColor;
  if(ocv) ocv.textContent = window._bonesOuterColor;
  // Persist
  localStorage.setItem('tn51_bonesGap', window._bonesGap);
  localStorage.setItem('tn51_bonesBorder', window._bonesBorder);
  localStorage.setItem('tn51_bonesColor', window._bonesColor);
  localStorage.setItem('tn51_bonesOuterColor', window._bonesOuterColor);"""

patches.append(('P3: Add outer color to updateBonesStyle', old_update, new_update))

# ─── P4: Add outer color to initBonesControls ───
old_initc = """  const gapEl = document.getElementById('bonesGap');
  const borderEl = document.getElementById('bonesBorder');
  const colorEl = document.getElementById('bonesColor');
  if(gapEl) gapEl.value = window._bonesGap;
  if(borderEl) borderEl.value = window._bonesBorder;
  if(colorEl) colorEl.value = window._bonesColor;
  const gv = document.getElementById('bonesGapVal');
  const bv = document.getElementById('bonesBorderVal');
  const cv = document.getElementById('bonesColorVal');
  if(gv) gv.textContent = window._bonesGap;
  if(bv) bv.textContent = window._bonesBorder;
  if(cv) cv.textContent = window._bonesColor;"""

new_initc = """  const gapEl = document.getElementById('bonesGap');
  const borderEl = document.getElementById('bonesBorder');
  const colorEl = document.getElementById('bonesColor');
  const outerColorEl = document.getElementById('bonesOuterColor');
  if(gapEl) gapEl.value = window._bonesGap;
  if(borderEl) borderEl.value = window._bonesBorder;
  if(colorEl) colorEl.value = window._bonesColor;
  if(outerColorEl) outerColorEl.value = window._bonesOuterColor;
  const gv = document.getElementById('bonesGapVal');
  const bv = document.getElementById('bonesBorderVal');
  const cv = document.getElementById('bonesColorVal');
  const ocv = document.getElementById('bonesOuterColorVal');
  if(gv) gv.textContent = window._bonesGap;
  if(bv) bv.textContent = window._bonesBorder;
  if(cv) cv.textContent = window._bonesColor;
  if(ocv) ocv.textContent = window._bonesOuterColor;"""

patches.append(('P4: Add outer color to initBonesControls', old_initc, new_initc))

# ─── P5: Add outer color to renderBoneyard config reads ───
old_config = """  const handBorderWidth = window._bonesBorder || 2;
  const handBorderColor = window._bonesColor || '#4A9EFF';"""

new_config = """  const handBorderWidth = window._bonesBorder || 2;
  const handBorderColor = window._bonesColor || '#4A9EFF';
  const handOuterColor = window._bonesOuterColor || '#2563EB';"""

patches.append(('P5: Add outer color read in renderBoneyard', old_config, new_config))

# ─── P6: Draw outside border around hand tiles ───
old_draw = """      // Border for tiles in player's hand (configurable)
      if(inHand){
        ctx.strokeStyle = handBorderColor;
        ctx.lineWidth = handBorderWidth;
        const hw = handBorderWidth / 2;
        ctx.strokeRect(hw, hw, tileW - handBorderWidth, tileH - handBorderWidth);
      }"""

new_draw = """      // Border for tiles in player's hand (configurable inner + outer)
      if(inHand){
        // Outer border (drawn outside the tile edges)
        ctx.strokeStyle = handOuterColor;
        ctx.lineWidth = handBorderWidth;
        const ohw = handBorderWidth / 2;
        ctx.strokeRect(-ohw, -ohw, tileW + handBorderWidth, tileH + handBorderWidth);
        // Inner border
        ctx.strokeStyle = handBorderColor;
        ctx.lineWidth = handBorderWidth;
        const ihw = handBorderWidth / 2;
        ctx.strokeRect(ihw, ihw, tileW - handBorderWidth, tileH - handBorderWidth);
      }"""

patches.append(('P6: Draw outer + inner border for hand tiles', old_draw, new_draw))

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

print(f'\nApplied {ok}/{len(patches)} patches → {OUTPUT}')
