#!/usr/bin/env python3
"""Build V10_46 from V10_45:
1. Hardcode boneyard 2 settings (remove settings gear + panel + updateBY2Style)
2. Replace SVG bone icon with vertical "BONES" text + arrow on the RIGHT side
3. Boneyard expands from right to left on click
"""
import re, sys

INPUT = 'TN51_Dominoes_V10_45.html'
OUTPUT = 'TN51_Dominoes_V10_46.html'

with open(INPUT, 'r', encoding='utf-8') as f:
    html = f.read()

patches_applied = 0

# ============================================================
# PATCH 1: Replace CSS — move toggle to right side, vertical text, remove settings CSS
# ============================================================
old_css = """  #boneyard2Container{
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
    width: 20px;
    height: 20px;
    z-index: 7;
    cursor: pointer;
    opacity: 0.5;
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
  .by2Row span{ min-width:18px; text-align:right; font-size:10px; }"""

new_css = """  #boneyard2Container{
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
    right: 0.5%;
    top: 16%;
    width: 18px;
    z-index: 7;
    cursor: pointer;
    opacity: 0.4;
    transition: opacity 0.2s;
    pointer-events: auto;
    user-select: none;
    -webkit-user-select: none;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
    padding: 3px 2px;
  }
  #boneyard2Toggle:hover{ opacity: 0.9; }
  #boneyard2Toggle.active{ opacity: 0.9; }
  #boneyard2Toggle .by2Label{
    writing-mode: vertical-rl;
    text-orientation: mixed;
    color: rgba(255,255,255,0.85);
    font-size: 9px;
    font-weight: bold;
    letter-spacing: 1px;
    text-transform: uppercase;
  }
  #boneyard2Toggle .by2Arrow{
    color: rgba(255,255,255,0.7);
    font-size: 10px;
    line-height: 1;
    transition: transform 0.3s;
  }
  #boneyard2Toggle.active .by2Arrow{
    transform: scaleX(-1);
  }"""

if old_css in html:
    html = html.replace(old_css, new_css, 1)
    patches_applied += 1
    print("PATCH 1 applied: CSS — toggle on right, vertical text, removed settings CSS")
else:
    print("ERROR: Could not find CSS block")
    sys.exit(1)

# ============================================================
# PATCH 2: Replace HTML — remove settings panel, new toggle icon
# ============================================================
old_html = """  <!-- Boneyard 2 — inline overlay -->
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
      <div class="by2Row"><label>Played Opacity</label><input type="range" id="by2HandOpacity" min="0" max="100" value="70" oninput="updateBY2Style()"><span id="by2HandOpacityVal">70%</span></div>
    </div>
  </div>
  <!-- Boneyard 2 toggle icon -->
  <div id="boneyard2Toggle"><svg viewBox="0 0 24 24" width="20" height="20" fill="rgba(255,255,255,0.9)" xmlns="http://www.w3.org/2000/svg"><path d="M19.5 7a2.5 2.5 0 0 0-1.77.73l-.13.14-3.17-3.17.14-.13a2.5 2.5 0 1 0-3.54-3.54 2.5 2.5 0 0 0 0 3.54l.13.14-7.42 7.42-.14-.13a2.5 2.5 0 0 0-3.54 0 2.5 2.5 0 0 0 0 3.54 2.5 2.5 0 0 0 3.54 0l.13-.14 3.17 3.17-.14.13a2.5 2.5 0 0 0 0 3.54 2.5 2.5 0 0 0 3.54 0 2.5 2.5 0 0 0 0-3.54l-.13-.14 7.42-7.42.14.13A2.5 2.5 0 1 0 22 7.5 2.5 2.5 0 0 0 19.5 7z"/></svg></div>"""

new_html = """  <!-- Boneyard 2 — inline overlay -->
  <div id="boneyard2Container">
    <canvas id="boneyard2Canvas"></canvas>
  </div>
  <!-- Boneyard 2 toggle — vertical BONES text + arrow on right side -->
  <div id="boneyard2Toggle"><span class="by2Arrow">&#9664;</span><span class="by2Label">BONES</span></div>"""

if old_html in html:
    html = html.replace(old_html, new_html, 1)
    patches_applied += 1
    print("PATCH 2 applied: HTML — removed settings, new BONES toggle on right")
else:
    print("ERROR: Could not find HTML block")
    sys.exit(1)

# ============================================================
# PATCH 3: Hardcode settings and remove updateBY2Style function
# ============================================================
old_js_settings = """// Style state (separate from full boneyard modal)
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
}"""

new_js_settings = """// Boneyard 2 — hardcoded settings
const BY2_GAP = 0;
const BY2_INNER_SIZE = 1;
const BY2_INNER_RADIUS = 5;
const BY2_OUTER_SIZE = 6;
const BY2_OUTER_RADIUS = 8;
const BY2_INNER_COLOR = '#beb6ab';
const BY2_OUTER_COLOR = '#00deff';
const BY2_PLAYED_OPACITY = 0.71;
let boneyard2Visible = false;"""

if old_js_settings in html:
    html = html.replace(old_js_settings, new_js_settings, 1)
    patches_applied += 1
    print("PATCH 3 applied: Hardcoded settings, removed updateBY2Style")
else:
    print("ERROR: Could not find JS settings block")
    sys.exit(1)

# ============================================================
# PATCH 4: Remove by2Controls reference from toggleBoneyard2 close path
# ============================================================
old_toggle_close = """    container.style.display = 'none';
    // Close settings panel too
    document.getElementById('by2Controls').style.display = 'none';
    // Restore trick history"""

new_toggle_close = """    container.style.display = 'none';
    // Restore trick history"""

if old_toggle_close in html:
    html = html.replace(old_toggle_close, new_toggle_close, 1)
    patches_applied += 1
    print("PATCH 4 applied: Removed by2Controls reference from toggle")
else:
    print("ERROR: Could not find toggle close block")
    sys.exit(1)

# Also remove from startNewHand
old_newhand_by2 = """    if(by2c) by2c.style.display = 'none';
    if(thBg) thBg.style.display = '';
    if(toggleBtn) toggleBtn.classList.remove('active');
    document.getElementById('by2Controls').style.display = 'none';"""

new_newhand_by2 = """    if(by2c) by2c.style.display = 'none';
    if(thBg) thBg.style.display = '';
    if(toggleBtn) toggleBtn.classList.remove('active');"""

if old_newhand_by2 in html:
    html = html.replace(old_newhand_by2, new_newhand_by2, 1)
    patches_applied += 1
    print("PATCH 4b applied: Removed by2Controls from startNewHand")
else:
    print("WARNING: Could not find newhand by2Controls reference")

# ============================================================
# PATCH 5: Update renderBoneyard2 to use hardcoded constants
# ============================================================
old_render_controls = """  // Read controls
  const gap = window._by2Gap;
  const handInnerSize = window._by2InnerSize;
  const handInnerRadius = window._by2InnerRadius;
  const handOuterSize = window._by2OuterSize;
  const handOuterRadius = window._by2OuterRadius;
  const handInnerColor = window._by2InnerColor;
  const handOuterColor = window._by2OuterColor;
  const handOpacity = window._by2HandOpacity / 100;"""

new_render_controls = """  // Hardcoded settings
  const gap = BY2_GAP;
  const handInnerSize = BY2_INNER_SIZE;
  const handInnerRadius = BY2_INNER_RADIUS;
  const handOuterSize = BY2_OUTER_SIZE;
  const handOuterRadius = BY2_OUTER_RADIUS;
  const handInnerColor = BY2_INNER_COLOR;
  const handOuterColor = BY2_OUTER_COLOR;
  const handOpacity = BY2_PLAYED_OPACITY;"""

if old_render_controls in html:
    html = html.replace(old_render_controls, new_render_controls, 1)
    patches_applied += 1
    print("PATCH 5 applied: renderBoneyard2 uses hardcoded constants")
else:
    print("ERROR: Could not find render controls block")
    sys.exit(1)

# ============================================================
# Update version string
# ============================================================
html = html.replace('TN51 Dominoes V10_45', 'TN51 Dominoes V10_46')
html = html.replace("'V10_45'", "'V10_46'")
html = html.replace('"V10_45"', '"V10_46"')
print("Version updated: V10_45 -> V10_46")

# Write output
with open(OUTPUT, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\nTotal patches applied: {patches_applied}")
print(f"Output: {OUTPUT} ({len(html):,} bytes)")
