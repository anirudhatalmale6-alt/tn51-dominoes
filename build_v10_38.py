#!/usr/bin/env python3
"""
Build V10_38: Fix Pass & Play bugs
- Bug 1: Splash screen stays visible when PP starts new game
- Bug 2: sortPlayerHandByTrump hardcodes sprites[0] and seatToPlayer(0)
- Bug 3: Trump highlights showing on face-down opponent tiles
- Bug 4: Only P1 can play - waitingForPlayer1 never set for other seats
"""

import re, sys

SRC = "TN51_Dominoes_V10_37.html"
DST = "TN51_Dominoes_V10_38.html"

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
# PATCH 1: Hide splash screen when PP mode starts a new game
# =============================================================================
patch("PATCH 1: Hide splash when PP starts new game",
    """  if (startNew) {
    ppResetRotation();
    startNewHand();
  } else {""",
    """  if (startNew) {
    ppResetRotation();
    hideStartScreen();
    startNewHand();
  } else {""")

# =============================================================================
# PATCH 2: Fix sortPlayerHandByTrump - use sortSeat for positioning and sprites
# The sort correctly reads from sprites[sortSeat] but writes back to sprites[0]
# and positions using seatToPlayer(0). Fix to use sortSeat throughout.
# =============================================================================
patch("PATCH 2: Fix sortPlayerHandByTrump positioning",
    """  // Reassign to sprites array and animate to new positions
  const playerNum = seatToPlayer(0);
  for(let i = 0; i < validSprites.length; i++){
    sprites[0][i] = validSprites[i];
    const pos = getHandPosition(playerNum, i);
    if(pos && validSprites[i].sprite){
      animateSprite(validSprites[i].sprite, pos, 300);
    }
  }

  // Clear remaining slots
  for(let i = validSprites.length; i < 7; i++){
    sprites[0][i] = null;
  }
}""",
    """  // Reassign to sprites array and animate to new positions
  const playerNum = PASS_AND_PLAY_MODE ? ppVisualPlayer(sortSeat) : seatToPlayer(sortSeat);
  for(let i = 0; i < validSprites.length; i++){
    sprites[sortSeat][i] = validSprites[i];
    const pos = getHandPosition(playerNum, i);
    if(pos && validSprites[i].sprite){
      animateSprite(validSprites[i].sprite, pos, 300);
    }
  }

  // Clear remaining slots
  for(let i = validSprites.length; i < 7; i++){
    sprites[sortSeat][i] = null;
  }
}""")

# =============================================================================
# PATCH 3: Fix ppCompleteTransition - set waitingForPlayer1 = true
# This is THE critical fix for Bug 4. When transitioning to any human seat,
# we must set the global waitingForPlayer1 flag so handlePlayer1Click works.
# =============================================================================
patch("PATCH 3: Set waitingForPlayer1 in ppCompleteTransition",
    """function ppCompleteTransition(seat) {
  ppHideHandoff();
  ppRotateBoard(seat);

  // Enable click handlers for the active seat
  ppEnableClicksForSeat(seat);
}""",
    """function ppCompleteTransition(seat) {
  ppHideHandoff();
  ppRotateBoard(seat);

  // Enable click handlers for the active seat
  ppEnableClicksForSeat(seat);
  // Set the global flag so handlePlayer1Click allows clicks
  waitingForPlayer1 = true;
}""")

# =============================================================================
# PATCH 4: Fix renderAll - handle PP mode in player hand clickability
# renderAll hardcodes current_player === 0 for enabling clicks.
# In PP mode, should check if current player is a human seat.
# =============================================================================
patch("PATCH 4: Fix renderAll PP clickability",
    """  // Update player hand clickability
  if(phase === PHASE_PLAYING && session.game.current_player === 0){
    waitingForPlayer1 = true;
    enablePlayer1Clicks();
    updatePlayer1ValidStates();
    showHint();
  } else {
    waitingForPlayer1 = false;
    disablePlayer1Clicks();
  }""",
    """  // Update player hand clickability
  if(PASS_AND_PLAY_MODE && phase === PHASE_PLAYING) {
    const cp = session.game.current_player;
    if(ppIsHuman(cp) && cp === ppActiveViewSeat) {
      waitingForPlayer1 = true;
      ppEnableClicksForSeat(cp);
      ppUpdateValidStates(cp);
    } else {
      waitingForPlayer1 = false;
    }
  } else if(phase === PHASE_PLAYING && session.game.current_player === 0){
    waitingForPlayer1 = true;
    enablePlayer1Clicks();
    updatePlayer1ValidStates();
    showHint();
  } else {
    waitingForPlayer1 = false;
    disablePlayer1Clicks();
  }""")

# =============================================================================
# PATCH 5: Fix handoff button - set waitingForPlayer1 for play phase
# After handoff is clicked and transition completes, enable play
# =============================================================================
patch("PATCH 5: Set waitingForPlayer1 in handoff handler",
    """  // Resume the appropriate game flow
  if (session.phase === PHASE_NEED_BID) {
    showBidOverlay(true);
  } else if (session.phase === PHASE_NEED_TRUMP) {
    // Trump selection - enable domino clicks
    ppUpdateValidStates(activeSeat);
  } else if (session.phase === PHASE_PLAYING) {
    ppUpdateValidStates(activeSeat);
  }""",
    """  // Resume the appropriate game flow
  if (session.phase === PHASE_NEED_BID) {
    showBidOverlay(true);
  } else if (session.phase === PHASE_NEED_TRUMP) {
    // Trump selection - enable domino clicks
    ppUpdateValidStates(activeSeat);
  } else if (session.phase === PHASE_PLAYING) {
    waitingForPlayer1 = true;
    ppUpdateValidStates(activeSeat);
  }""")

# =============================================================================
# PATCH 6: Fix trump highlights on face-down tiles
# syncSpritesWithGameState calls updatePlayer1ValidStates which highlights
# trumps on seat 0 even when that seat is face-down. In PP mode, only
# highlight the active viewing seat, and clear highlights on all others.
# =============================================================================
patch("PATCH 6: Fix syncSpritesWithGameState for PP mode",
    """  // Update valid states for player 1
  updatePlayer1ValidStates();
}""",
    """  // Update valid states
  if (PASS_AND_PLAY_MODE) {
    // In PP mode: only highlight the active viewing seat's tiles
    // Clear highlights on all other seats to prevent face-down trump highlighting
    for (let s = 0; s < 6; s++) {
      if (s === ppActiveViewSeat) continue;
      const ss = sprites[s] || [];
      ss.forEach(d => { if (d && d.sprite) d.sprite.setState(false, true); });
    }
    ppUpdateValidStates(ppActiveViewSeat);
  } else {
    updatePlayer1ValidStates();
  }
}""")

# =============================================================================
# PATCH 7: Fix confirmTrumpSelection PP mode - also call sortPlayerHandByTrump
# After trump is confirmed in PP mode, the hand should be sorted for the active seat
# =============================================================================
# (sortPlayerHandByTrump is already called before the PP check, so this is handled)

print(f"\n{'='*60}")
print(f"Build complete: {patches_ok} patches applied")
print(f"Size: {len(html):,} bytes (was {original_len:,}, delta {len(html)-original_len:+,})")
write(DST, html)
print(f"Output: {DST}")
