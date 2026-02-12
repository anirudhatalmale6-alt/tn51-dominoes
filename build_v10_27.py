#!/usr/bin/env python3
"""
V10_27 Build Script — Separate inner/outer border size controls
"""

INPUT  = '/var/lib/freelancer/projects/40101953/TN51_Dominoes_V10_26.html'
OUTPUT = '/var/lib/freelancer/projects/40101953/TN51_Dominoes_V10_27.html'

with open(INPUT, 'r', encoding='utf-8') as f:
    src = f.read()

patches = []

# ─── P1: Replace single "Border" slider with "Inner Size" and "Outer Size" in HTML ───
old_html = """        <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
          <label style="min-width:80px;">Border</label>
          <input type="range" id="bonesBorder" min="1" max="8" value="2" style="flex:1;" oninput="updateBonesStyle()">
          <span id="bonesBorderVal" style="min-width:20px;text-align:right;">2</span>
        </div>
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
          <label style="min-width:80px;">Inner Color</label>"""

new_html = """        <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
          <label style="min-width:80px;">Inner Size</label>
          <input type="range" id="bonesInnerSize" min="0" max="8" value="2" style="flex:1;" oninput="updateBonesStyle()">
          <span id="bonesInnerSizeVal" style="min-width:20px;text-align:right;">2</span>
        </div>
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
          <label style="min-width:80px;">Outer Size</label>
          <input type="range" id="bonesOuterSize" min="0" max="8" value="2" style="flex:1;" oninput="updateBonesStyle()">
          <span id="bonesOuterSizeVal" style="min-width:20px;text-align:right;">2</span>
        </div>
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
          <label style="min-width:80px;">Inner Color</label>"""

patches.append(('P1: Replace single Border slider with Inner Size + Outer Size', old_html, new_html))

# ─── P2: Replace global state init — split _bonesBorder into _bonesInnerSize + _bonesOuterSize ───
old_state = """window._bonesBorder = parseInt(localStorage.getItem('tn51_bonesBorder')) || 2;
window._bonesColor = localStorage.getItem('tn51_bonesColor') || '#4A9EFF';
window._bonesOuterColor = localStorage.getItem('tn51_bonesOuterColor') || '#2563EB';"""

new_state = """window._bonesInnerSize = parseInt(localStorage.getItem('tn51_bonesInnerSize')) || 2;
window._bonesOuterSize = parseInt(localStorage.getItem('tn51_bonesOuterSize')) || 2;
window._bonesColor = localStorage.getItem('tn51_bonesColor') || '#4A9EFF';
window._bonesOuterColor = localStorage.getItem('tn51_bonesOuterColor') || '#2563EB';"""

patches.append(('P2: Split global state into inner/outer size', old_state, new_state))

# ─── P3: Replace updateBonesStyle reads ───
old_update = """  const gapEl = document.getElementById('bonesGap');
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

new_update = """  const gapEl = document.getElementById('bonesGap');
  const innerSizeEl = document.getElementById('bonesInnerSize');
  const outerSizeEl = document.getElementById('bonesOuterSize');
  const colorEl = document.getElementById('bonesColor');
  const outerColorEl = document.getElementById('bonesOuterColor');
  if(gapEl) window._bonesGap = parseInt(gapEl.value);
  if(innerSizeEl) window._bonesInnerSize = parseInt(innerSizeEl.value);
  if(outerSizeEl) window._bonesOuterSize = parseInt(outerSizeEl.value);
  if(colorEl) window._bonesColor = colorEl.value;
  if(outerColorEl) window._bonesOuterColor = outerColorEl.value;
  // Update display values
  const gv = document.getElementById('bonesGapVal');
  const isv = document.getElementById('bonesInnerSizeVal');
  const osv = document.getElementById('bonesOuterSizeVal');
  const cv = document.getElementById('bonesColorVal');
  const ocv = document.getElementById('bonesOuterColorVal');
  if(gv) gv.textContent = window._bonesGap;
  if(isv) isv.textContent = window._bonesInnerSize;
  if(osv) osv.textContent = window._bonesOuterSize;
  if(cv) cv.textContent = window._bonesColor;
  if(ocv) ocv.textContent = window._bonesOuterColor;
  // Persist
  localStorage.setItem('tn51_bonesGap', window._bonesGap);
  localStorage.setItem('tn51_bonesInnerSize', window._bonesInnerSize);
  localStorage.setItem('tn51_bonesOuterSize', window._bonesOuterSize);
  localStorage.setItem('tn51_bonesColor', window._bonesColor);
  localStorage.setItem('tn51_bonesOuterColor', window._bonesOuterColor);"""

patches.append(('P3: Update updateBonesStyle for inner/outer size', old_update, new_update))

# ─── P4: Replace initBonesControls ───
old_initc = """  const gapEl = document.getElementById('bonesGap');
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

new_initc = """  const gapEl = document.getElementById('bonesGap');
  const innerSizeEl = document.getElementById('bonesInnerSize');
  const outerSizeEl = document.getElementById('bonesOuterSize');
  const colorEl = document.getElementById('bonesColor');
  const outerColorEl = document.getElementById('bonesOuterColor');
  if(gapEl) gapEl.value = window._bonesGap;
  if(innerSizeEl) innerSizeEl.value = window._bonesInnerSize;
  if(outerSizeEl) outerSizeEl.value = window._bonesOuterSize;
  if(colorEl) colorEl.value = window._bonesColor;
  if(outerColorEl) outerColorEl.value = window._bonesOuterColor;
  const gv = document.getElementById('bonesGapVal');
  const isv = document.getElementById('bonesInnerSizeVal');
  const osv = document.getElementById('bonesOuterSizeVal');
  const cv = document.getElementById('bonesColorVal');
  const ocv = document.getElementById('bonesOuterColorVal');
  if(gv) gv.textContent = window._bonesGap;
  if(isv) isv.textContent = window._bonesInnerSize;
  if(osv) osv.textContent = window._bonesOuterSize;
  if(cv) cv.textContent = window._bonesColor;
  if(ocv) ocv.textContent = window._bonesOuterColor;"""

patches.append(('P4: Update initBonesControls for inner/outer size', old_initc, new_initc))

# ─── P5: Replace renderBoneyard config reads ───
old_config = """  const handBorderWidth = window._bonesBorder || 2;
  const handBorderColor = window._bonesColor || '#4A9EFF';
  const handOuterColor = window._bonesOuterColor || '#2563EB';"""

new_config = """  const handInnerSize = window._bonesInnerSize || 2;
  const handOuterSize = window._bonesOuterSize || 2;
  const handInnerColor = window._bonesColor || '#4A9EFF';
  const handOuterColor = window._bonesOuterColor || '#2563EB';"""

patches.append(('P5: Split renderBoneyard config into inner/outer size', old_config, new_config))

# ─── P6: Replace border drawing code ───
old_draw = """      // Border for tiles in player's hand (configurable inner + outer)
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

new_draw = """      // Border for tiles in player's hand (independent inner + outer size/color)
      if(inHand){
        // Outer border (drawn outside the tile edges)
        if(handOuterSize > 0){
          ctx.strokeStyle = handOuterColor;
          ctx.lineWidth = handOuterSize;
          const ohw = handOuterSize / 2;
          ctx.strokeRect(-ohw, -ohw, tileW + handOuterSize, tileH + handOuterSize);
        }
        // Inner border
        if(handInnerSize > 0){
          ctx.strokeStyle = handInnerColor;
          ctx.lineWidth = handInnerSize;
          const ihw = handInnerSize / 2;
          ctx.strokeRect(ihw, ihw, tileW - handInnerSize, tileH - handInnerSize);
        }
      }"""

patches.append(('P6: Use independent inner/outer sizes in border drawing', old_draw, new_draw))

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
