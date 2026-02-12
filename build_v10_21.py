#!/usr/bin/env python3
"""
Build V10_21 from V10_20:
1. Add bid hint (show AI-recommended bid when HINT_MODE is on)
2. Fix Nello multiplier bug (2X/3X bid should award correct marks when playing Nello)
"""
import sys

SRC = "/var/lib/freelancer/projects/40101953/TN51_Dominoes_V10_20.html"
DST = "/var/lib/freelancer/projects/40101953/TN51_Dominoes_V10_21.html"

with open(SRC, "r", encoding="utf-8") as f:
    code = f.read()

patches_applied = 0

def patch(label, old, new):
    global code, patches_applied
    if old not in code:
        print(f"FAILED: {label} — old string not found")
        sys.exit(1)
    count = code.count(old)
    if count > 1:
        print(f"WARNING: {label} — old string found {count} times, replacing first only")
    code = code.replace(old, new, 1)
    patches_applied += 1
    print(f"OK: {label}")

# ===========================================================================
# PATCH 1: Add bid hint display element to bidding overlay HTML
# Add a small hint text below the bid value display
# ===========================================================================

patch("P1: Add bid hint element to bidding overlay",
    """<div class="bidCurrentValue" id="bidValueDisplay">34</div>""",
    """<div class="bidCurrentValue" id="bidValueDisplay">34</div>
      <div id="bidHintDisplay" style="font-size:12px;color:#aaa;text-align:center;margin-top:4px;min-height:16px;"></div>""")


# ===========================================================================
# PATCH 2: Show bid hint when bid overlay opens (in showBidOverlay)
# After setupBidSlider() call, if HINT_MODE is on, show AI recommendation
# ===========================================================================

patch("P2: Show bid hint in showBidOverlay",
    """function showBidOverlay(show) {
  document.getElementById('bidBackdrop').style.display = show ? 'flex' : 'none';
  if(show) {
    setupBidSlider();
    // Enable bidding preview - allows clicking dominoes to preview trump sorting
    enableBiddingPreview();
  } else {""",
    """function showBidOverlay(show) {
  document.getElementById('bidBackdrop').style.display = show ? 'flex' : 'none';
  if(show) {
    setupBidSlider();
    updateBidHint();
    // Enable bidding preview - allows clicking dominoes to preview trump sorting
    enableBiddingPreview();
  } else {""")


# ===========================================================================
# PATCH 3: Add updateBidHint() function after updateBidDisplay()
# Uses evaluateHandForBid to get AI recommendation and displays it
# ===========================================================================

patch("P3: Add updateBidHint function",
    """function updateBidDisplay() {
  const display = document.getElementById('bidValueDisplay');
  display.textContent = currentBidSelection;
}""",
    """function updateBidDisplay() {
  const display = document.getElementById('bidValueDisplay');
  display.textContent = currentBidSelection;
}

function updateBidHint() {
  const hintEl = document.getElementById('bidHintDisplay');
  if(!hintEl) return;

  if(!HINT_MODE){
    hintEl.textContent = '';
    return;
  }

  try {
    // Get the current bidder's hand
    const bidder = biddingState ? biddingState.currentBidder : 0;
    const hand = session.game.hands[bidder] || [];
    if(hand.length === 0){
      hintEl.textContent = '';
      return;
    }

    // Run AI evaluation
    const evaluation = evaluateHandForBid(hand);

    if(evaluation.action === 'pass'){
      hintEl.textContent = 'AI recommends: Pass';
      hintEl.style.color = '#f87171'; // red-ish
    } else {
      // Check if AI's bid is higher than current high bid
      const highBid = biddingState ? biddingState.highBid : 0;
      if(evaluation.bid > highBid){
        hintEl.textContent = 'AI recommends: Bid ' + evaluation.bid;
        hintEl.style.color = '#4ade80'; // green
      } else {
        // AI would bid but can't beat current bid
        hintEl.textContent = 'AI recommends: Pass (would bid ' + evaluation.bid + ')';
        hintEl.style.color = '#fbbf24'; // yellow/amber
      }
    }
  } catch(e) {
    hintEl.textContent = '';
    console.log("Bid hint error:", e);
  }
}""")


# ===========================================================================
# PATCH 4: Fix Nello multiplier bug — use actual bid marks instead of hardcoded 1
# When selecting Nello from trump selection, pass the real marks from the bid
# ===========================================================================

patch("P4: Fix Nello multiplier - NELLO case",
    """  if(trump === 'NELLO'){
    document.getElementById('trumpBackdrop').style.display = 'none';
    selectedTrump = null;
    showNelloOpponentSelection(1);
    return;
  }
  if(trump === 'NELLO_2'){
    document.getElementById('trumpBackdrop').style.display = 'none';
    selectedTrump = null;
    showNelloOpponentSelection(2);
    return;
  }""",
    """  if(trump === 'NELLO' || trump === 'NELLO_2'){
    document.getElementById('trumpBackdrop').style.display = 'none';
    selectedTrump = null;
    // Use the actual bid marks from the bidding phase (not hardcoded)
    // This ensures 2X/3X multiplier bids carry through to Nello scoring
    const nelloMarks = session.bid_marks || (biddingState ? biddingState.highMarks : 1) || 1;
    showNelloOpponentSelection(nelloMarks);
    return;
  }""")


# ===========================================================================
# PATCH 5: Clear bid hint when overlay hides
# ===========================================================================

patch("P5: Clear bid hint when overlay closes",
    """  } else {
    // Save the previewed trump before disabling (for trump selection phase)
    biddingPreviewedTrump = previewedTrump;""",
    """  } else {
    // Clear bid hint
    const hintEl = document.getElementById('bidHintDisplay');
    if(hintEl) hintEl.textContent = '';
    // Save the previewed trump before disabling (for trump selection phase)
    biddingPreviewedTrump = previewedTrump;""")


# ===========================================================================
# Write output
# ===========================================================================

with open(DST, "w", encoding="utf-8") as f:
    f.write(code)

print(f"\nDone — {patches_applied} patches applied → {DST}")
print(f"Output size: {len(code):,} bytes")
