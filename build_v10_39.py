#!/usr/bin/env python3
"""
Build V10_39: Fix remaining Pass & Play bugs
- ppCompleteTransition missing ppUpdateValidStates/showHint
- highlightTrumpDominoes hardcoded sprites[0]
- previewSortHandByTrump hardcoded sprites[0] and seatToPlayer(0)
- restoreOriginalHandOrder hardcoded sprites[0] and seatToPlayer(0)
- showHint/clearHint hardcoded to seat 0
"""

import re, sys

SRC = "TN51_Dominoes_V10_38.html"
DST = "TN51_Dominoes_V10_39.html"

def read(f):
    with open(f, encoding="utf-8") as fh:
        return fh.read()

def write(f, s):
    with open(f, "w", encoding="utf-8") as fh:
        fh.write(s)

html = read(SRC)
original_len = len(html)
patches_ok = 0

def patch(label, old, new, count=1):
    global html, patches_ok
    n = html.count(old)
    if n < count:
        print(f"FAIL {label}: found {n} occurrences, expected >= {count}")
        print(f"  Looking for: {old[:120]}...")
        sys.exit(1)
    html = html.replace(old, new, count)
    patches_ok += 1
    print(f"  OK {label}")

# =============================================================================
# PATCH 1: ppCompleteTransition — add ppUpdateValidStates and hint
# This is the KEY fix. When transitioning to a human seat for play,
# we must mark legal tiles and show the hint.
# =============================================================================
patch("PATCH 1: ppCompleteTransition add valid states + hint",
    """function ppCompleteTransition(seat) {
  ppHideHandoff();
  ppRotateBoard(seat);

  // Enable click handlers for the active seat
  ppEnableClicksForSeat(seat);
  // Set the global flag so handlePlayer1Click allows clicks
  waitingForPlayer1 = true;
}""",
    """function ppCompleteTransition(seat) {
  ppHideHandoff();
  ppRotateBoard(seat);

  // Enable click handlers for the active seat
  ppEnableClicksForSeat(seat);
  // Set the global flag so handlePlayer1Click allows clicks
  waitingForPlayer1 = true;

  // Update valid states so tiles show legal/illegal
  if (session.phase === PHASE_PLAYING) {
    ppUpdateValidStates(seat);
    showHint();
  }
}""")

# =============================================================================
# PATCH 2: highlightTrumpDominoes — use PP active seat
# =============================================================================
patch("PATCH 2: Fix highlightTrumpDominoes for PP mode",
    """function highlightTrumpDominoes(trump){
  const seatSprites = sprites[0] || [];""",
    """function highlightTrumpDominoes(trump){
  const activeSeat = PASS_AND_PLAY_MODE ? ppActiveViewSeat : 0;
  const seatSprites = sprites[activeSeat] || [];""")

# =============================================================================
# PATCH 3: previewSortHandByTrump — use PP active seat for reading and positioning
# =============================================================================
patch("PATCH 3a: Fix previewSortHandByTrump read seat",
    """function previewSortHandByTrump(trump){
  const seatSprites = sprites[0] || [];""",
    """function previewSortHandByTrump(trump){
  const activeSeat = PASS_AND_PLAY_MODE ? ppActiveViewSeat : 0;
  const seatSprites = sprites[activeSeat] || [];""")

patch("PATCH 3b: Fix previewSortHandByTrump positioning",
    """  // Animate to new positions (preview only - don't change sprites array)
  const playerNum = seatToPlayer(0);
  for(let i = 0; i < validSprites.length; i++){
    const pos = getHandPosition(playerNum, i);
    if(pos && validSprites[i].sprite){
      animateSprite(validSprites[i].sprite, pos, 200);
    }
  }
}

// Restore hand to original order (by originalSlot)
function restoreOriginalHandOrder(){
  const seatSprites = sprites[0] || [];""",
    """  // Animate to new positions (preview only - don't change sprites array)
  const playerNum = PASS_AND_PLAY_MODE ? ppVisualPlayer(activeSeat) : seatToPlayer(activeSeat);
  for(let i = 0; i < validSprites.length; i++){
    const pos = getHandPosition(playerNum, i);
    if(pos && validSprites[i].sprite){
      animateSprite(validSprites[i].sprite, pos, 200);
    }
  }
}

// Restore hand to original order (by originalSlot)
function restoreOriginalHandOrder(){
  const activeSeat = PASS_AND_PLAY_MODE ? ppActiveViewSeat : 0;
  const seatSprites = sprites[activeSeat] || [];""")

# =============================================================================
# PATCH 4: restoreOriginalHandOrder — fix positioning
# =============================================================================
patch("PATCH 4: Fix restoreOriginalHandOrder positioning",
    """  // Animate back to original positions
  const playerNum = seatToPlayer(0);
  for(let i = 0; i < validSprites.length; i++){
    const pos = getHandPosition(playerNum, i);
    if(pos && validSprites[i].sprite){
      animateSprite(validSprites[i].sprite, pos, 200);
    }
  }
}

// Disable trump domino clicks""",
    """  // Animate back to original positions
  const playerNum = PASS_AND_PLAY_MODE ? ppVisualPlayer(activeSeat) : seatToPlayer(activeSeat);
  for(let i = 0; i < validSprites.length; i++){
    const pos = getHandPosition(playerNum, i);
    if(pos && validSprites[i].sprite){
      animateSprite(validSprites[i].sprite, pos, 200);
    }
  }
}

// Disable trump domino clicks""")

# =============================================================================
# PATCH 5: showHint — support PP mode (any human seat, not just seat 0)
# =============================================================================
patch("PATCH 5: Fix showHint for PP mode",
    """function showHint(){
  clearHint(); // clear any previous hint
  if(!HINT_MODE) return;
  if(session.phase !== PHASE_PLAYING) return;
  if(session.game.current_player !== 0) return;

  try {
    const aiRec = choose_tile_ai(session.game, 0, session.contract, true, session.current_bid);
    if(!aiRec || !aiRec.tile) return;

    const hintTile = aiRec.tile;
    const p1Sprites = sprites[0] || [];

    for(const data of p1Sprites){""",
    """function showHint(){
  clearHint(); // clear any previous hint
  if(!HINT_MODE) return;
  if(session.phase !== PHASE_PLAYING) return;

  const hintSeat = PASS_AND_PLAY_MODE ? ppActiveViewSeat : 0;
  if(session.game.current_player !== hintSeat) return;

  try {
    const aiRec = choose_tile_ai(session.game, hintSeat, session.contract, true, session.current_bid);
    if(!aiRec || !aiRec.tile) return;

    const hintTile = aiRec.tile;
    const hintSprites = sprites[hintSeat] || [];

    for(const data of hintSprites){""")

# =============================================================================
# PATCH 6: clearHint — support PP mode
# =============================================================================
patch("PATCH 6: Fix clearHint for PP mode",
    """function clearHint(){
  const p1Sprites = sprites[0] || [];
  for(const data of p1Sprites){
    if(data && data.sprite && data.sprite._shadow){
      data.sprite._shadow.classList.remove('hintGlow');
    }
  }
}""",
    """function clearHint(){
  // Clear hints on ALL seats (since active seat can change)
  for(let s = 0; s < 6; s++){
    const ss = sprites[s] || [];
    for(const data of ss){
      if(data && data.sprite && data.sprite._shadow){
        data.sprite._shadow.classList.remove('hintGlow');
      }
    }
  }
}""")

print(f"\n{'='*60}")
print(f"Build complete: {patches_ok} patches applied")
print(f"Size: {len(html):,} bytes (was {original_len:,}, delta {len(html)-original_len:+,})")
write(DST, html)
print(f"Output: {DST}")
