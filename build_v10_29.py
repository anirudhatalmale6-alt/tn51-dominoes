#!/usr/bin/env python3
"""
V10_29 Build Script — Hardcode client's final boneyard settings, move icon bottom-left, 10% opacity
"""

INPUT  = '/var/lib/freelancer/projects/40101953/TN51_Dominoes_V10_28.html'
OUTPUT = '/var/lib/freelancer/projects/40101953/TN51_Dominoes_V10_29.html'

with open(INPUT, 'r', encoding='utf-8') as f:
    src = f.read()

patches = []

# ─── P1: Move gear icon to bottom-left, 10% opacity ───
old_btn = """<button id="bonesSettingsBtn" onclick="document.getElementById('bonesControls').style.display=document.getElementById('bonesControls').style.display==='none'?'block':'none';" style="position:absolute;bottom:8px;right:8px;background:none;border:none;color:rgba(255,255,255,0.5);font-size:20px;cursor:pointer;padding:4px;">&#9881;</button>"""

new_btn = """<button id="bonesSettingsBtn" onclick="document.getElementById('bonesControls').style.display=document.getElementById('bonesControls').style.display==='none'?'block':'none';" style="position:absolute;bottom:8px;left:8px;background:none;border:none;color:rgba(255,255,255,0.1);font-size:20px;cursor:pointer;padding:4px;">&#9881;</button>"""

patches.append(('P1: Move gear to bottom-left, 10% opacity', old_btn, new_btn))

# ─── P2: Update HTML slider defaults ───
# Spacing 8 -> 7
old_spacing = """<input type="range" id="bonesGap" min="1" max="12" value="8" style="flex:1;" oninput="updateBonesStyle()">
          <span id="bonesGapVal" style="min-width:20px;text-align:right;">8</span>"""
new_spacing = """<input type="range" id="bonesGap" min="1" max="12" value="7" style="flex:1;" oninput="updateBonesStyle()">
          <span id="bonesGapVal" style="min-width:20px;text-align:right;">7</span>"""
patches.append(('P2a: Spacing default 7', old_spacing, new_spacing))

# Inner Size stays 1 — no change needed

# Inner Radius 0 -> 8
old_ir = """<input type="range" id="bonesInnerRadius" min="0" max="16" value="0" style="flex:1;" oninput="updateBonesStyle()">
          <span id="bonesInnerRadiusVal" style="min-width:20px;text-align:right;">0</span>"""
new_ir = """<input type="range" id="bonesInnerRadius" min="0" max="16" value="8" style="flex:1;" oninput="updateBonesStyle()">
          <span id="bonesInnerRadiusVal" style="min-width:20px;text-align:right;">8</span>"""
patches.append(('P2b: Inner Radius default 8', old_ir, new_ir))

# Outer Size stays 3 — no change needed

# Outer Radius 0 -> 11
old_or = """<input type="range" id="bonesOuterRadius" min="0" max="16" value="0" style="flex:1;" oninput="updateBonesStyle()">
          <span id="bonesOuterRadiusVal" style="min-width:20px;text-align:right;">0</span>"""
new_or = """<input type="range" id="bonesOuterRadius" min="0" max="16" value="11" style="flex:1;" oninput="updateBonesStyle()">
          <span id="bonesOuterRadiusVal" style="min-width:20px;text-align:right;">11</span>"""
patches.append(('P2c: Outer Radius default 11', old_or, new_or))

# Inner Color #000000 -> #beb6ab
old_ic = """<input type="color" id="bonesColor" value="#000000" style="width:40px;height:28px;border:none;background:none;cursor:pointer;" oninput="updateBonesStyle()">
          <span id="bonesColorVal" style="font-size:11px;">#000000</span>"""
new_ic = """<input type="color" id="bonesColor" value="#beb6ab" style="width:40px;height:28px;border:none;background:none;cursor:pointer;" oninput="updateBonesStyle()">
          <span id="bonesColorVal" style="font-size:11px;">#beb6ab</span>"""
patches.append(('P2d: Inner Color default #beb6ab', old_ic, new_ic))

# Outer Color #00c4ff -> #00deff
old_oc = """<input type="color" id="bonesOuterColor" value="#00c4ff" style="width:40px;height:28px;border:none;background:none;cursor:pointer;" oninput="updateBonesStyle()">
          <span id="bonesOuterColorVal" style="font-size:11px;">#00c4ff</span>"""
new_oc = """<input type="color" id="bonesOuterColor" value="#00deff" style="width:40px;height:28px;border:none;background:none;cursor:pointer;" oninput="updateBonesStyle()">
          <span id="bonesOuterColorVal" style="font-size:11px;">#00deff</span>"""
patches.append(('P2e: Outer Color default #00deff', old_oc, new_oc))

# ─── P3: Update JS global state defaults ───
old_state = """window._bonesGap = parseInt(localStorage.getItem('tn51_bonesGap')) || 8;
window._bonesInnerSize = parseInt(localStorage.getItem('tn51_bonesInnerSize')) || 1;
window._bonesInnerRadius = parseInt(localStorage.getItem('tn51_bonesInnerRadius') || '0');
window._bonesOuterSize = parseInt(localStorage.getItem('tn51_bonesOuterSize')) || 3;
window._bonesOuterRadius = parseInt(localStorage.getItem('tn51_bonesOuterRadius') || '0');
window._bonesColor = localStorage.getItem('tn51_bonesColor') || '#000000';
window._bonesOuterColor = localStorage.getItem('tn51_bonesOuterColor') || '#00c4ff';"""

new_state = """window._bonesGap = parseInt(localStorage.getItem('tn51_bonesGap')) || 7;
window._bonesInnerSize = parseInt(localStorage.getItem('tn51_bonesInnerSize')) || 1;
window._bonesInnerRadius = parseInt(localStorage.getItem('tn51_bonesInnerRadius') || '8');
window._bonesOuterSize = parseInt(localStorage.getItem('tn51_bonesOuterSize')) || 3;
window._bonesOuterRadius = parseInt(localStorage.getItem('tn51_bonesOuterRadius') || '11');
window._bonesColor = localStorage.getItem('tn51_bonesColor') || '#beb6ab';
window._bonesOuterColor = localStorage.getItem('tn51_bonesOuterColor') || '#00deff';"""

patches.append(('P3: Update JS global state defaults', old_state, new_state))

# ─── P4: Update renderBoneyard fallback defaults ───
old_render = """  const handInnerSize = window._bonesInnerSize != null ? window._bonesInnerSize : 1;
  const handInnerRadius = window._bonesInnerRadius != null ? window._bonesInnerRadius : 0;
  const handOuterSize = window._bonesOuterSize != null ? window._bonesOuterSize : 3;
  const handOuterRadius = window._bonesOuterRadius != null ? window._bonesOuterRadius : 0;
  const handInnerColor = window._bonesColor || '#000000';
  const handOuterColor = window._bonesOuterColor || '#00c4ff';"""

new_render = """  const handInnerSize = window._bonesInnerSize != null ? window._bonesInnerSize : 1;
  const handInnerRadius = window._bonesInnerRadius != null ? window._bonesInnerRadius : 8;
  const handOuterSize = window._bonesOuterSize != null ? window._bonesOuterSize : 3;
  const handOuterRadius = window._bonesOuterRadius != null ? window._bonesOuterRadius : 11;
  const handInnerColor = window._bonesColor || '#beb6ab';
  const handOuterColor = window._bonesOuterColor || '#00deff';"""

patches.append(('P4: Update renderBoneyard fallback defaults', old_render, new_render))

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
