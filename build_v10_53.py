#!/usr/bin/env python3
"""
Build script: TN51_TX42_Dominoes_V10_53
Base: TN51_Dominoes_V10_52.html (same file, client renamed on their end)
Fixes: 2x multiplier scoring bug, boneyard rendering bug
Features: Full X/Y coordinate sliders, separate Boneyard Settings menu
"""

import sys

INPUT_FILE = "TN51_Dominoes_V10_52.html"
OUTPUT_FILE = "TN51_TX42_Dominoes_V10_53.html"

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def patch(src, old, new, label, count=1):
    occurrences = src.count(old)
    if occurrences == 0:
        print(f"  FAIL: '{label}' — target string not found!")
        sys.exit(1)
    if occurrences != count:
        print(f"  WARN: '{label}' — expected {count} occurrences, found {occurrences}")
    result = src.replace(old, new, count) if count == 1 else src.replace(old, new)
    print(f"  OK: {label} ({occurrences} replaced)")
    return result

def main():
    print(f"Reading {INPUT_FILE}...")
    html = read_file(INPUT_FILE)
    original_len = len(html)

    # =========================================================================
    # BUG FIX 1: 2x multiplier humanBid — actualBid = 51 → dynamic
    # =========================================================================
    print("\n=== FIX 1: 2x multiplier humanBid ===")

    html = patch(html,
        "// For 2x, 3x etc: bid stays at 51, but marks are multiplied\n      actualBid = 51;  // The bid amount is still 51 points",
        "// For 2x, 3x etc: bid stays at max points, but marks are multiplied\n      actualBid = GAME_MODE === 'T42' ? 42 : 51;  // Max points for game mode",
        "humanBid 2x multiplier fix")

    # =========================================================================
    # BUG FIX 2: AI multiplier calculation — /51 → dynamic
    # =========================================================================
    print("\n=== FIX 2: AI multiplier calculation ===")

    html = patch(html,
        "biddingState.highMultiplier = Math.floor(evaluation.bid / 51);",
        "biddingState.highMultiplier = Math.floor(evaluation.bid / (GAME_MODE === 'T42' ? 42 : 51));",
        "AI multiplier calculation fix")

    # =========================================================================
    # BUG FIX 3: Boneyard2 _by2MaxPip hoisting bug
    # Move declaration before first usage
    # =========================================================================
    print("\n=== FIX 3: Boneyard2 _by2MaxPip hoisting bug ===")

    # Add _by2MaxPip declaration before the lines that use it
    html = patch(html,
        "  // Now we know: boneyard rows 0-5 align with trick history rows 0-5\n  // Rows 6-7 extend below with same rowSpacing\n  const maxCols = _by2MaxPip + 1;\n  const numRows = _by2MaxPip + 1;",
        "  // Now we know: boneyard rows 0-5 align with trick history rows 0-5\n  // Rows 6-7 extend below with same rowSpacing\n  const _by2MaxPip = session.game.max_pip;\n  const maxCols = _by2MaxPip + 1;\n  const numRows = _by2MaxPip + 1;",
        "Boneyard2 _by2MaxPip declaration moved up")

    # Remove the old declaration that's now a duplicate
    html = patch(html,
        "  // Build the grid: dynamic based on game mode (double-7 for TN51, double-6 for T42)\n  const _by2MaxPip = session.game.max_pip;\n  const rows = [];",
        "  // Build the grid: dynamic based on game mode (double-7 for TN51, double-6 for T42)\n  const rows = [];",
        "Remove duplicate _by2MaxPip declaration")

    # =========================================================================
    # FEATURE 1: Extended T42 Layout Settings with full X/Y for all players
    # Replace the T42_SETTINGS object and applyT42Settings function
    # =========================================================================
    print("\n=== FEATURE 1: Extended T42 Layout Settings ===")

    old_settings = """let T42_SETTINGS = {
  p1Scale: 1.071,        // Player 1 (bottom) tile scale
  p1Spacing: 0.13487,    // Player 1 tile spacing
  opponentScale: 0.393,  // P2/P3/P4 tile scale
  p2x: 0.165,            // Player 2 (left) X position
  p4x: 0.835,            // Player 4 (right) X position
  p3y: 0.411,            // Player 3 (top) Y position
  sideSpacing: 0.0456,   // P2/P4 vertical spacing between tiles
  p3Spacing: 0.0556,     // P3 horizontal spacing between tiles
  trickScale: 0.393,     // Trick area (played domino) scale
  p2TrickX: 0.380,       // P2 played domino X
  p4TrickX: 0.610,       // P4 played domino X
  p1TrickY: 0.678,       // P1 played domino Y
  p3TrickY: 0.522,       // P3 played domino Y
  leadScale: 0.393,      // Lead pip scale
};"""

    new_settings = """let T42_SETTINGS = {
  // Player 1 (bottom - you)
  p1Scale: 1.071,        // P1 tile scale
  p1Spacing: 0.13487,    // P1 tile spacing (horizontal)
  p1x: 0.9,              // P1 starting X (rightmost tile)
  p1y: 0.88,             // P1 Y position
  // Player 2 (left opponent)
  p2Scale: 0.393,        // P2 tile scale
  p2x: 0.165,            // P2 X position
  p2y: 0.600,            // P2 center Y position
  p2Spacing: 0.0456,     // P2 vertical spacing between tiles
  // Player 3 (top partner)
  p3Scale: 0.393,        // P3 tile scale
  p3x: 0.3282,           // P3 starting X (leftmost tile)
  p3y: 0.411,            // P3 Y position
  p3Spacing: 0.0556,     // P3 horizontal spacing between tiles
  // Player 4 (right opponent)
  p4Scale: 0.393,        // P4 tile scale
  p4x: 0.835,            // P4 X position
  p4y: 0.600,            // P4 center Y position
  p4Spacing: 0.0456,     // P4 vertical spacing (linked with P2 by default)
  // Trick area (center played dominoes)
  trickScale: 0.393,     // Trick area domino scale
  p1TrickX: 0.495,       // P1 played domino X
  p1TrickY: 0.678,       // P1 played domino Y
  p2TrickX: 0.380,       // P2 played domino X
  p2TrickY: 0.600,       // P2 played domino Y
  p3TrickX: 0.495,       // P3 played domino X
  p3TrickY: 0.522,       // P3 played domino Y
  p4TrickX: 0.610,       // P4 played domino X
  p4TrickY: 0.600,       // P4 played domino Y
  leadScale: 0.393,      // Lead pip scale
  leadX: 0.495,          // Lead pip X position
  leadY: 0.600,          // Lead pip Y position
};"""
    html = patch(html, old_settings, new_settings, "Extended T42_SETTINGS object")

    # =========================================================================
    # FEATURE 2: Extended applyT42Settings function
    # =========================================================================
    print("\n=== FEATURE 2: Extended applyT42Settings ===")

    old_apply = """function applyT42Settings(){
  if(GAME_MODE !== 'T42') return;
  const s = T42_SETTINGS;
  const L = LAYOUT_T42.sections;
  // P1 Hand
  const p1h = L.find(x => x.name === 'Player_1_Hand');
  if(p1h){
    for(let i = 0; i < 7; i++){
      p1h.dominoes[i].xN = 0.9 - i * s.p1Spacing;
      p1h.dominoes[i].scale = s.p1Scale;
    }
  }
  // P2 Hand (left, vertical)
  const p2h = L.find(x => x.name === 'Player_2_Hand');
  if(p2h){
    const cy = 0.600;
    for(let i = 0; i < 7; i++){
      p2h.dominoes[i].xN = s.p2x;
      p2h.dominoes[i].yN = (cy - 3*s.sideSpacing) + i*s.sideSpacing;
      p2h.dominoes[i].scale = s.opponentScale;
    }
  }
  // P3 Hand (top, horizontal)
  const p3h = L.find(x => x.name === 'Player_3_Hand');
  if(p3h){
    for(let i = 0; i < 7; i++){
      p3h.dominoes[i].xN = 0.3282 + i * s.p3Spacing;
      p3h.dominoes[i].yN = s.p3y;
      p3h.dominoes[i].scale = s.opponentScale;
    }
  }
  // P4 Hand (right, vertical)
  const p4h = L.find(x => x.name === 'Player_4_Hand');
  if(p4h){
    const cy = 0.600;
    for(let i = 0; i < 7; i++){
      p4h.dominoes[i].xN = s.p4x;
      p4h.dominoes[i].yN = (cy - 3*s.sideSpacing) + i*s.sideSpacing;
      p4h.dominoes[i].scale = s.opponentScale;
    }
  }
  // Played domino placeholders
  const p1pd = L.find(x => x.name === 'Player_1_Played_Domino');
  if(p1pd){ p1pd.dominoes[0].yN = s.p1TrickY; p1pd.dominoes[0].scale = s.trickScale; }
  const p2pd = L.find(x => x.name === 'Player_2_Played_Domino');
  if(p2pd){ p2pd.dominoes[0].xN = s.p2TrickX; p2pd.dominoes[0].scale = s.trickScale; }
  const p3pd = L.find(x => x.name === 'Player_3_Played_Domino');
  if(p3pd){ p3pd.dominoes[0].yN = s.p3TrickY; p3pd.dominoes[0].scale = s.trickScale; }
  const p4pd = L.find(x => x.name === 'Player_4_Played_Domino');
  if(p4pd){ p4pd.dominoes[0].xN = s.p4TrickX; p4pd.dominoes[0].scale = s.trickScale; }
  // Lead domino
  const ld = L.find(x => x.name === 'Lead_Domino');
  if(ld){ ld.dominoes[0].scale = s.leadScale; }
  // Update placeholder config
  PLACEHOLDER_CONFIG_T42.players[1].yN = s.p1TrickY;
  PLACEHOLDER_CONFIG_T42.players[2].xN = s.p2TrickX;
  PLACEHOLDER_CONFIG_T42.players[3].yN = s.p3TrickY;
  PLACEHOLDER_CONFIG_T42.players[4].xN = s.p4TrickX;
  // Refresh
  refreshLayout();
}"""

    new_apply = """function applyT42Settings(){
  if(GAME_MODE !== 'T42') return;
  const s = T42_SETTINGS;
  const L = LAYOUT_T42.sections;
  // P1 Hand (bottom, horizontal)
  const p1h = L.find(x => x.name === 'Player_1_Hand');
  if(p1h){
    for(let i = 0; i < 7; i++){
      p1h.dominoes[i].xN = s.p1x - i * s.p1Spacing;
      p1h.dominoes[i].yN = s.p1y;
      p1h.dominoes[i].scale = s.p1Scale;
    }
  }
  // P2 Hand (left, vertical)
  const p2h = L.find(x => x.name === 'Player_2_Hand');
  if(p2h){
    for(let i = 0; i < 7; i++){
      p2h.dominoes[i].xN = s.p2x;
      p2h.dominoes[i].yN = (s.p2y - 3*s.p2Spacing) + i*s.p2Spacing;
      p2h.dominoes[i].scale = s.p2Scale;
    }
  }
  // P3 Hand (top, horizontal)
  const p3h = L.find(x => x.name === 'Player_3_Hand');
  if(p3h){
    for(let i = 0; i < 7; i++){
      p3h.dominoes[i].xN = s.p3x + i * s.p3Spacing;
      p3h.dominoes[i].yN = s.p3y;
      p3h.dominoes[i].scale = s.p3Scale;
    }
  }
  // P4 Hand (right, vertical)
  const p4h = L.find(x => x.name === 'Player_4_Hand');
  if(p4h){
    for(let i = 0; i < 7; i++){
      p4h.dominoes[i].xN = s.p4x;
      p4h.dominoes[i].yN = (s.p4y - 3*s.p4Spacing) + i*s.p4Spacing;
      p4h.dominoes[i].scale = s.p4Scale;
    }
  }
  // Played domino placeholders — full X/Y control
  const p1pd = L.find(x => x.name === 'Player_1_Played_Domino');
  if(p1pd){ p1pd.dominoes[0].xN = s.p1TrickX; p1pd.dominoes[0].yN = s.p1TrickY; p1pd.dominoes[0].scale = s.trickScale; }
  const p2pd = L.find(x => x.name === 'Player_2_Played_Domino');
  if(p2pd){ p2pd.dominoes[0].xN = s.p2TrickX; p2pd.dominoes[0].yN = s.p2TrickY; p2pd.dominoes[0].scale = s.trickScale; }
  const p3pd = L.find(x => x.name === 'Player_3_Played_Domino');
  if(p3pd){ p3pd.dominoes[0].xN = s.p3TrickX; p3pd.dominoes[0].yN = s.p3TrickY; p3pd.dominoes[0].scale = s.trickScale; }
  const p4pd = L.find(x => x.name === 'Player_4_Played_Domino');
  if(p4pd){ p4pd.dominoes[0].xN = s.p4TrickX; p4pd.dominoes[0].yN = s.p4TrickY; p4pd.dominoes[0].scale = s.trickScale; }
  // Lead domino — full position + scale
  const ld = L.find(x => x.name === 'Lead_Domino');
  if(ld){ ld.dominoes[0].xN = s.leadX; ld.dominoes[0].yN = s.leadY; ld.dominoes[0].scale = s.leadScale; }
  // Update placeholder config
  PLACEHOLDER_CONFIG_T42.players[1].xN = s.p1TrickX;
  PLACEHOLDER_CONFIG_T42.players[1].yN = s.p1TrickY;
  PLACEHOLDER_CONFIG_T42.players[2].xN = s.p2TrickX;
  PLACEHOLDER_CONFIG_T42.players[2].yN = s.p2TrickY;
  PLACEHOLDER_CONFIG_T42.players[3].xN = s.p3TrickX;
  PLACEHOLDER_CONFIG_T42.players[3].yN = s.p3TrickY;
  PLACEHOLDER_CONFIG_T42.players[4].xN = s.p4TrickX;
  PLACEHOLDER_CONFIG_T42.players[4].yN = s.p4TrickY;
  PLACEHOLDER_CONFIG_T42.lead.xN = s.leadX;
  PLACEHOLDER_CONFIG_T42.lead.yN = s.leadY;
  // Refresh
  refreshLayout();
}"""
    html = patch(html, old_apply, new_apply, "Extended applyT42Settings function")

    # =========================================================================
    # FEATURE 3: Replace T42 Layout Settings popup HTML with full controls
    # =========================================================================
    print("\n=== FEATURE 3: Replace T42 Layout Settings popup ===")

    old_popup = """<div id="t42SettingsBackdrop" class="modalBackdrop" style="display:none;z-index:2000;">
  <div class="modal" style="width:340px;max-height:80vh;overflow-y:auto;">
    <div class="modalHeader" style="padding:12px 16px;">
      <span style="font-weight:700;font-size:15px;">T42 Layout Settings</span>
      <button class="closeBtn" id="btnCloseT42Settings">&times;</button>
    </div>
    <div class="modalBody" style="padding:12px 16px;">
      <div class="t42s-group">
        <label>P1 (You) Tile Scale</label>
        <input type="range" min="0.5" max="1.5" step="0.01" id="t42s_p1Scale">
        <span id="t42sv_p1Scale"></span>
      </div>
      <div class="t42s-group">
        <label>P1 Tile Spacing</label>
        <input type="range" min="0.05" max="0.20" step="0.001" id="t42s_p1Spacing">
        <span id="t42sv_p1Spacing"></span>
      </div>
      <div class="t42s-group">
        <label>Opponent Tile Scale</label>
        <input type="range" min="0.2" max="0.8" step="0.01" id="t42s_opponentScale">
        <span id="t42sv_opponentScale"></span>
      </div>
      <div class="t42s-group">
        <label>P2 X Position (Left)</label>
        <input type="range" min="0.05" max="0.35" step="0.005" id="t42s_p2x">
        <span id="t42sv_p2x"></span>
      </div>
      <div class="t42s-group">
        <label>P4 X Position (Right)</label>
        <input type="range" min="0.65" max="0.95" step="0.005" id="t42s_p4x">
        <span id="t42sv_p4x"></span>
      </div>
      <div class="t42s-group">
        <label>P3 Y Position (Top)</label>
        <input type="range" min="0.30" max="0.50" step="0.005" id="t42s_p3y">
        <span id="t42sv_p3y"></span>
      </div>
      <div class="t42s-group">
        <label>Side Tile Spacing (P2/P4)</label>
        <input type="range" min="0.02" max="0.08" step="0.001" id="t42s_sideSpacing">
        <span id="t42sv_sideSpacing"></span>
      </div>
      <div class="t42s-group">
        <label>P3 Tile Spacing</label>
        <input type="range" min="0.03" max="0.10" step="0.001" id="t42s_p3Spacing">
        <span id="t42sv_p3Spacing"></span>
      </div>
      <div class="t42s-group">
        <label>Trick Area Scale</label>
        <input type="range" min="0.2" max="0.8" step="0.01" id="t42s_trickScale">
        <span id="t42sv_trickScale"></span>
      </div>
      <div class="t42s-group">
        <label>P2 Trick X</label>
        <input type="range" min="0.25" max="0.48" step="0.005" id="t42s_p2TrickX">
        <span id="t42sv_p2TrickX"></span>
      </div>
      <div class="t42s-group">
        <label>P4 Trick X</label>
        <input type="range" min="0.52" max="0.75" step="0.005" id="t42s_p4TrickX">
        <span id="t42sv_p4TrickX"></span>
      </div>
      <div class="t42s-group">
        <label>P1 Trick Y</label>
        <input type="range" min="0.60" max="0.80" step="0.005" id="t42s_p1TrickY">
        <span id="t42sv_p1TrickY"></span>
      </div>
      <div class="t42s-group">
        <label>P3 Trick Y</label>
        <input type="range" min="0.45" max="0.60" step="0.005" id="t42s_p3TrickY">
        <span id="t42sv_p3TrickY"></span>
      </div>
      <div style="text-align:center;margin-top:12px;">
        <button class="glossBtn" id="btnT42Reset" style="padding:6px 14px;font-size:12px;">Reset Defaults</button>
        <button class="glossBtn" id="btnT42Export" style="padding:6px 14px;font-size:12px;margin-left:8px;">Export Values</button>
      </div>
    </div>
  </div>
</div>
<style>
.t42s-group { margin-bottom:8px; }
.t42s-group label { display:block;font-size:11px;color:rgba(255,255,255,0.8);margin-bottom:2px; }
.t42s-group input[type=range] { width:220px;vertical-align:middle; }
.t42s-group span { font-size:11px;color:#fff;margin-left:6px; }
#t42SettingsBtn { position:fixed; bottom:10px; left:10px; z-index:900; background:rgba(0,0,0,0.6); color:#fff; border:1px solid rgba(255,255,255,0.3); border-radius:6px; padding:4px 10px; font-size:11px; cursor:pointer; display:none; }
#t42SettingsBtn:hover { background:rgba(0,0,0,0.8); }
</style>
<button id="t42SettingsBtn">T42 Layout</button>"""

    new_popup = """<div id="t42SettingsBackdrop" class="modalBackdrop" style="display:none;z-index:2000;">
  <div class="modal" style="width:360px;max-height:85vh;overflow-y:auto;">
    <div class="modalHeader" style="padding:12px 16px;">
      <span style="font-weight:700;font-size:15px;">T42 Layout Settings</span>
      <button class="closeBtn" id="btnCloseT42Settings">&times;</button>
    </div>
    <div class="modalBody" style="padding:12px 16px;">
      <div class="t42s-section">Player 1 (You - Bottom)</div>
      <div class="t42s-group"><label>Scale</label><input type="range" min="0.5" max="1.5" step="0.01" id="t42s_p1Scale"><span id="t42sv_p1Scale"></span></div>
      <div class="t42s-group"><label>X (Start)</label><input type="range" min="0.70" max="0.98" step="0.005" id="t42s_p1x"><span id="t42sv_p1x"></span></div>
      <div class="t42s-group"><label>Y</label><input type="range" min="0.75" max="0.98" step="0.005" id="t42s_p1y"><span id="t42sv_p1y"></span></div>
      <div class="t42s-group"><label>Spacing</label><input type="range" min="0.05" max="0.20" step="0.001" id="t42s_p1Spacing"><span id="t42sv_p1Spacing"></span></div>

      <div class="t42s-section">Player 2 (Left Opponent)</div>
      <div class="t42s-group"><label>Scale</label><input type="range" min="0.2" max="0.8" step="0.01" id="t42s_p2Scale"><span id="t42sv_p2Scale"></span></div>
      <div class="t42s-group"><label>X</label><input type="range" min="0.03" max="0.35" step="0.005" id="t42s_p2x"><span id="t42sv_p2x"></span></div>
      <div class="t42s-group"><label>Y (Center)</label><input type="range" min="0.40" max="0.80" step="0.005" id="t42s_p2y"><span id="t42sv_p2y"></span></div>
      <div class="t42s-group"><label>Spacing</label><input type="range" min="0.02" max="0.08" step="0.001" id="t42s_p2Spacing"><span id="t42sv_p2Spacing"></span></div>

      <div class="t42s-section">Player 3 (Top Partner)</div>
      <div class="t42s-group"><label>Scale</label><input type="range" min="0.2" max="0.8" step="0.01" id="t42s_p3Scale"><span id="t42sv_p3Scale"></span></div>
      <div class="t42s-group"><label>X (Start)</label><input type="range" min="0.15" max="0.50" step="0.005" id="t42s_p3x"><span id="t42sv_p3x"></span></div>
      <div class="t42s-group"><label>Y</label><input type="range" min="0.30" max="0.55" step="0.005" id="t42s_p3y"><span id="t42sv_p3y"></span></div>
      <div class="t42s-group"><label>Spacing</label><input type="range" min="0.03" max="0.10" step="0.001" id="t42s_p3Spacing"><span id="t42sv_p3Spacing"></span></div>

      <div class="t42s-section">Player 4 (Right Opponent)</div>
      <div class="t42s-group"><label>Scale</label><input type="range" min="0.2" max="0.8" step="0.01" id="t42s_p4Scale"><span id="t42sv_p4Scale"></span></div>
      <div class="t42s-group"><label>X</label><input type="range" min="0.65" max="0.97" step="0.005" id="t42s_p4x"><span id="t42sv_p4x"></span></div>
      <div class="t42s-group"><label>Y (Center)</label><input type="range" min="0.40" max="0.80" step="0.005" id="t42s_p4y"><span id="t42sv_p4y"></span></div>
      <div class="t42s-group"><label>Spacing</label><input type="range" min="0.02" max="0.08" step="0.001" id="t42s_p4Spacing"><span id="t42sv_p4Spacing"></span></div>

      <div class="t42s-section">Trick Area (Center)</div>
      <div class="t42s-group"><label>Trick Scale</label><input type="range" min="0.2" max="0.8" step="0.01" id="t42s_trickScale"><span id="t42sv_trickScale"></span></div>
      <div class="t42s-group"><label>P1 Trick X</label><input type="range" min="0.35" max="0.65" step="0.005" id="t42s_p1TrickX"><span id="t42sv_p1TrickX"></span></div>
      <div class="t42s-group"><label>P1 Trick Y</label><input type="range" min="0.55" max="0.80" step="0.005" id="t42s_p1TrickY"><span id="t42sv_p1TrickY"></span></div>
      <div class="t42s-group"><label>P2 Trick X</label><input type="range" min="0.25" max="0.50" step="0.005" id="t42s_p2TrickX"><span id="t42sv_p2TrickX"></span></div>
      <div class="t42s-group"><label>P2 Trick Y</label><input type="range" min="0.45" max="0.75" step="0.005" id="t42s_p2TrickY"><span id="t42sv_p2TrickY"></span></div>
      <div class="t42s-group"><label>P3 Trick X</label><input type="range" min="0.35" max="0.65" step="0.005" id="t42s_p3TrickX"><span id="t42sv_p3TrickX"></span></div>
      <div class="t42s-group"><label>P3 Trick Y</label><input type="range" min="0.40" max="0.65" step="0.005" id="t42s_p3TrickY"><span id="t42sv_p3TrickY"></span></div>
      <div class="t42s-group"><label>P4 Trick X</label><input type="range" min="0.50" max="0.75" step="0.005" id="t42s_p4TrickX"><span id="t42sv_p4TrickX"></span></div>
      <div class="t42s-group"><label>P4 Trick Y</label><input type="range" min="0.45" max="0.75" step="0.005" id="t42s_p4TrickY"><span id="t42sv_p4TrickY"></span></div>
      <div class="t42s-group"><label>Lead Scale</label><input type="range" min="0.2" max="0.8" step="0.01" id="t42s_leadScale"><span id="t42sv_leadScale"></span></div>
      <div class="t42s-group"><label>Lead X</label><input type="range" min="0.35" max="0.65" step="0.005" id="t42s_leadX"><span id="t42sv_leadX"></span></div>
      <div class="t42s-group"><label>Lead Y</label><input type="range" min="0.45" max="0.70" step="0.005" id="t42s_leadY"><span id="t42sv_leadY"></span></div>
      <div style="text-align:center;margin-top:12px;">
        <button class="glossBtn" id="btnT42Reset" style="padding:6px 14px;font-size:12px;">Reset Defaults</button>
        <button class="glossBtn" id="btnT42Export" style="padding:6px 14px;font-size:12px;margin-left:8px;">Export Values</button>
      </div>
    </div>
  </div>
</div>
<!-- Boneyard Settings Popup -->
<div id="by2SettingsBackdrop" class="modalBackdrop" style="display:none;z-index:2100;">
  <div class="modal" style="width:340px;max-height:80vh;overflow-y:auto;">
    <div class="modalHeader" style="padding:12px 16px;">
      <span style="font-weight:700;font-size:15px;">Boneyard Settings</span>
      <button class="closeBtn" id="btnCloseBy2Settings">&times;</button>
    </div>
    <div class="modalBody" style="padding:12px 16px;">
      <div class="t42s-section">Tile Appearance</div>
      <div class="t42s-group"><label>Tile Gap</label><input type="range" min="0" max="8" step="1" id="by2s_gap"><span id="by2sv_gap"></span></div>
      <div class="t42s-group"><label>Played Tile Opacity</label><input type="range" min="0.1" max="1.0" step="0.01" id="by2s_playedOpacity"><span id="by2sv_playedOpacity"></span></div>
      <div class="t42s-section">Hand Tile Border</div>
      <div class="t42s-group"><label>Inner Border Size</label><input type="range" min="0" max="5" step="0.5" id="by2s_innerSize"><span id="by2sv_innerSize"></span></div>
      <div class="t42s-group"><label>Inner Border Radius</label><input type="range" min="0" max="15" step="1" id="by2s_innerRadius"><span id="by2sv_innerRadius"></span></div>
      <div class="t42s-group"><label>Inner Border Color</label><input type="color" id="by2s_innerColor" style="width:60px;height:24px;vertical-align:middle;"><span id="by2sv_innerColor" style="margin-left:6px;font-size:11px;color:#fff;"></span></div>
      <div class="t42s-group"><label>Outer Border Size</label><input type="range" min="0" max="5" step="0.5" id="by2s_outerSize"><span id="by2sv_outerSize"></span></div>
      <div class="t42s-group"><label>Outer Border Radius</label><input type="range" min="0" max="15" step="1" id="by2s_outerRadius"><span id="by2sv_outerRadius"></span></div>
      <div class="t42s-group"><label>Outer Border Color</label><input type="color" id="by2s_outerColor" style="width:60px;height:24px;vertical-align:middle;"><span id="by2sv_outerColor" style="margin-left:6px;font-size:11px;color:#fff;"></span></div>
      <div style="text-align:center;margin-top:12px;">
        <button class="glossBtn" id="btnBy2Reset" style="padding:6px 14px;font-size:12px;">Reset Defaults</button>
        <button class="glossBtn" id="btnBy2Export" style="padding:6px 14px;font-size:12px;margin-left:8px;">Export Values</button>
      </div>
    </div>
  </div>
</div>
<style>
.t42s-group { margin-bottom:8px; }
.t42s-group label { display:block;font-size:11px;color:rgba(255,255,255,0.8);margin-bottom:2px; }
.t42s-group input[type=range] { width:220px;vertical-align:middle; }
.t42s-group span { font-size:11px;color:#fff;margin-left:6px; }
.t42s-section { font-size:12px;font-weight:700;color:#4ecdc4;margin:12px 0 6px 0;padding-bottom:4px;border-bottom:1px solid rgba(255,255,255,0.15); }
.t42s-section:first-child { margin-top:0; }
#t42SettingsBtn { position:fixed; bottom:10px; left:10px; z-index:900; background:rgba(0,0,0,0.6); color:#fff; border:1px solid rgba(255,255,255,0.3); border-radius:6px; padding:4px 10px; font-size:11px; cursor:pointer; display:none; }
#t42SettingsBtn:hover { background:rgba(0,0,0,0.8); }
#by2SettingsBtn { position:fixed; bottom:10px; left:100px; z-index:900; background:rgba(0,0,0,0.6); color:#fff; border:1px solid rgba(255,255,255,0.3); border-radius:6px; padding:4px 10px; font-size:11px; cursor:pointer; display:none; }
#by2SettingsBtn:hover { background:rgba(0,0,0,0.8); }
</style>
<button id="t42SettingsBtn">T42 Layout</button>
<button id="by2SettingsBtn">Boneyard</button>"""
    html = patch(html, old_popup, new_popup, "Replace T42 settings popup + add Boneyard settings")

    # =========================================================================
    # FEATURE 4: Replace T42 settings JS handler
    # =========================================================================
    print("\n=== FEATURE 4: Replace T42 settings + Boneyard settings JS ===")

    old_js = """<script>
(function(){
  const DEFAULTS = {
    p1Scale: 1.071, p1Spacing: 0.13487, opponentScale: 0.393,
    p2x: 0.165, p4x: 0.835, p3y: 0.411,
    sideSpacing: 0.0456, p3Spacing: 0.0556, trickScale: 0.393,
    p2TrickX: 0.380, p4TrickX: 0.610, p1TrickY: 0.678, p3TrickY: 0.522,
    leadScale: 0.393
  };
  const KEYS = Object.keys(DEFAULTS);

  function showT42Settings(){
    document.getElementById('t42SettingsBackdrop').style.display = 'flex';
    KEYS.forEach(k => {
      const slider = document.getElementById('t42s_' + k);
      const label = document.getElementById('t42sv_' + k);
      if(slider){
        slider.value = T42_SETTINGS[k];
        if(label) label.textContent = T42_SETTINGS[k].toFixed(3);
      }
    });
  }
  function hideT42Settings(){
    document.getElementById('t42SettingsBackdrop').style.display = 'none';
  }

  // Toggle button visibility
  const origInitGameMode = window.initGameMode;
  const _t42Btn = document.getElementById('t42SettingsBtn');
  if(origInitGameMode){
    window.initGameMode = function(mode){
      origInitGameMode(mode);
      if(_t42Btn) _t42Btn.style.display = mode === 'T42' ? 'block' : 'none';
    };
  }

  // Button click
  if(_t42Btn) _t42Btn.addEventListener('click', showT42Settings);

  // Close button
  document.getElementById('btnCloseT42Settings').addEventListener('click', hideT42Settings);

  // Backdrop click
  document.getElementById('t42SettingsBackdrop').addEventListener('click', function(e){
    if(e.target === this) hideT42Settings();
  });

  // Slider changes — live update
  KEYS.forEach(k => {
    const slider = document.getElementById('t42s_' + k);
    const label = document.getElementById('t42sv_' + k);
    if(slider){
      slider.addEventListener('input', function(){
        const val = parseFloat(this.value);
        T42_SETTINGS[k] = val;
        if(label) label.textContent = val.toFixed(3);
        applyT42Settings();
      });
    }
  });

  // Reset defaults
  document.getElementById('btnT42Reset').addEventListener('click', function(){
    Object.assign(T42_SETTINGS, DEFAULTS);
    KEYS.forEach(k => {
      const slider = document.getElementById('t42s_' + k);
      const label = document.getElementById('t42sv_' + k);
      if(slider){ slider.value = DEFAULTS[k]; }
      if(label){ label.textContent = DEFAULTS[k].toFixed(3); }
    });
    applyT42Settings();
  });

  // Export values
  document.getElementById('btnT42Export').addEventListener('click', function(){
    const vals = {};
    KEYS.forEach(k => { vals[k] = T42_SETTINGS[k]; });
    const str = JSON.stringify(vals, null, 2);
    prompt('Copy these T42 layout values:', str);
  });
})();
</script>"""

    new_js = """<script>
(function(){
  // ==================== T42 LAYOUT SETTINGS ====================
  const T42_DEFAULTS = {
    p1Scale:1.071, p1Spacing:0.13487, p1x:0.9, p1y:0.88,
    p2Scale:0.393, p2x:0.165, p2y:0.600, p2Spacing:0.0456,
    p3Scale:0.393, p3x:0.3282, p3y:0.411, p3Spacing:0.0556,
    p4Scale:0.393, p4x:0.835, p4y:0.600, p4Spacing:0.0456,
    trickScale:0.393,
    p1TrickX:0.495, p1TrickY:0.678,
    p2TrickX:0.380, p2TrickY:0.600,
    p3TrickX:0.495, p3TrickY:0.522,
    p4TrickX:0.610, p4TrickY:0.600,
    leadScale:0.393, leadX:0.495, leadY:0.600
  };
  const T42_KEYS = Object.keys(T42_DEFAULTS);

  function showT42Settings(){
    document.getElementById('t42SettingsBackdrop').style.display = 'flex';
    T42_KEYS.forEach(k => {
      const slider = document.getElementById('t42s_' + k);
      const label = document.getElementById('t42sv_' + k);
      if(slider){
        slider.value = T42_SETTINGS[k];
        if(label) label.textContent = T42_SETTINGS[k].toFixed(3);
      }
    });
  }
  function hideT42Settings(){
    document.getElementById('t42SettingsBackdrop').style.display = 'none';
  }

  // Toggle button visibility for both T42 and Boneyard settings
  const origInitGameMode = window.initGameMode;
  const _t42Btn = document.getElementById('t42SettingsBtn');
  const _by2Btn = document.getElementById('by2SettingsBtn');
  if(origInitGameMode){
    window.initGameMode = function(mode){
      origInitGameMode(mode);
      if(_t42Btn) _t42Btn.style.display = mode === 'T42' ? 'block' : 'none';
      if(_by2Btn) _by2Btn.style.display = mode === 'T42' ? 'block' : 'none';
    };
  }

  if(_t42Btn) _t42Btn.addEventListener('click', showT42Settings);
  document.getElementById('btnCloseT42Settings').addEventListener('click', hideT42Settings);
  document.getElementById('t42SettingsBackdrop').addEventListener('click', function(e){
    if(e.target === this) hideT42Settings();
  });

  T42_KEYS.forEach(k => {
    const slider = document.getElementById('t42s_' + k);
    const label = document.getElementById('t42sv_' + k);
    if(slider){
      slider.addEventListener('input', function(){
        const val = parseFloat(this.value);
        T42_SETTINGS[k] = val;
        if(label) label.textContent = val.toFixed(3);
        applyT42Settings();
      });
    }
  });

  document.getElementById('btnT42Reset').addEventListener('click', function(){
    Object.assign(T42_SETTINGS, T42_DEFAULTS);
    T42_KEYS.forEach(k => {
      const slider = document.getElementById('t42s_' + k);
      const label = document.getElementById('t42sv_' + k);
      if(slider){ slider.value = T42_DEFAULTS[k]; }
      if(label){ label.textContent = T42_DEFAULTS[k].toFixed(3); }
    });
    applyT42Settings();
  });

  document.getElementById('btnT42Export').addEventListener('click', function(){
    const vals = {};
    T42_KEYS.forEach(k => { vals[k] = T42_SETTINGS[k]; });
    prompt('Copy these T42 layout values:', JSON.stringify(vals, null, 2));
  });

  // ==================== BONEYARD SETTINGS ====================
  const BY2_DEFAULTS = {
    gap: 0, playedOpacity: 0.71,
    innerSize: 1, innerRadius: 5, innerColor: '#beb6ab',
    outerSize: 2, outerRadius: 8, outerColor: '#00deff'
  };
  const BY2_KEYS = Object.keys(BY2_DEFAULTS);

  function showBy2Settings(){
    document.getElementById('by2SettingsBackdrop').style.display = 'flex';
    const vals = {
      gap: BY2_GAP, playedOpacity: BY2_PLAYED_OPACITY,
      innerSize: BY2_INNER_SIZE, innerRadius: BY2_INNER_RADIUS, innerColor: BY2_INNER_COLOR,
      outerSize: BY2_OUTER_SIZE, outerRadius: BY2_OUTER_RADIUS, outerColor: BY2_OUTER_COLOR
    };
    BY2_KEYS.forEach(k => {
      const el = document.getElementById('by2s_' + k);
      const label = document.getElementById('by2sv_' + k);
      if(el){
        el.value = vals[k];
        if(label){
          label.textContent = (typeof vals[k] === 'number') ? vals[k].toFixed(k.includes('Opacity') ? 2 : 1) : vals[k];
        }
      }
    });
  }
  function hideBy2Settings(){
    document.getElementById('by2SettingsBackdrop').style.display = 'none';
  }

  if(_by2Btn) _by2Btn.addEventListener('click', showBy2Settings);
  document.getElementById('btnCloseBy2Settings').addEventListener('click', hideBy2Settings);
  document.getElementById('by2SettingsBackdrop').addEventListener('click', function(e){
    if(e.target === this) hideBy2Settings();
  });

  // Map setting keys to global variable names
  const BY2_VARMAP = {
    gap: 'BY2_GAP', playedOpacity: 'BY2_PLAYED_OPACITY',
    innerSize: 'BY2_INNER_SIZE', innerRadius: 'BY2_INNER_RADIUS', innerColor: 'BY2_INNER_COLOR',
    outerSize: 'BY2_OUTER_SIZE', outerRadius: 'BY2_OUTER_RADIUS', outerColor: 'BY2_OUTER_COLOR'
  };

  BY2_KEYS.forEach(k => {
    const el = document.getElementById('by2s_' + k);
    const label = document.getElementById('by2sv_' + k);
    if(el){
      el.addEventListener('input', function(){
        let val;
        if(k === 'innerColor' || k === 'outerColor'){
          val = this.value;
        } else {
          val = parseFloat(this.value);
        }
        window[BY2_VARMAP[k]] = val;
        if(label){
          label.textContent = (typeof val === 'number') ? val.toFixed(k.includes('Opacity') ? 2 : 1) : val;
        }
        if(boneyard2Visible) renderBoneyard2();
      });
    }
  });

  document.getElementById('btnBy2Reset').addEventListener('click', function(){
    window.BY2_GAP = BY2_DEFAULTS.gap;
    window.BY2_PLAYED_OPACITY = BY2_DEFAULTS.playedOpacity;
    window.BY2_INNER_SIZE = BY2_DEFAULTS.innerSize;
    window.BY2_INNER_RADIUS = BY2_DEFAULTS.innerRadius;
    window.BY2_INNER_COLOR = BY2_DEFAULTS.innerColor;
    window.BY2_OUTER_SIZE = BY2_DEFAULTS.outerSize;
    window.BY2_OUTER_RADIUS = BY2_DEFAULTS.outerRadius;
    window.BY2_OUTER_COLOR = BY2_DEFAULTS.outerColor;
    showBy2Settings();  // Re-sync sliders
    if(boneyard2Visible) renderBoneyard2();
  });

  document.getElementById('btnBy2Export').addEventListener('click', function(){
    const vals = {
      BY2_GAP: BY2_GAP, BY2_PLAYED_OPACITY: BY2_PLAYED_OPACITY,
      BY2_INNER_SIZE: BY2_INNER_SIZE, BY2_INNER_RADIUS: BY2_INNER_RADIUS, BY2_INNER_COLOR: BY2_INNER_COLOR,
      BY2_OUTER_SIZE: BY2_OUTER_SIZE, BY2_OUTER_RADIUS: BY2_OUTER_RADIUS, BY2_OUTER_COLOR: BY2_OUTER_COLOR
    };
    prompt('Copy these Boneyard values:', JSON.stringify(vals, null, 2));
  });
})();
</script>"""
    html = patch(html, old_js, new_js, "Replace settings JS handler")

    # =========================================================================
    # FEATURE 5: Make BY2 variables writable (const → let)
    # =========================================================================
    print("\n=== FEATURE 5: Make BY2 variables writable ===")

    # Find the BY2 variable declarations and make them let instead of const
    html = patch(html,
        "const BY2_GAP = 0;",
        "let BY2_GAP = 0;",
        "BY2_GAP const→let")

    html = patch(html,
        "const BY2_INNER_SIZE = 1;",
        "let BY2_INNER_SIZE = 1;",
        "BY2_INNER_SIZE const→let")

    html = patch(html,
        "const BY2_INNER_RADIUS = 5;",
        "let BY2_INNER_RADIUS = 5;",
        "BY2_INNER_RADIUS const→let")

    html = patch(html,
        "const BY2_OUTER_SIZE = 2;",
        "let BY2_OUTER_SIZE = 2;",
        "BY2_OUTER_SIZE const→let")

    html = patch(html,
        "const BY2_OUTER_RADIUS = 8;",
        "let BY2_OUTER_RADIUS = 8;",
        "BY2_OUTER_RADIUS const→let")

    html = patch(html,
        "const BY2_INNER_COLOR = '#beb6ab';",
        "let BY2_INNER_COLOR = '#beb6ab';",
        "BY2_INNER_COLOR const→let")

    html = patch(html,
        "const BY2_OUTER_COLOR = '#00deff';",
        "let BY2_OUTER_COLOR = '#00deff';",
        "BY2_OUTER_COLOR const→let")

    html = patch(html,
        "const BY2_PLAYED_OPACITY = 0.71;",
        "let BY2_PLAYED_OPACITY = 0.71;",
        "BY2_PLAYED_OPACITY const→let")

    # =========================================================================
    # FEATURE 6: Version update
    # =========================================================================
    print("\n=== FEATURE 6: Version update ===")

    html = patch(html,
        "<title>TN51 / T42 Domino Game V10_52</title>",
        "<title>TN51 / T42 Domino Game V10_53</title>",
        "Version title update")

    # =========================================================================
    # DONE
    # =========================================================================
    print(f"\nAll patches applied successfully!")
    print(f"Original size: {original_len:,} bytes")
    print(f"New size: {len(html):,} bytes")
    print(f"Delta: +{len(html) - original_len:,} bytes")

    write_file(OUTPUT_FILE, html)
    print(f"Written to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
