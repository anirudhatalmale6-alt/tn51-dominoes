#!/usr/bin/env python3
"""
Build script for TN51 Dominoes V10_50
Patches V10_47 HTML file with 5 changes:

1. Persistent boneyard timing fix - hide BEFORE animation, 1000ms delay after
2. Game Settings popup - marks-to-win moved off start screen, shown after New Game
3. Trump selection hint - AI recommends suit/doubles/no-trump during trump pick phase
4. AI bug fix: partner winning should never dump trumps when non-trump options exist
5. AI bug fix: trump lead should pick lowest value trump, not highest rank
"""

import sys
import os

INPUT_FILE = os.path.join(os.path.dirname(__file__), 'TN51_Dominoes_V10_47.html')
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), 'TN51_Dominoes_V10_50.html')

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def apply_patch(html, old, new, patch_name):
    if old not in html:
        print(f"  WARNING: Could not find patch target for '{patch_name}'")
        print(f"  Looking for: {old[:80]}...")
        return html, False
    count = html.count(old)
    if count > 1:
        print(f"  WARNING: Found {count} occurrences for '{patch_name}', replacing first only")
        idx = html.index(old)
        html = html[:idx] + new + html[idx + len(old):]
        return html, True
    html = html.replace(old, new)
    print(f"  OK: {patch_name}")
    return html, True

def main():
    print(f"Reading {INPUT_FILE}...")
    html = read_file(INPUT_FILE)
    patches_applied = 0
    patches_failed = 0

    # =========================================================================
    # PATCH 1: Persistent boneyard timing fix
    # Hide boneyard BEFORE trick collection animation, 1000ms delay after
    # =========================================================================
    old_boneyard_timing = """  // Refresh boneyard 2 if visible — show trick history temporarily during collection,
  // then bring boneyard back after a short delay
  if(boneyard2Visible){
    // Temporarily show trick history sprites (they just got collected)
    showTrickHistorySprites();
    const container = document.getElementById('boneyard2Container');
    const thBg = document.getElementById('trickHistoryBg');
    if(container) container.style.display = 'none';
    if(thBg) thBg.style.display = '';
    // After delay, bring boneyard back
    setTimeout(() => {
      if(boneyard2Visible){
        hideTrickHistorySprites();
        if(container) container.style.display = 'block';
        if(thBg) thBg.style.display = 'none';
        renderBoneyard2();
      }
    }, 500);
  }"""

    new_boneyard_timing = """  // Refresh boneyard 2 if visible — boneyard was hidden before animation,
  // now bring it back after a 1000ms delay
  if(boneyard2Visible){
    // Trick has been collected — show trick history sprites
    showTrickHistorySprites();
    const container = document.getElementById('boneyard2Container');
    const thBg = document.getElementById('trickHistoryBg');
    // After 1000ms delay, bring boneyard back
    setTimeout(() => {
      if(boneyard2Visible){
        hideTrickHistorySprites();
        if(container) container.style.display = 'block';
        if(thBg) thBg.style.display = 'none';
        renderBoneyard2();
      }
    }, 1000);
  }"""

    html, ok = apply_patch(html, old_boneyard_timing, new_boneyard_timing, "Patch 1a: Boneyard timing - post-collection 1000ms delay")
    if ok: patches_applied += 1
    else: patches_failed += 1

    # Now we need to hide the boneyard BEFORE the trick collection animation starts.
    # The collectToHistory function starts with clearWinningHighlight() and SFX.playCollect()
    # We need to add boneyard hiding right at the start, before the animation loop.
    old_collect_start = """async function collectToHistory(){
  if(playedThisTrick.length === 0) return;

  // Clear winning highlight before collecting
  clearWinningHighlight();

  // Play collect sound
  SFX.playCollect();

  setStatus('Collecting to trick history...');"""

    new_collect_start = """async function collectToHistory(){
  if(playedThisTrick.length === 0) return;

  // Hide boneyard BEFORE animation starts (will be restored after collection + delay)
  if(boneyard2Visible){
    const by2c = document.getElementById('boneyard2Container');
    const thBg = document.getElementById('trickHistoryBg');
    if(by2c) by2c.style.display = 'none';
    if(thBg) thBg.style.display = '';
    showTrickHistorySprites();
  }

  // Clear winning highlight before collecting
  clearWinningHighlight();

  // Play collect sound
  SFX.playCollect();

  setStatus('Collecting to trick history...');"""

    html, ok = apply_patch(html, old_collect_start, new_collect_start, "Patch 1b: Boneyard timing - hide BEFORE animation")
    if ok: patches_applied += 1
    else: patches_failed += 1

    # =========================================================================
    # PATCH 2: Game Settings popup - marks-to-win moved off start screen
    # =========================================================================

    # 2a: Remove marks selection from start screen HTML
    old_marks_html = """    <div id="marksSelection" style="text-align:center;margin-bottom:8px;">
      <div style="font-size:12px;color:rgba(255,255,255,0.7);margin-bottom:6px;">Marks to Win</div>
      <div style="display:flex;gap:8px;justify-content:center;">
        <button class="glossBtn marksBtn" data-marks="3" style="padding:6px 14px;font-size:13px;background:linear-gradient(135deg,#6366f1,#4f46e5);border:none;border-radius:8px;color:#fff;cursor:pointer;">3<br><span style="font-size:9px;opacity:0.7;">Short</span></button>
        <button class="glossBtn marksBtn marksSelected" data-marks="7" style="padding:6px 14px;font-size:13px;background:linear-gradient(135deg,#22c55e,#16a34a);border:2px solid #fff;border-radius:8px;color:#fff;cursor:pointer;">7<br><span style="font-size:9px;opacity:0.7;">Standard</span></button>
        <button class="glossBtn marksBtn" data-marks="15" style="padding:6px 14px;font-size:13px;background:linear-gradient(135deg,#f59e0b,#d97706);border:none;border-radius:8px;color:#fff;cursor:pointer;">15<br><span style="font-size:9px;opacity:0.7;">Long</span></button>
      </div>
    </div>"""

    new_marks_html = ""  # Remove it entirely

    html, ok = apply_patch(html, old_marks_html, new_marks_html, "Patch 2a: Remove marks selection from start screen")
    if ok: patches_applied += 1
    else: patches_failed += 1

    # 2b: Add Game Settings popup HTML (before the start screen div)
    old_start_screen_div = """<div class="modalBackdrop" id="startScreenBackdrop" style="display:flex; background:transparent;">"""

    new_start_screen_div = """<!-- Game Settings Popup -->
<div class="modalBackdrop" id="gameSettingsBackdrop" style="display:none;">
  <div class="modalPanel" style="max-width:320px;background:linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);border-radius:16px;border:1px solid rgba(255,255,255,0.2);box-shadow:0 8px 32px rgba(0,0,0,0.4);">
    <div class="modalHeader" style="border-bottom:1px solid rgba(255,255,255,0.15);padding:14px 16px;">
      <span style="font-size:18px;font-weight:700;color:#fff;">Game Settings</span>
    </div>
    <div class="modalBody" style="padding:16px;">
      <div style="text-align:center;margin-bottom:16px;">
        <div style="font-size:13px;color:rgba(255,255,255,0.8);margin-bottom:10px;font-weight:600;">Marks to Win</div>
        <div style="display:flex;gap:10px;justify-content:center;">
          <button class="glossBtn gsMarksBtn" data-marks="3" style="padding:8px 18px;font-size:14px;background:linear-gradient(135deg,#6366f1,#4f46e5);border:none;border-radius:10px;color:#fff;cursor:pointer;min-width:60px;">3<br><span style="font-size:10px;opacity:0.7;">Short</span></button>
          <button class="glossBtn gsMarksBtn gsMarksSelected" data-marks="7" style="padding:8px 18px;font-size:14px;background:linear-gradient(135deg,#22c55e,#16a34a);border:2px solid #fff;border-radius:10px;color:#fff;cursor:pointer;min-width:60px;">7<br><span style="font-size:10px;opacity:0.7;">Standard</span></button>
          <button class="glossBtn gsMarksBtn" data-marks="15" style="padding:8px 18px;font-size:14px;background:linear-gradient(135deg,#f59e0b,#d97706);border:none;border-radius:10px;color:#fff;cursor:pointer;min-width:60px;">15<br><span style="font-size:10px;opacity:0.7;">Long</span></button>
        </div>
      </div>
    </div>
    <div class="modalFooter" style="border-top:1px solid rgba(255,255,255,0.15);padding:12px 16px;text-align:center;">
      <button class="glossBtn glossGreen" id="btnGameSettingsStart" style="padding:10px 32px;font-size:15px;font-weight:700;border-radius:10px;">Start Game</button>
    </div>
  </div>
</div>

<div class="modalBackdrop" id="startScreenBackdrop" style="display:flex; background:transparent;">"""

    html, ok = apply_patch(html, old_start_screen_div, new_start_screen_div, "Patch 2b: Add Game Settings popup HTML")
    if ok: patches_applied += 1
    else: patches_failed += 1

    # 2c: Replace old marks JS with new game settings JS
    old_marks_js = """// Marks to win selection
let selectedMarksToWin = 7;
document.querySelectorAll('.marksBtn').forEach(btn => {
  btn.addEventListener('click', () => {
    selectedMarksToWin = parseInt(btn.dataset.marks);
    document.querySelectorAll('.marksBtn').forEach(b => {
      b.style.border = 'none';
      b.classList.remove('marksSelected');
    });
    btn.style.border = '2px solid #fff';
    btn.classList.add('marksSelected');
  });
});

// Start screen button handlers
document.getElementById('btnStartNewGame').addEventListener('click', () => {
  hideStartScreen();
  clearSavedGame();
  session.marks_to_win = selectedMarksToWin;
  startNewHand();
});"""

    new_marks_js = """// Game Settings popup
let selectedMarksToWin = 7;

function showGameSettings(){
  document.getElementById('gameSettingsBackdrop').style.display = 'flex';
}
function hideGameSettings(){
  document.getElementById('gameSettingsBackdrop').style.display = 'none';
}

document.querySelectorAll('.gsMarksBtn').forEach(btn => {
  btn.addEventListener('click', () => {
    selectedMarksToWin = parseInt(btn.dataset.marks);
    document.querySelectorAll('.gsMarksBtn').forEach(b => {
      b.style.border = 'none';
      b.classList.remove('gsMarksSelected');
    });
    btn.style.border = '2px solid #fff';
    btn.classList.add('gsMarksSelected');
  });
});

document.getElementById('btnGameSettingsStart').addEventListener('click', () => {
  hideGameSettings();
  clearSavedGame();
  session.marks_to_win = selectedMarksToWin;
  startNewHand();
});

// Start screen button handlers — New Game now opens Game Settings popup
document.getElementById('btnStartNewGame').addEventListener('click', () => {
  hideStartScreen();
  showGameSettings();
});"""

    html, ok = apply_patch(html, old_marks_js, new_marks_js, "Patch 2c: Game Settings popup JS")
    if ok: patches_applied += 1
    else: patches_failed += 1

    # =========================================================================
    # PATCH 3: Trump selection hint
    # Add AI recommendation to the trump overlay using aiChooseTrump
    # =========================================================================

    # 3a: Add a hint label to the trump overlay HTML (below the header)
    old_trump_header = """    <div class="modalHeader">
      <span>Pick Trump</span>
    </div>
    <div class="modalBody">
      <!-- Central pip display -->"""

    new_trump_header = """    <div class="modalHeader">
      <span>Pick Trump</span>
    </div>
    <div id="trumpHintBar" style="display:none;text-align:center;padding:6px 12px;background:rgba(255,255,255,0.1);border-bottom:1px solid rgba(255,255,255,0.1);font-size:12px;color:#a5f3fc;">
      <span style="opacity:0.7;">AI suggests: </span><span id="trumpHintText" style="font-weight:700;color:#4ade80;"></span>
    </div>
    <div class="modalBody">
      <!-- Central pip display -->"""

    html, ok = apply_patch(html, old_trump_header, new_trump_header, "Patch 3a: Trump hint bar HTML")
    if ok: patches_applied += 1
    else: patches_failed += 1

    # 3b: Add trump hint logic to buildTrumpOptions (show hint when overlay appears)
    old_build_trump_end = """  // Show/hide Nel-O button based on bid
  nelloBtn.style.display = showNello ? 'block' : 'none';"""

    new_build_trump_end = """  // Show/hide Nel-O button based on bid
  nelloBtn.style.display = showNello ? 'block' : 'none';

  // Trump selection hint
  if(HINT_MODE){
    const hintSeat = PASS_AND_PLAY_MODE ? ppActiveViewSeat : 0;
    const hintHand = session.game.hands[hintSeat] || [];
    const hintBid = session.current_bid || 34;
    const aiTrump = aiChooseTrump(hintHand, hintBid);
    const hintBar = document.getElementById('trumpHintBar');
    const hintText = document.getElementById('trumpHintText');
    if(hintBar && hintText){
      let label = '';
      if(aiTrump === 'NELLO') label = 'Nel-O';
      else if(aiTrump === 'NT') label = 'No Trump (Doubles)';
      else if(typeof aiTrump === 'number') label = aiTrump + 's Trump';
      else label = String(aiTrump);
      hintText.textContent = label;
      hintBar.style.display = 'block';

      // Pre-select the AI's recommendation
      if(biddingPreviewedTrump === null){
        if(aiTrump === 'NELLO' && showNello){
          selectedTrump = 'NELLO';
          nelloBtn.classList.add('selected');
          document.getElementById('btnTrumpConfirm').disabled = false;
        } else if(aiTrump === 'NT'){
          selectedTrump = 'DOUBLES';
          doublesBtn.classList.add('selected');
          document.getElementById('btnTrumpConfirm').disabled = false;
          highlightTrumpDominoes('DOUBLES');
        } else if(typeof aiTrump === 'number'){
          selectedTrump = aiTrump;
          slider.value = aiTrump;
          document.getElementById('btnTrumpConfirm').disabled = false;
          highlightTrumpDominoes(aiTrump);
          updateTrumpDisplay(aiTrump);
        }
      }
    }
  } else {
    const hintBar = document.getElementById('trumpHintBar');
    if(hintBar) hintBar.style.display = 'none';
  }"""

    html, ok = apply_patch(html, old_build_trump_end, new_build_trump_end, "Patch 3b: Trump hint logic in buildTrumpOptions")
    if ok: patches_applied += 1
    else: patches_failed += 1

    # =========================================================================
    # PATCH 4: AI bug fix - partner winning should never dump trumps
    # =========================================================================
    old_partner_winning = """  // ── Partner/teammate winning: throw count ──
  if(partnerWinning){
    let countIdx = -1, countVal = 0, lowIdx = legal[0], lowVal = Infinity;
    for(const idx of legal){
      const tile = hand[idx];
      const pipSum = tile[0] + tile[1];
      if(pipSum === 5 || pipSum === 10){
        if(pipSum > countVal){ countVal = pipSum; countIdx = idx; }
      }
      if(pipSum < lowVal){ lowVal = pipSum; lowIdx = idx; }
    }
    if(countIdx >= 0) return makeResult(countIdx, "Partner winning, throw count (" + countVal + "pts)");
    return makeResult(lowIdx, "Partner winning, play low");
  }"""

    new_partner_winning = """  // ── Partner/teammate winning: throw count (but NEVER dump trumps if non-trump options exist) ──
  if(partnerWinning){
    // Separate legal tiles into trump and non-trump
    const pwNonTrumps = [];
    const pwTrumps = [];
    for(const idx of legal){
      if(gameState._is_trump_tile(hand[idx])) pwTrumps.push(idx);
      else pwNonTrumps.push(idx);
    }
    // Use non-trump tiles if available; only fall back to trumps if ALL tiles are trump
    const pwCandidates = pwNonTrumps.length > 0 ? pwNonTrumps : pwTrumps;

    let countIdx = -1, countVal = 0, lowIdx = pwCandidates[0], lowVal = Infinity;
    for(const idx of pwCandidates){
      const tile = hand[idx];
      const pipSum = tile[0] + tile[1];
      if(pipSum === 5 || pipSum === 10){
        if(pipSum > countVal){ countVal = pipSum; countIdx = idx; }
      }
      if(pipSum < lowVal){ lowVal = pipSum; lowIdx = idx; }
    }
    if(countIdx >= 0) return makeResult(countIdx, "Partner winning, throw count (" + countVal + "pts)");
    return makeResult(lowIdx, "Partner winning, play low");
  }"""

    html, ok = apply_patch(html, old_partner_winning, new_partner_winning, "Patch 4: Partner winning - never dump trumps")
    if ok: patches_applied += 1
    else: patches_failed += 1

    # =========================================================================
    # PATCH 5: AI bug fix - trump lead should pick lowest value, not highest rank
    # =========================================================================

    # 5a: Phase A P2 - lead high trump (pulling remaining trumps)
    old_trump_lead_p2 = """      // P2: Lead high trump IF we have the highest remaining
      // BUT respect last-trump protection
      // AND don't waste high trumps pulling partner's trumps
      if(otherTrumps.length > 0 && iHaveHighestTrump && !shouldSaveLastTrump && !partnersHoldRemainingTrumps){
        let bestIdx = otherTrumps[0], bestR = -1;
        for(const idx of otherTrumps){
          const r = getTrumpRankNum(hand[idx]);
          if(r > bestR){ bestR = r; bestIdx = idx; }
        }
        return makeResult(bestIdx, "Lead: high trump (pulling remaining trumps)");
      }"""

    new_trump_lead_p2 = """      // P2: Lead trump IF we have the highest remaining
      // BUT respect last-trump protection
      // AND don't waste high trumps pulling partner's trumps
      // PICK LOWEST VALUE trump to avoid wasting count tiles (5-1 worth 5pts, etc.)
      if(otherTrumps.length > 0 && iHaveHighestTrump && !shouldSaveLastTrump && !partnersHoldRemainingTrumps){
        let bestIdx = otherTrumps[0], bestVal = Infinity;
        for(const idx of otherTrumps){
          const tile = hand[idx];
          const pipSum = tile[0] + tile[1];
          if(pipSum < bestVal){ bestVal = pipSum; bestIdx = idx; }
        }
        return makeResult(bestIdx, "Lead: low-value trump (pulling remaining trumps)");
      }"""

    html, ok = apply_patch(html, old_trump_lead_p2, new_trump_lead_p2, "Patch 5a: Trump lead P2 - pick lowest value")
    if ok: patches_applied += 1
    else: patches_failed += 1

    # 5b: Phase A P3 - early trump aggression
    old_trump_lead_p3 = """      // P3: Early game trump aggression — lead trump even without highest
      // if we have 2+ trumps, it's trick 0 or 1, and bid isn't safe yet
      // Skip if remaining trumps are only held by partners (don't pull partner trumps)
      if(otherTrumps.length >= 2 && trickNum <= 1 && !bidIsSafe && !partnersHoldRemainingTrumps){
        // Lead highest trump to force opponents' trumps out early
        let bestIdx = otherTrumps[0], bestR = -1;
        for(const idx of otherTrumps){
          const r = getTrumpRankNum(hand[idx]);
          if(r > bestR){ bestR = r; bestIdx = idx; }
        }
        return makeResult(bestIdx, "Lead: early trump (forcing opponent trumps)");
      }"""

    new_trump_lead_p3 = """      // P3: Early game trump aggression — lead trump even without highest
      // if we have 2+ trumps, it's trick 0 or 1, and bid isn't safe yet
      // Skip if remaining trumps are only held by partners (don't pull partner trumps)
      // PICK LOWEST VALUE trump to avoid wasting count tiles
      if(otherTrumps.length >= 2 && trickNum <= 1 && !bidIsSafe && !partnersHoldRemainingTrumps){
        let bestIdx = otherTrumps[0], bestVal = Infinity;
        for(const idx of otherTrumps){
          const tile = hand[idx];
          const pipSum = tile[0] + tile[1];
          if(pipSum < bestVal){ bestVal = pipSum; bestIdx = idx; }
        }
        return makeResult(bestIdx, "Lead: early trump (forcing opponent trumps)");
      }"""

    html, ok = apply_patch(html, old_trump_lead_p3, new_trump_lead_p3, "Patch 5b: Trump lead P3 - pick lowest value")
    if ok: patches_applied += 1
    else: patches_failed += 1

    # =========================================================================
    # PATCH 6: Update version string
    # =========================================================================
    old_version = 'Tennessee 51</div>'
    # Find the one in the start screen
    new_version = 'Tennessee 51</div>'
    # Actually the title stays the same - version is in filename only.

    # =========================================================================
    # DONE
    # =========================================================================
    print(f"\nResults: {patches_applied} patches applied, {patches_failed} failed")

    if patches_failed > 0:
        print("WARNING: Some patches failed! Check output carefully.")

    write_file(OUTPUT_FILE, html)
    print(f"Written to {OUTPUT_FILE}")
    print(f"File size: {len(html):,} bytes")

if __name__ == '__main__':
    main()
