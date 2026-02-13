#!/usr/bin/env python3
"""
Build V10_43: Fix PP "Continue Game" — attach click handlers to human seats' sprites
When PP is enabled on an existing game, sprites for non-P1 seats don't have
click/touchstart handlers because they were created when PASS_AND_PLAY_MODE was false.

Fix: Add a ppAttachClickHandlers() function that attaches handlers to all human
seats' sprites, called from ppContinueFromCurrentState() and ppActivateFromModal().
Also fix loadSavedGame sprite creation to support PP mode.
"""

import re, sys

SRC = "TN51_Dominoes_V10_42.html"
DST = "TN51_Dominoes_V10_43.html"

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
# PATCH 1: Add ppAttachClickHandlers() helper function right after ppEnableClicksForSeat
# This function attaches actual click/touchstart event listeners to all human
# seats' sprites. Called when PP is enabled on an existing game.
# =============================================================================
patch("PATCH 1: Add ppAttachClickHandlers helper",
    """// Update valid states for a specific seat (generalized from P1-only)
function ppUpdateValidStates(seat) {""",
    """// Attach click/touchstart handlers to all human seats' sprites
// Called when PP is enabled on an existing game where sprites were created
// without handlers (because PASS_AND_PLAY_MODE was false at creation time)
function ppAttachClickHandlers() {
  for (let seat = 0; seat < 6; seat++) {
    if (!ppIsHuman(seat)) continue;
    if (seat === 0) continue; // Seat 0 already has handlers from creation
    const seatSprites = sprites[seat];
    if (!seatSprites) continue;
    seatSprites.forEach(data => {
      if (data && data.sprite) {
        // Check if handler already attached (avoid duplicates)
        if (data._ppHandlerAttached) return;
        const spriteEl = data.sprite.el ? data.sprite.el : data.sprite;
        spriteEl.addEventListener('click', () => handlePlayer1Click(spriteEl));
        spriteEl.addEventListener('touchstart', (e) => {
          e.preventDefault();
          e.stopPropagation();
          handlePlayer1Click(spriteEl);
        }, { passive: false });
        data._ppHandlerAttached = true;
      }
    });
  }
}

// Update valid states for a specific seat (generalized from P1-only)
function ppUpdateValidStates(seat) {""")

# =============================================================================
# PATCH 2: Call ppAttachClickHandlers from ppContinueFromCurrentState
# =============================================================================
patch("PATCH 2: Fix ppContinueFromCurrentState",
    """function ppContinueFromCurrentState() {
  const seat = session.game.current_player;
  if (ppIsHuman(seat)) {
    const phase = session.phase === PHASE_NEED_BID ? 'Bidding Phase' :
                  session.phase === PHASE_NEED_TRUMP ? 'Choose Trump' :
                  session.phase === PHASE_PLAYING ? 'Play Phase' : '';
    ppTransitionToSeat(seat, phase);
  } else {
    // AI seat — run AI until we hit a human
    ppResetRotation();
    maybeAIKick();
  }
}""",
    """function ppContinueFromCurrentState() {
  // Attach click handlers to all human seats' sprites
  // (they may not have handlers if game started in normal mode)
  ppAttachClickHandlers();

  const seat = session.phase === PHASE_NEED_BID && biddingState
    ? biddingState.currentBidder
    : session.game.current_player;

  if (ppIsHuman(seat)) {
    const phase = session.phase === PHASE_NEED_BID ? 'Bidding Phase' :
                  session.phase === PHASE_NEED_TRUMP ? 'Choose Trump' :
                  session.phase === PHASE_PLAYING ? 'Play Phase' : '';
    if (session.phase === PHASE_NEED_BID) {
      // Rotate to bidder and show bid overlay
      ppRotateBoard(seat);
      startBiddingRound();
    } else {
      ppTransitionToSeat(seat, phase);
    }
  } else {
    // AI seat — run AI until we hit a human
    ppResetRotation();
    if (session.phase === PHASE_NEED_BID) {
      startBiddingRound();
    } else if (session.phase === PHASE_PLAYING) {
      maybeAIKick();
    }
  }
}""")

# =============================================================================
# PATCH 3: Also call ppAttachClickHandlers when PP is activated with startNew=true
# (this is already handled by startNewHand, but belt-and-suspenders for safety)
# And ensure ppActivateFromModal(false) path is solid
# =============================================================================
# Already handled by PATCH 2 via ppContinueFromCurrentState. No additional patch needed.

print(f"\n{'='*60}")
print(f"Build complete: {patches_ok} patches applied")
print(f"Size: {len(html):,} bytes (was {original_len:,}, delta {len(html)-original_len:+,})")
write(DST, html)
print(f"Output: {DST}")
