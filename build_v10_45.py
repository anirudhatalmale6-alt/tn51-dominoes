#!/usr/bin/env python3
"""Build V10_45 from V10_44:
1. Fix opacity slider — should affect played/boneyard tiles, not hand tiles
2. Fix bone icon (🧀 cheese → use text "BY" or SVG bone)
3. Fix sprite hiding — tag trick history sprites instead of position-based detection
4. Fix shadows remaining when boneyard 2 opens
"""
import re, sys

INPUT = 'TN51_Dominoes_V10_44.html'
OUTPUT = 'TN51_Dominoes_V10_45.html'

with open(INPUT, 'r', encoding='utf-8') as f:
    html = f.read()

patches_applied = 0

# ============================================================
# PATCH 1: Tag sprites when moved to trick history
# In collectToHistory(), mark sprites with _inTrickHistory flag
# ============================================================
old_collect = """    bringToFront(sprite);

    // Convert seat to player row (0-5, based on player number order P1-P6)"""

new_collect = """    bringToFront(sprite);

    // Tag this sprite as being in trick history (for boneyard 2 toggling)
    sprite._inTrickHistory = true;
    if(sprite._shadow) sprite._shadow._inTrickHistory = true;

    // Convert seat to player row (0-5, based on player number order P1-P6)"""

if old_collect in html:
    html = html.replace(old_collect, new_collect, 1)
    patches_applied += 1
    print("PATCH 1 applied: Tag trick history sprites")
else:
    print("ERROR: Could not find collectToHistory sprite anchor")
    sys.exit(1)

# ============================================================
# PATCH 2: Fix hideTrickHistorySprites — use _inTrickHistory flag
# Also hide shadows from #shadowLayer
# ============================================================
old_hide = """function hideTrickHistorySprites(){
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
}"""

new_hide = """function hideTrickHistorySprites(){
  // Hide sprites tagged as trick history (moved there by collectToHistory)
  const spriteEls = document.querySelectorAll('#spriteLayer .dominoSprite');
  spriteEls.forEach(el => {
    if(el._inTrickHistory){
      el._by2Hidden = true;
      el.style.display = 'none';
    }
  });
  // Also hide their shadows
  const shadowEls = document.querySelectorAll('#shadowLayer .dominoShadow');
  shadowEls.forEach(el => {
    if(el._inTrickHistory){
      el._by2Hidden = true;
      el.style.display = 'none';
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
  const shadowEls = document.querySelectorAll('#shadowLayer .dominoShadow');
  shadowEls.forEach(el => {
    if(el._by2Hidden){
      el._by2Hidden = false;
      el.style.display = '';
    }
  });
}"""

if old_hide in html:
    html = html.replace(old_hide, new_hide, 1)
    patches_applied += 1
    print("PATCH 2 applied: Fix sprite hiding with tag-based detection + shadow hiding")
else:
    print("ERROR: Could not find hideTrickHistorySprites")
    sys.exit(1)

# ============================================================
# PATCH 3: Fix opacity slider — apply to played tiles, not hand tiles
# In renderBoneyard2, swap: hand tiles get full opacity + border,
# played tiles get adjustable opacity
# ============================================================
old_opacity_logic = """      // Set opacity for in-hand tiles (ghost effect)
      if(inHand){
        ctx.globalAlpha = handOpacity;
      }"""

new_opacity_logic = """      // Set opacity: played tiles get ghost effect (adjustable), hand tiles full opacity
      if(played){
        ctx.globalAlpha = handOpacity;  // "handOpacity" slider now controls played tile opacity
      }"""

if old_opacity_logic in html:
    html = html.replace(old_opacity_logic, new_opacity_logic, 1)
    patches_applied += 1
    print("PATCH 3 applied: Opacity now applies to played tiles")
else:
    print("ERROR: Could not find opacity logic in renderBoneyard2")
    sys.exit(1)

# Also rename the slider label from "Hand Opacity" to "Played Opacity" in HTML
old_opacity_label = """<label>Hand Opacity</label><input type="range" id="by2HandOpacity" min="30" max="100" value="70" oninput="updateBY2Style()"><span id="by2HandOpacityVal">70%</span>"""
new_opacity_label = """<label>Played Opacity</label><input type="range" id="by2HandOpacity" min="0" max="100" value="70" oninput="updateBY2Style()"><span id="by2HandOpacityVal">70%</span>"""

if old_opacity_label in html:
    html = html.replace(old_opacity_label, new_opacity_label, 1)
    patches_applied += 1
    print("PATCH 3b applied: Renamed opacity slider label")
else:
    print("WARNING: Could not find opacity label HTML")

# ============================================================
# PATCH 4: Fix bone icon — replace cheese emoji with text bone icon
# The Unicode bone emoji doesn't render properly everywhere.
# Use a simple SVG bone or text alternative.
# ============================================================
old_bone_icon_css = """  #boneyard2Toggle{
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
  #boneyard2Toggle.active{ opacity: 1; }"""

new_bone_icon_css = """  #boneyard2Toggle{
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
  #boneyard2Toggle.active{ opacity: 1; }"""

if old_bone_icon_css in html:
    html = html.replace(old_bone_icon_css, new_bone_icon_css, 1)
    patches_applied += 1
    print("PATCH 4a applied: Updated bone icon CSS")
else:
    print("ERROR: Could not find bone icon CSS")
    sys.exit(1)

# Replace the HTML bone icon element with an inline SVG bone
old_bone_html = """<div id="boneyard2Toggle">&#129472;</div>"""
new_bone_html = """<div id="boneyard2Toggle"><svg viewBox="0 0 24 24" width="20" height="20" fill="rgba(255,255,255,0.9)" xmlns="http://www.w3.org/2000/svg"><path d="M19.5 7a2.5 2.5 0 0 0-1.77.73l-.13.14-3.17-3.17.14-.13a2.5 2.5 0 1 0-3.54-3.54 2.5 2.5 0 0 0 0 3.54l.13.14-7.42 7.42-.14-.13a2.5 2.5 0 0 0-3.54 0 2.5 2.5 0 0 0 0 3.54 2.5 2.5 0 0 0 3.54 0l.13-.14 3.17 3.17-.14.13a2.5 2.5 0 0 0 0 3.54 2.5 2.5 0 0 0 3.54 0 2.5 2.5 0 0 0 0-3.54l-.13-.14 7.42-7.42.14.13A2.5 2.5 0 1 0 22 7.5 2.5 2.5 0 0 0 19.5 7z"/></svg></div>"""

if old_bone_html in html:
    html = html.replace(old_bone_html, new_bone_html, 1)
    patches_applied += 1
    print("PATCH 4b applied: Replaced emoji with SVG bone icon")
else:
    print("ERROR: Could not find bone icon HTML")
    sys.exit(1)

# ============================================================
# Update version string
# ============================================================
html = html.replace('TN51 Dominoes V10_44', 'TN51 Dominoes V10_45')
html = html.replace("'V10_44'", "'V10_45'")
html = html.replace('"V10_44"', '"V10_45"')
print("Version updated: V10_44 -> V10_45")

# Write output
with open(OUTPUT, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\nTotal patches applied: {patches_applied}")
print(f"Output: {OUTPUT} ({len(html):,} bytes)")
