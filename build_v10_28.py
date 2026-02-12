#!/usr/bin/env python3
"""
V10_28 Build Script — Update defaults to client's values + add inner/outer radius controls
"""

INPUT  = '/var/lib/freelancer/projects/40101953/TN51_Dominoes_V10_27.html'
OUTPUT = '/var/lib/freelancer/projects/40101953/TN51_Dominoes_V10_28.html'

with open(INPUT, 'r', encoding='utf-8') as f:
    src = f.read()

patches = []

# ─── P1: Update HTML defaults + add radius controls ───
old_html = """        <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
          <label style="min-width:80px;">Spacing</label>
          <input type="range" id="bonesGap" min="1" max="12" value="3" style="flex:1;" oninput="updateBonesStyle()">
          <span id="bonesGapVal" style="min-width:20px;text-align:right;">3</span>
        </div>
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
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
          <label style="min-width:80px;">Inner Color</label>
          <input type="color" id="bonesColor" value="#4A9EFF" style="width:40px;height:28px;border:none;background:none;cursor:pointer;" oninput="updateBonesStyle()">
          <span id="bonesColorVal" style="font-size:11px;">#4A9EFF</span>
        </div>
        <div style="display:flex;align-items:center;gap:8px;">
          <label style="min-width:80px;">Outer Color</label>
          <input type="color" id="bonesOuterColor" value="#2563EB" style="width:40px;height:28px;border:none;background:none;cursor:pointer;" oninput="updateBonesStyle()">
          <span id="bonesOuterColorVal" style="font-size:11px;">#2563EB</span>
        </div>"""

new_html = """        <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
          <label style="min-width:80px;">Spacing</label>
          <input type="range" id="bonesGap" min="1" max="12" value="8" style="flex:1;" oninput="updateBonesStyle()">
          <span id="bonesGapVal" style="min-width:20px;text-align:right;">8</span>
        </div>
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
          <label style="min-width:80px;">Inner Size</label>
          <input type="range" id="bonesInnerSize" min="0" max="8" value="1" style="flex:1;" oninput="updateBonesStyle()">
          <span id="bonesInnerSizeVal" style="min-width:20px;text-align:right;">1</span>
        </div>
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
          <label style="min-width:80px;">Inner Radius</label>
          <input type="range" id="bonesInnerRadius" min="0" max="16" value="0" style="flex:1;" oninput="updateBonesStyle()">
          <span id="bonesInnerRadiusVal" style="min-width:20px;text-align:right;">0</span>
        </div>
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
          <label style="min-width:80px;">Outer Size</label>
          <input type="range" id="bonesOuterSize" min="0" max="8" value="3" style="flex:1;" oninput="updateBonesStyle()">
          <span id="bonesOuterSizeVal" style="min-width:20px;text-align:right;">3</span>
        </div>
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
          <label style="min-width:80px;">Outer Radius</label>
          <input type="range" id="bonesOuterRadius" min="0" max="16" value="0" style="flex:1;" oninput="updateBonesStyle()">
          <span id="bonesOuterRadiusVal" style="min-width:20px;text-align:right;">0</span>
        </div>
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
          <label style="min-width:80px;">Inner Color</label>
          <input type="color" id="bonesColor" value="#000000" style="width:40px;height:28px;border:none;background:none;cursor:pointer;" oninput="updateBonesStyle()">
          <span id="bonesColorVal" style="font-size:11px;">#000000</span>
        </div>
        <div style="display:flex;align-items:center;gap:8px;">
          <label style="min-width:80px;">Outer Color</label>
          <input type="color" id="bonesOuterColor" value="#00c4ff" style="width:40px;height:28px;border:none;background:none;cursor:pointer;" oninput="updateBonesStyle()">
          <span id="bonesOuterColorVal" style="font-size:11px;">#00c4ff</span>
        </div>"""

patches.append(('P1: Update HTML defaults + add radius controls', old_html, new_html))

# ─── P2: Update global state defaults ───
old_state = """window._bonesGap = parseInt(localStorage.getItem('tn51_bonesGap')) || 3;
window._bonesInnerSize = parseInt(localStorage.getItem('tn51_bonesInnerSize')) || 2;
window._bonesOuterSize = parseInt(localStorage.getItem('tn51_bonesOuterSize')) || 2;
window._bonesColor = localStorage.getItem('tn51_bonesColor') || '#4A9EFF';
window._bonesOuterColor = localStorage.getItem('tn51_bonesOuterColor') || '#2563EB';"""

new_state = """window._bonesGap = parseInt(localStorage.getItem('tn51_bonesGap')) || 8;
window._bonesInnerSize = parseInt(localStorage.getItem('tn51_bonesInnerSize')) || 1;
window._bonesInnerRadius = parseInt(localStorage.getItem('tn51_bonesInnerRadius') || '0');
window._bonesOuterSize = parseInt(localStorage.getItem('tn51_bonesOuterSize')) || 3;
window._bonesOuterRadius = parseInt(localStorage.getItem('tn51_bonesOuterRadius') || '0');
window._bonesColor = localStorage.getItem('tn51_bonesColor') || '#000000';
window._bonesOuterColor = localStorage.getItem('tn51_bonesOuterColor') || '#00c4ff';"""

patches.append(('P2: Update global state defaults + add radius vars', old_state, new_state))

# ─── P3: Update updateBonesStyle ───
old_update = """  const gapEl = document.getElementById('bonesGap');
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

new_update = """  const gapEl = document.getElementById('bonesGap');
  const innerSizeEl = document.getElementById('bonesInnerSize');
  const innerRadiusEl = document.getElementById('bonesInnerRadius');
  const outerSizeEl = document.getElementById('bonesOuterSize');
  const outerRadiusEl = document.getElementById('bonesOuterRadius');
  const colorEl = document.getElementById('bonesColor');
  const outerColorEl = document.getElementById('bonesOuterColor');
  if(gapEl) window._bonesGap = parseInt(gapEl.value);
  if(innerSizeEl) window._bonesInnerSize = parseInt(innerSizeEl.value);
  if(innerRadiusEl) window._bonesInnerRadius = parseInt(innerRadiusEl.value);
  if(outerSizeEl) window._bonesOuterSize = parseInt(outerSizeEl.value);
  if(outerRadiusEl) window._bonesOuterRadius = parseInt(outerRadiusEl.value);
  if(colorEl) window._bonesColor = colorEl.value;
  if(outerColorEl) window._bonesOuterColor = outerColorEl.value;
  // Update display values
  const gv = document.getElementById('bonesGapVal');
  const isv = document.getElementById('bonesInnerSizeVal');
  const irv = document.getElementById('bonesInnerRadiusVal');
  const osv = document.getElementById('bonesOuterSizeVal');
  const orv = document.getElementById('bonesOuterRadiusVal');
  const cv = document.getElementById('bonesColorVal');
  const ocv = document.getElementById('bonesOuterColorVal');
  if(gv) gv.textContent = window._bonesGap;
  if(isv) isv.textContent = window._bonesInnerSize;
  if(irv) irv.textContent = window._bonesInnerRadius;
  if(osv) osv.textContent = window._bonesOuterSize;
  if(orv) orv.textContent = window._bonesOuterRadius;
  if(cv) cv.textContent = window._bonesColor;
  if(ocv) ocv.textContent = window._bonesOuterColor;
  // Persist
  localStorage.setItem('tn51_bonesGap', window._bonesGap);
  localStorage.setItem('tn51_bonesInnerSize', window._bonesInnerSize);
  localStorage.setItem('tn51_bonesInnerRadius', window._bonesInnerRadius);
  localStorage.setItem('tn51_bonesOuterSize', window._bonesOuterSize);
  localStorage.setItem('tn51_bonesOuterRadius', window._bonesOuterRadius);
  localStorage.setItem('tn51_bonesColor', window._bonesColor);
  localStorage.setItem('tn51_bonesOuterColor', window._bonesOuterColor);"""

patches.append(('P3: Add radius to updateBonesStyle', old_update, new_update))

# ─── P4: Update initBonesControls ───
old_initc = """  const gapEl = document.getElementById('bonesGap');
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

new_initc = """  const gapEl = document.getElementById('bonesGap');
  const innerSizeEl = document.getElementById('bonesInnerSize');
  const innerRadiusEl = document.getElementById('bonesInnerRadius');
  const outerSizeEl = document.getElementById('bonesOuterSize');
  const outerRadiusEl = document.getElementById('bonesOuterRadius');
  const colorEl = document.getElementById('bonesColor');
  const outerColorEl = document.getElementById('bonesOuterColor');
  if(gapEl) gapEl.value = window._bonesGap;
  if(innerSizeEl) innerSizeEl.value = window._bonesInnerSize;
  if(innerRadiusEl) innerRadiusEl.value = window._bonesInnerRadius;
  if(outerSizeEl) outerSizeEl.value = window._bonesOuterSize;
  if(outerRadiusEl) outerRadiusEl.value = window._bonesOuterRadius;
  if(colorEl) colorEl.value = window._bonesColor;
  if(outerColorEl) outerColorEl.value = window._bonesOuterColor;
  const gv = document.getElementById('bonesGapVal');
  const isv = document.getElementById('bonesInnerSizeVal');
  const irv = document.getElementById('bonesInnerRadiusVal');
  const osv = document.getElementById('bonesOuterSizeVal');
  const orv = document.getElementById('bonesOuterRadiusVal');
  const cv = document.getElementById('bonesColorVal');
  const ocv = document.getElementById('bonesOuterColorVal');
  if(gv) gv.textContent = window._bonesGap;
  if(isv) isv.textContent = window._bonesInnerSize;
  if(irv) irv.textContent = window._bonesInnerRadius;
  if(osv) osv.textContent = window._bonesOuterSize;
  if(orv) orv.textContent = window._bonesOuterRadius;
  if(cv) cv.textContent = window._bonesColor;
  if(ocv) ocv.textContent = window._bonesOuterColor;"""

patches.append(('P4: Add radius to initBonesControls', old_initc, new_initc))

# ─── P5: Update renderBoneyard config reads ───
old_config = """  const handInnerSize = window._bonesInnerSize || 2;
  const handOuterSize = window._bonesOuterSize || 2;
  const handInnerColor = window._bonesColor || '#4A9EFF';
  const handOuterColor = window._bonesOuterColor || '#2563EB';"""

new_config = """  const handInnerSize = window._bonesInnerSize != null ? window._bonesInnerSize : 1;
  const handInnerRadius = window._bonesInnerRadius != null ? window._bonesInnerRadius : 0;
  const handOuterSize = window._bonesOuterSize != null ? window._bonesOuterSize : 3;
  const handOuterRadius = window._bonesOuterRadius != null ? window._bonesOuterRadius : 0;
  const handInnerColor = window._bonesColor || '#000000';
  const handOuterColor = window._bonesOuterColor || '#00c4ff';"""

patches.append(('P5: Add radius config reads in renderBoneyard', old_config, new_config))

# ─── P6: Replace border drawing to use roundRectPath with radius ───
old_draw = """      // Border for tiles in player's hand (independent inner + outer size/color)
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

new_draw = """      // Border for tiles in player's hand (independent inner + outer size/color/radius)
      if(inHand){
        // Outer border (drawn outside the tile edges)
        if(handOuterSize > 0){
          ctx.strokeStyle = handOuterColor;
          ctx.lineWidth = handOuterSize;
          const ohw = handOuterSize / 2;
          roundRectPath(ctx, -ohw, -ohw, tileW + handOuterSize, tileH + handOuterSize, handOuterRadius);
          ctx.stroke();
        }
        // Inner border
        if(handInnerSize > 0){
          ctx.strokeStyle = handInnerColor;
          ctx.lineWidth = handInnerSize;
          const ihw = handInnerSize / 2;
          roundRectPath(ctx, ihw, ihw, tileW - handInnerSize, tileH - handInnerSize, handInnerRadius);
          ctx.stroke();
        }
      }"""

patches.append(('P6: Use roundRectPath with radius for borders', old_draw, new_draw))

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
