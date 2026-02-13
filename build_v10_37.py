#!/usr/bin/env python3
"""
Build V10_37: Fix Pass & Play trump selection and play phase rotation bugs
- Fix finalizeBidding() to rotate board to bid winner before trump overlay
- Fix enableTrumpDominoClicks/disableTrumpDominoClicks to use PP active seat
- Fix handlePlayer1Click trump routing to use PP active seat
- Fix sortPlayerHandByTrump to sort PP active seat's hand
- Fix confirmTrumpSelection to handle PP mode transition to play
- Fix enableBiddingPreview to use PP active seat
"""

import re, sys

SRC = "TN51_Dominoes_V10_36.html"
DST = "TN51_Dominoes_V10_37.html"

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
# PATCH 1: Fix finalizeBidding() — rotate to bid winner before showing trump overlay
# When a human wins the bid in PP mode, we need to rotate the board to them
# BEFORE showing the trump overlay so they see their own tiles.
# Also: since it's the same player going from bid→trump, NO privacy screen needed.
# =============================================================================
patch("PATCH 1: Rotate to bid winner before trump overlay",
    """  session.phase = PHASE_NEED_TRUMP;
  session.status = `You won the bid (${biddingState.highBid}). Pick trump.`;
  setStatus(session.status);
  showTrumpOverlay(true);
  return { done: true, winner: winnerSeat, bid: biddingState.highBid };
}""",
    """  session.phase = PHASE_NEED_TRUMP;

  // In PP mode, rotate board to the bid winner before showing trump overlay
  if (PASS_AND_PLAY_MODE) {
    const bidderLabel = `P${seatToPlayer(winnerSeat)}`;
    session.status = `${bidderLabel} won the bid (${biddingState.highBid}). Pick trump.`;
    setStatus(session.status);
    // Rotate board to bid winner (no privacy screen — same player just bid)
    ppRotateBoard(winnerSeat);
    showTrumpOverlay(true);
    return { done: true, winner: winnerSeat, bid: biddingState.highBid };
  }

  session.status = `You won the bid (${biddingState.highBid}). Pick trump.`;
  setStatus(session.status);
  showTrumpOverlay(true);
  return { done: true, winner: winnerSeat, bid: biddingState.highBid };
}""")

# =============================================================================
# PATCH 2: Fix enableTrumpDominoClicks — use PP active seat instead of sprites[0]
# =============================================================================
patch("PATCH 2: Fix enableTrumpDominoClicks for PP mode",
    """function enableTrumpDominoClicks(){
  trumpSelectionActive = true;
  // Bring player's dominoes above the overlay and make them clickable
  const seatSprites = sprites[0] || [];""",
    """function enableTrumpDominoClicks(){
  trumpSelectionActive = true;
  // Bring player's dominoes above the overlay and make them clickable
  const activeSeat = PASS_AND_PLAY_MODE ? ppActiveViewSeat : 0;
  const seatSprites = sprites[activeSeat] || [];""")

# =============================================================================
# PATCH 3: Fix disableTrumpDominoClicks — use PP active seat instead of sprites[0]
# =============================================================================
patch("PATCH 3: Fix disableTrumpDominoClicks for PP mode",
    """function disableTrumpDominoClicks(){
  trumpSelectionActive = false;
  clearTrumpHighlights();
  // Reset z-index and remove clickable for player's dominoes
  const seatSprites = sprites[0] || [];""",
    """function disableTrumpDominoClicks(){
  trumpSelectionActive = false;
  clearTrumpHighlights();
  // Reset z-index and remove clickable for player's dominoes
  const activeSeat = PASS_AND_PLAY_MODE ? ppActiveViewSeat : 0;
  const seatSprites = sprites[activeSeat] || [];""")

# =============================================================================
# PATCH 4: Fix handlePlayer1Click trump routing — use PP active seat
# =============================================================================
patch("PATCH 4: Fix trump click routing for PP mode",
    """  // If in trump selection mode, route to trump selection instead
  if(trumpSelectionActive && session.phase === PHASE_NEED_TRUMP){
    const spriteData = sprites[0][spriteSlotIndex];
    if(spriteData && spriteData.tile){
      handleTrumpDominoClick(spriteData.tile);
    }
    return;
  }

  // If in bidding preview mode, route to bidding preview handler
  if(biddingPreviewActive && session.phase === PHASE_NEED_BID){
    const spriteData = sprites[0][spriteSlotIndex];
    if(spriteData && spriteData.tile){
      handleBiddingDominoClick(spriteData.tile);
    }
    return;
  }""",
    """  // If in trump selection mode, route to trump selection instead
  if(trumpSelectionActive && session.phase === PHASE_NEED_TRUMP){
    const trumpSeat = PASS_AND_PLAY_MODE ? ppActiveViewSeat : 0;
    const spriteData = sprites[trumpSeat][spriteSlotIndex];
    if(spriteData && spriteData.tile){
      handleTrumpDominoClick(spriteData.tile);
    }
    return;
  }

  // If in bidding preview mode, route to bidding preview handler
  if(biddingPreviewActive && session.phase === PHASE_NEED_BID){
    const bidSeat = PASS_AND_PLAY_MODE ? ppActiveViewSeat : 0;
    const spriteData = sprites[bidSeat][spriteSlotIndex];
    if(spriteData && spriteData.tile){
      handleBiddingDominoClick(spriteData.tile);
    }
    return;
  }""")

# =============================================================================
# PATCH 5: Fix sortPlayerHandByTrump — use PP active seat instead of sprites[0]
# =============================================================================
patch("PATCH 5: Fix sortPlayerHandByTrump for PP mode",
    """function sortPlayerHandByTrump(){
  const seatSprites = sprites[0] || [];""",
    """function sortPlayerHandByTrump(){
  const sortSeat = PASS_AND_PLAY_MODE ? ppActiveViewSeat : 0;
  const seatSprites = sprites[sortSeat] || [];""")

# =============================================================================
# PATCH 6: Fix enableBiddingPreview — use PP active seat instead of sprites[0]
# =============================================================================
patch("PATCH 6: Fix enableBiddingPreview for PP mode",
    """function enableBiddingPreview(){
  biddingPreviewActive = true;
  previewedTrump = null;
  // Clear any existing highlights before starting preview mode
  clearTrumpHighlights();
  // Bring player's dominoes above the overlay and make them clickable
  const seatSprites = sprites[0] || [];""",
    """function enableBiddingPreview(){
  biddingPreviewActive = true;
  previewedTrump = null;
  // Clear any existing highlights before starting preview mode
  clearTrumpHighlights();
  // Bring player's dominoes above the overlay and make them clickable
  const activeSeat = PASS_AND_PLAY_MODE ? ppActiveViewSeat : 0;
  const seatSprites = sprites[activeSeat] || [];""")

# =============================================================================
# PATCH 7: Fix confirmTrumpSelection — add PP mode handling for play phase start
# The bid winner just selected trump, now they lead the first trick.
# In PP mode: since it's the same player, NO privacy screen — just enable clicks.
# =============================================================================
patch("PATCH 7: Fix confirmTrumpSelection for PP mode",
    """  // Setup for playing
  const currentPlayer = session.game.current_player;
  console.log("confirmTrumpSelection - currentPlayer:", currentPlayer);
  console.log("confirmTrumpSelection - session.phase:", session.phase);
  console.log("confirmTrumpSelection - bid_winner_seat:", session.bid_winner_seat);

  if(currentPlayer === 0){
    console.log("Setting up for player 0 to play");
    waitingForPlayer1 = true;
    enablePlayer1Clicks();
    updatePlayer1ValidStates();
  } else {
    console.log("AI will play first, current_player:", currentPlayer);
    waitingForPlayer1 = false;
    disablePlayer1Clicks();
    setTimeout(() => aiPlayTurn(), 500);
  }""",
    """  // Setup for playing
  const currentPlayer = session.game.current_player;
  console.log("confirmTrumpSelection - currentPlayer:", currentPlayer);
  console.log("confirmTrumpSelection - session.phase:", session.phase);
  console.log("confirmTrumpSelection - bid_winner_seat:", session.bid_winner_seat);

  if(PASS_AND_PLAY_MODE) {
    // PP mode: bid winner leads first trick
    // Board is already rotated to bid winner from finalizeBidding
    // No privacy screen needed — same player just picked trump
    if(ppIsHuman(currentPlayer)) {
      ppActiveViewSeat = currentPlayer;
      waitingForPlayer1 = true;
      ppEnableClicksForSeat(currentPlayer);
      ppUpdateValidStates(currentPlayer);
    } else {
      // AI won bid somehow (shouldn't happen — AI trump is handled elsewhere)
      waitingForPlayer1 = false;
      ppAIPlayLoop();
    }
  } else if(currentPlayer === 0){
    console.log("Setting up for player 0 to play");
    waitingForPlayer1 = true;
    enablePlayer1Clicks();
    updatePlayer1ValidStates();
  } else {
    console.log("AI will play first, current_player:", currentPlayer);
    waitingForPlayer1 = false;
    disablePlayer1Clicks();
    setTimeout(() => aiPlayTurn(), 500);
  }""")

# =============================================================================
# PATCH 8: Fix clearTrumpHighlights — use PP active seat for highlight cleanup
# =============================================================================
patch("PATCH 8: Fix clearTrumpHighlights for PP mode",
    """function clearTrumpHighlights(){
  const seatSprites = sprites[0] || [];""",
    """function clearTrumpHighlights(){
  const activeSeat = PASS_AND_PLAY_MODE ? ppActiveViewSeat : 0;
  const seatSprites = sprites[activeSeat] || [];""")

# =============================================================================
# PATCH 9: Fix disableBiddingPreview — use PP active seat instead of sprites[0]
# =============================================================================
patch("PATCH 9: Fix disableBiddingPreview for PP mode",
    """function disableBiddingPreview(){
  biddingPreviewActive = false;
  previewedTrump = null;
  clearTrumpHighlights();
  // Reset z-index and remove clickable for player's dominoes
  const seatSprites = sprites[0] || [];""",
    """function disableBiddingPreview(){
  biddingPreviewActive = false;
  previewedTrump = null;
  clearTrumpHighlights();
  // Reset z-index and remove clickable for player's dominoes
  const activeSeat = PASS_AND_PLAY_MODE ? ppActiveViewSeat : 0;
  const seatSprites = sprites[activeSeat] || [];""")

print(f"\n{'='*60}")
print(f"Build complete: {patches_ok} patches applied")
print(f"Size: {len(html):,} bytes (was {original_len:,}, delta {len(html)-original_len:+,})")
write(DST, html)
print(f"Output: {DST}")
