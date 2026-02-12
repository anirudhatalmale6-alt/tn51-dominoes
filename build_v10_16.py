#!/usr/bin/env python3
"""Build V10_16 — Fix debug log issues + add Clear Log button
Fixes:
1. "Only legal move" early returns now show full basic context (seat, hand, trick, etc.)
2. Trump-led tricks show "TRUMP" instead of "null" for led pip
3. Add "Clear Log" button that resets hand number to 1
"""

import sys, os

SRC = "/var/lib/freelancer/projects/40101953/TN51_Dominoes_V10_15.html"
DST = "/var/lib/freelancer/projects/40101953/TN51_Dominoes_V10_16.html"

with open(SRC, "r", encoding="utf-8") as f:
    html = f.read()

patches_applied = 0

# ============================================================
# PATCH 1: Move basic debug population BEFORE early returns
# ============================================================

old_dbg_init = """  // Debug info collector
  const _dbg = { enabled: returnRec };
  const _dbgCandidates = [];

  const makeResult = (idx, reason) => {
    if(!returnRec) return idx;
    return { index: idx, tile: hand[idx], reason: reason, debugInfo: _dbg.enabled ? _dbg : null };
  };

  if(legal.length === 0) return makeResult(-1, "No legal moves");
  if(legal.length === 1) return makeResult(legal[0], "Only legal move");

  const trumpSuit = gameState.trump_suit;
  const trumpMode = gameState.trump_mode;
  const isNello = contract === "NELLO";
  const maxPip = gameState.max_pip;
  const myTeam = p % 2;
  const trickNum = gameState.trick_number; // 0-indexed: how many tricks completed so far
  const totalTricks = gameState.hand_size || 6;

  // ── Led suit via game engine ──
  let ledPip = null;
  if(!isLead){
    const engineLed = gameState._led_suit_for_trick();
    if(engineLed !== null && engineLed !== -1) ledPip = engineLed;
  }"""

new_dbg_init = """  // Debug info collector
  const _dbg = { enabled: returnRec };
  const _dbgCandidates = [];

  // Populate basic debug info BEFORE early returns so "Only legal move" still shows context
  if(_dbg.enabled){
    const _earlyLed = !isLead ? gameState._led_suit_for_trick() : null;
    _dbg.seat = p;
    _dbg.myTeam = p % 2;
    _dbg.trickNum = gameState.trick_number;
    _dbg.isLead = isLead;
    _dbg.ledPip = _earlyLed === -1 ? 'TRUMP' : (_earlyLed !== null ? _earlyLed : null);
    _dbg.handTiles = hand.map(t => t[0]+'-'+t[1]);
    _dbg.legalTiles = legal.map(i => hand[i][0]+'-'+hand[i][1]);
    _dbg.playedCount = '(early)';
    _dbg.trumpMode = gameState.trump_mode;
    _dbg.trumpSuit = gameState.trump_suit;
  }

  const makeResult = (idx, reason) => {
    if(!returnRec) return idx;
    return { index: idx, tile: hand[idx], reason: reason, debugInfo: _dbg.enabled ? _dbg : null };
  };

  if(legal.length === 0) return makeResult(-1, "No legal moves");
  if(legal.length === 1) return makeResult(legal[0], "Only legal move");

  const trumpSuit = gameState.trump_suit;
  const trumpMode = gameState.trump_mode;
  const isNello = contract === "NELLO";
  const maxPip = gameState.max_pip;
  const myTeam = p % 2;
  const trickNum = gameState.trick_number; // 0-indexed: how many tricks completed so far
  const totalTricks = gameState.hand_size || 6;

  // ── Led suit via game engine ──
  let ledPip = null;
  let trumpWasLed = false;
  if(!isLead){
    const engineLed = gameState._led_suit_for_trick();
    if(engineLed === -1) trumpWasLed = true;
    else if(engineLed !== null) ledPip = engineLed;
  }"""

if old_dbg_init not in html:
    print("ERROR: Could not find debug init block")
    sys.exit(1)
html = html.replace(old_dbg_init, new_dbg_init, 1)
patches_applied += 1
print("PATCH 1: Moved basic debug before early returns + added trumpWasLed")

# ============================================================
# PATCH 2: Update the later debug snapshot to use trumpWasLed
#           and show 'TRUMP' for ledPip in debug
# ============================================================

# The existing tile memory debug snapshot sets _dbg.ledPip = ledPip
# which is null when trump is led. Update it to show 'TRUMP'.
old_mem_debug = """  // Debug: snapshot tile memory
  if(_dbg.enabled){
    _dbg.playedCount = playedSet.size;
    _dbg.handTiles = hand.map(t => t[0]+'-'+t[1]);
    _dbg.legalTiles = legal.map(i => hand[i][0]+'-'+hand[i][1]);
    _dbg.trickNum = trickNum;
    _dbg.isLead = isLead;
    _dbg.ledPip = ledPip;
    _dbg.myTeam = myTeam;
    _dbg.seat = p;
  }"""

new_mem_debug = """  // Debug: snapshot tile memory (overwrite early values with full analysis)
  if(_dbg.enabled){
    _dbg.playedCount = playedSet.size;
    _dbg.handTiles = hand.map(t => t[0]+'-'+t[1]);
    _dbg.legalTiles = legal.map(i => hand[i][0]+'-'+hand[i][1]);
    _dbg.trickNum = trickNum;
    _dbg.isLead = isLead;
    _dbg.ledPip = trumpWasLed ? 'TRUMP' : ledPip;
    _dbg.myTeam = myTeam;
    _dbg.seat = p;
  }"""

if old_mem_debug not in html:
    print("ERROR: Could not find tile memory debug block")
    sys.exit(1)
html = html.replace(old_mem_debug, new_mem_debug, 1)
patches_applied += 1
print("PATCH 2: Updated ledPip debug to show TRUMP")

# ============================================================
# PATCH 3: Fix the advanced log formatter to handle 'TRUMP' ledPip
#           and also show more info for "Only legal move" entries
# ============================================================

# The formatter already checks d.isLead for "LEADING" vs "FOLLOWING".
# When ledPip is 'TRUMP' it will show "FOLLOWING (led pip: TRUMP)" which is fine.
# But we need to handle the case where d.playedCount is '(early)' gracefully.
# This is already handled since it just prints the string.
# No change needed here — the formatter is flexible enough.

# ============================================================
# PATCH 4: Add "Clear Log" button to both log modals
# ============================================================

# Add clear button to the game log modal (after copy button)
old_gamelog_copy = """<button id="gameLogCopyBtn" style="width:100%;padding:10px;background:rgba(59,130,246,0.8);border:none;border-radius:8px;color:#fff;font-weight:600;cursor:pointer;">Copy Log to Clipboard</button>"""

new_gamelog_copy = """<div style="display:flex;gap:8px;">
        <button id="gameLogCopyBtn" style="flex:1;padding:10px;background:rgba(59,130,246,0.8);border:none;border-radius:8px;color:#fff;font-weight:600;cursor:pointer;">Copy Log to Clipboard</button>
        <button id="gameLogClearBtn" style="flex:0 0 auto;padding:10px 16px;background:rgba(239,68,68,0.8);border:none;border-radius:8px;color:#fff;font-weight:600;cursor:pointer;">Clear Log</button>
      </div>"""

c = html.count(old_gamelog_copy)
if c == 0:
    print("ERROR: Could not find game log copy button")
    sys.exit(1)
# Replace first occurrence only (game log modal)
html = html.replace(old_gamelog_copy, new_gamelog_copy, 1)
patches_applied += 1
print(f"PATCH 4a: Added Clear button to game log modal (found {c} occurrences, replaced 1st)")

# Add clear button handler after the existing game log copy handler
old_gamelog_copy_handler = """document.getElementById('gameLogCopyBtn').addEventListener('click', () => {
  const text = formatGameLog();
  navigator.clipboard.writeText(text).then(() => {
    document.getElementById('gameLogCopyBtn').textContent = 'Copied!';
    setTimeout(() => {
      document.getElementById('gameLogCopyBtn').textContent = 'Copy Log to Clipboard';
    }, 1500);
  }).catch(e => {
    console.error('Copy failed:', e);
  });
});"""

new_gamelog_copy_handler = old_gamelog_copy_handler + """

document.getElementById('gameLogClearBtn').addEventListener('click', () => {
  if(confirm('Clear all game log entries? Hand numbering will restart from 1.')){
    gameLog = [];
    handNumber = 0;
    trickNumber = 0;
    saveGameLog();
    document.getElementById('gameLogContent').textContent = 'Log cleared. Hand numbering will start from 1.';
  }
});"""

if old_gamelog_copy_handler not in html:
    print("ERROR: Could not find game log copy handler")
    sys.exit(1)
html = html.replace(old_gamelog_copy_handler, new_gamelog_copy_handler, 1)
patches_applied += 1
print("PATCH 4b: Added Clear button handler for game log")

# Now add clear button to advanced log modal too
# The advanced log has Copy and Download buttons in a flex row
old_advlog_buttons = """<div style="display:flex;gap:8px;margin-top:10px;">
        <button id="advLogCopyBtn" style="flex:1;padding:10px;background:rgba(59,130,246,0.8);border:none;border-radius:8px;color:#fff;font-weight:600;cursor:pointer;">Copy to Clipboard</button>
        <button id="advLogDownloadBtn" style="flex:1;padding:10px;background:rgba(34,197,94,0.8);border:none;border-radius:8px;color:#fff;font-weight:600;cursor:pointer;">Download .txt</button>
      </div>"""

new_advlog_buttons = """<div style="display:flex;gap:8px;margin-top:10px;">
        <button id="advLogCopyBtn" style="flex:1;padding:10px;background:rgba(59,130,246,0.8);border:none;border-radius:8px;color:#fff;font-weight:600;cursor:pointer;">Copy to Clipboard</button>
        <button id="advLogDownloadBtn" style="flex:1;padding:10px;background:rgba(34,197,94,0.8);border:none;border-radius:8px;color:#fff;font-weight:600;cursor:pointer;">Download .txt</button>
        <button id="advLogClearBtn" style="flex:0 0 auto;padding:10px 16px;background:rgba(239,68,68,0.8);border:none;border-radius:8px;color:#fff;font-weight:600;cursor:pointer;">Clear</button>
      </div>"""

if old_advlog_buttons not in html:
    print("ERROR: Could not find advanced log buttons")
    sys.exit(1)
html = html.replace(old_advlog_buttons, new_advlog_buttons, 1)
patches_applied += 1
print("PATCH 4c: Added Clear button to advanced log modal")

# Add the advanced log clear handler after the download handler
old_advlog_download = """document.getElementById('advLogDownloadBtn').addEventListener('click', () => {
  const text = formatAdvancedLog();
  const blob = new Blob([text], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'tn51_ai_debug_' + new Date().toISOString().slice(0,10) + '.txt';
  a.click();
  URL.revokeObjectURL(url);
});"""

new_advlog_download = old_advlog_download + """

document.getElementById('advLogClearBtn').addEventListener('click', () => {
  if(confirm('Clear all log entries? Hand numbering will restart from 1.')){
    gameLog = [];
    handNumber = 0;
    trickNumber = 0;
    saveGameLog();
    document.getElementById('advLogContent').textContent = 'Log cleared. Hand numbering will start from 1.';
  }
});"""

if old_advlog_download not in html:
    print("ERROR: Could not find advanced log download handler")
    sys.exit(1)
html = html.replace(old_advlog_download, new_advlog_download, 1)
patches_applied += 1
print("PATCH 4d: Added Clear button handler for advanced log")

# ============================================================
# PATCH 5: Also fix the current trick void detection for trump-led
# The code checks: if(!isLead && ledPip === null) to detect trump led
# But now ledPip stays null AND trumpWasLed is true.
# Update the trump-led detection to use trumpWasLed flag.
# ============================================================

old_trump_led_void = """  // Current trick: trump was led (engineLed === -1)
  if(!isLead && ledPip === null){
    const engineLed = gameState._led_suit_for_trick();
    if(engineLed === -1){
      // Trump was led
      for(const play of trick){
        if(!Array.isArray(play)) continue;
        const [seat, t] = play;
        if(seat === p) continue;
        if(!gameState._is_trump_tile(t)){
          trumpVoidConfirmed[seat] = true;
        }
      }
    }
  }"""

new_trump_led_void = """  // Current trick: trump was led
  if(!isLead && trumpWasLed){
    for(const play of trick){
      if(!Array.isArray(play)) continue;
      const [seat, t] = play;
      if(seat === p) continue;
      if(!gameState._is_trump_tile(t)){
        trumpVoidConfirmed[seat] = true;
      }
    }
  }"""

if old_trump_led_void not in html:
    print("ERROR: Could not find trump-led void detection block")
    sys.exit(1)
html = html.replace(old_trump_led_void, new_trump_led_void, 1)
patches_applied += 1
print("PATCH 5: Simplified trump-led void detection with trumpWasLed flag")

# ============================================================
# Verification
# ============================================================
checks = [
    ("_earlyLed", "Early debug population"),
    ("trumpWasLed", "Trump-was-led flag"),
    ("gameLogClearBtn", "Game log clear button"),
    ("advLogClearBtn", "Advanced log clear button"),
    ("handNumber = 0", "Hand number reset"),
    ("formatAdvancedLog", "Advanced log formatter"),
    ("_dbg.enabled", "Debug collector"),
]

all_ok = True
for pattern, desc in checks:
    if pattern not in html:
        print(f"  ✗ Missing: {desc} ({pattern})")
        all_ok = False
    else:
        print(f"  ✓ {desc}")

if not all_ok:
    print("ERROR: Verification failed!")
    sys.exit(1)

with open(DST, "w", encoding="utf-8") as f:
    f.write(html)

src_size = os.path.getsize(SRC)
dst_size = os.path.getsize(DST)
print(f"\nPatches applied: {patches_applied}")
print(f"Source: {src_size:,} bytes")
print(f"Output: {dst_size:,} bytes")
print(f"Delta:  {dst_size - src_size:+,} bytes")
print(f"Written to: {DST}")
print("SUCCESS!")
