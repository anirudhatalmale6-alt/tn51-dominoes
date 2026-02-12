#!/usr/bin/env python3
"""
V10_25 Build Script — Boneyard style controls (spacing, border thickness, color)
"""

INPUT  = '/var/lib/freelancer/projects/40101953/TN51_Dominoes_V10_24.html'
OUTPUT = '/var/lib/freelancer/projects/40101953/TN51_Dominoes_V10_25.html'

with open(INPUT, 'r', encoding='utf-8') as f:
    src = f.read()

patches = []

# ─── P1: Add settings gear icon + controls panel to boneyard modal HTML ───
old_html = """    <canvas id="bonesCanvas" style="width:100%;border-radius:8px;"></canvas>
  </div>
</div>"""

new_html = """    <canvas id="bonesCanvas" style="width:100%;border-radius:8px;"></canvas>
    <!-- Boneyard Style Controls -->
    <div style="position:relative;">
      <button id="bonesSettingsBtn" onclick="document.getElementById('bonesControls').style.display=document.getElementById('bonesControls').style.display==='none'?'block':'none';" style="position:absolute;bottom:8px;right:8px;background:none;border:none;color:rgba(255,255,255,0.5);font-size:20px;cursor:pointer;padding:4px;">&#9881;</button>
      <div id="bonesControls" style="display:none;padding:8px 4px;font-size:13px;color:#fff;">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
          <label style="min-width:80px;">Spacing</label>
          <input type="range" id="bonesGap" min="1" max="12" value="3" style="flex:1;" oninput="updateBonesStyle()">
          <span id="bonesGapVal" style="min-width:20px;text-align:right;">3</span>
        </div>
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
          <label style="min-width:80px;">Border</label>
          <input type="range" id="bonesBorder" min="1" max="8" value="2" style="flex:1;" oninput="updateBonesStyle()">
          <span id="bonesBorderVal" style="min-width:20px;text-align:right;">2</span>
        </div>
        <div style="display:flex;align-items:center;gap:8px;">
          <label style="min-width:80px;">Color</label>
          <input type="color" id="bonesColor" value="#4A9EFF" style="width:40px;height:28px;border:none;background:none;cursor:pointer;" oninput="updateBonesStyle()">
          <span id="bonesColorVal" style="font-size:11px;">#4A9EFF</span>
        </div>
      </div>
    </div>
  </div>
</div>"""

patches.append(('P1: Add boneyard style controls HTML', old_html, new_html))

# ─── P2: Make renderBoneyard use configurable gap, border thickness, and color ───
old_render_top = """  // Tile dimensions — shrunk ~15% from original 48x96
  const tileW = 40;
  const tileH = 80;
  const gap = 3;"""

new_render_top = """  // Tile dimensions — shrunk ~15% from original 48x96
  const tileW = 40;
  const tileH = 80;
  // Read adjustable style settings (or defaults)
  const gap = window._bonesGap || 3;
  const handBorderWidth = window._bonesBorder || 2;
  const handBorderColor = window._bonesColor || '#4A9EFF';"""

patches.append(('P2: Make renderBoneyard use configurable style vars', old_render_top, new_render_top))

# ─── P3: Replace hardcoded border drawing with configurable values ───
old_border = """      // Blue border for tiles in player's hand
      if(inHand){
        ctx.strokeStyle = '#4A9EFF';
        ctx.lineWidth = 2;
        ctx.strokeRect(1, 1, tileW - 2, tileH - 2);
      }"""

new_border = """      // Border for tiles in player's hand (configurable)
      if(inHand){
        ctx.strokeStyle = handBorderColor;
        ctx.lineWidth = handBorderWidth;
        const hw = handBorderWidth / 2;
        ctx.strokeRect(hw, hw, tileW - handBorderWidth, tileH - handBorderWidth);
      }"""

patches.append(('P3: Use configurable border width/color for hand tiles', old_border, new_border))

# ─── P4: Add updateBonesStyle function + localStorage persistence ───
old_bones_listener = """document.getElementById('menuBones').addEventListener('click', () => {
  document.getElementById('settingsMenu').classList.remove('open');
  renderBoneyard();
  document.getElementById('bonesBackdrop').style.display = 'block';
});"""

new_bones_listener = """// Boneyard style controls — persist with localStorage
window._bonesGap = parseInt(localStorage.getItem('tn51_bonesGap')) || 3;
window._bonesBorder = parseInt(localStorage.getItem('tn51_bonesBorder')) || 2;
window._bonesColor = localStorage.getItem('tn51_bonesColor') || '#4A9EFF';

function updateBonesStyle(){
  const gapEl = document.getElementById('bonesGap');
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
  localStorage.setItem('tn51_bonesColor', window._bonesColor);
  // Re-render
  renderBoneyard();
}

function initBonesControls(){
  const gapEl = document.getElementById('bonesGap');
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
  if(cv) cv.textContent = window._bonesColor;
}

document.getElementById('menuBones').addEventListener('click', () => {
  document.getElementById('settingsMenu').classList.remove('open');
  initBonesControls();
  renderBoneyard();
  document.getElementById('bonesBackdrop').style.display = 'block';
});"""

patches.append(('P4: Add updateBonesStyle function + localStorage + init', old_bones_listener, new_bones_listener))

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
