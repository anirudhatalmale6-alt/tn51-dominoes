#!/usr/bin/env python3
"""
Build V10_20 from V10_19:
1. Fix end-of-trick state bug (clear current_trick before debug AI run)
2. Effective top rank (context-aware inferred void per trick)
3. Retroactive cross-trick void analysis (second pass)
4. Hint feature (white shadow on AI-recommended domino, settings toggle)
"""
import sys

SRC = "/var/lib/freelancer/projects/40101953/TN51_Dominoes_V10_19.html"
DST = "/var/lib/freelancer/projects/40101953/TN51_Dominoes_V10_20.html"

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
# PATCH 1: Fix end-of-trick state bug
# The logTrickEnd function calls choose_tile_ai while current_trick still has
# the completed trick's plays. This makes the AI think it's mid-trick (following
# suit) instead of leading the next trick. With only 1 legal move it hits the
# early exit and returns empty/broken debug data.
# Fix: temporarily clear current_trick before the debug AI run.
# ===========================================================================

patch("P1: Fix end-of-trick state - clear current_trick before debug AI run",
    """  let trickEndState = null;
  try {
    // Run AI from seat 0 just to get the debug info (won't actually play)
    const debugRec = choose_tile_ai(session.game, 0, session.contract, true, session.current_bid);""",
    """  let trickEndState = null;
  try {
    // Run AI from seat 0 just to get the debug info (won't actually play)
    // IMPORTANT: Temporarily clear current_trick so AI evaluates as if leading
    // the NEXT trick (current_trick still has the just-completed trick's plays
    // at this point because collectToHistory hasn't finished yet)
    const savedTrick = session.game.current_trick;
    session.game.current_trick = [];
    const debugRec = choose_tile_ai(session.game, 0, session.contract, true, session.current_bid);
    session.game.current_trick = savedTrick;""")


# ===========================================================================
# PATCH 2: Effective top rank — context-aware inferred void
# When multiple opponents play trump on the same trick, evaluate each one's
# played rank against what was AVAILABLE to them (not global top rank).
# If opponent A played 7-6 and opponent B played 7-5, then 7-5 was effectively
# the highest available to B (since A took 7-6). So B gets 90%, not 70%.
# ===========================================================================

patch("P2: Effective top rank - context-aware inferred void scoring",
    """      // Inferred trump void: player played high trump on a losing trick
      // = they were forced to play it (probably their only/last trump)
      // Confidence scales with how high the trump was:
      // - Highest remaining non-double trump → 90% (almost certainly last/only trump)
      // - High trump (top half of remaining) → 70%
      // - Mid-range trump → 50%
      const trumpPlays = plays.filter(p2 => gameState._is_trump_tile(p2.tile));
      if(trumpPlays.length >= 2){
        trumpPlays.sort((a, b) => getTrumpRankNum(b.tile) - getTrumpRankNum(a.tile));
        const winner = trumpPlays[0]; // highest trump won
        for(let i = 1; i < trumpPlays.length; i++){
          const loser = trumpPlays[i];
          if(loser.seat === p) continue;
          const rank = getTrumpRankNum(loser.tile);
          if(rank >= 2){
            // Check: was this the highest or near-highest non-double trump at the time?
            // Compare against all trump tiles (non-doubles only, excluding the winner)
            const nonDoubleRanks = allTrumpTiles
              .filter(t => t[0] !== t[1])
              .map(t => getTrumpRankNum(t))
              .sort((a,b) => b - a);
            const topRank = nonDoubleRanks.length > 0 ? nonDoubleRanks[0] : 0;
            let confidence;
            if(rank >= topRank){
              confidence = 0.9; // played the highest possible non-double trump — almost certainly forced
            } else if(rank >= topRank * 0.7){
              confidence = 0.7; // very high trump
            } else {
              confidence = 0.5; // mid-range
            }
            trumpVoidLikely[loser.seat] = Math.min(1, (trumpVoidLikely[loser.seat] || 0) + confidence);
          }
        }
      }""",
    """      // Inferred trump void: player played high trump on a losing trick
      // = they were forced to play it (probably their only/last trump)
      // ENHANCED: "Effective top rank" — when multiple players play trump in the
      // same trick, each player's rank is evaluated against what was AVAILABLE
      // to them (excluding ranks played by OTHER seats in the same trick).
      // This way if opponents play 7-6, 7-5, 7-4, all three get ~90% void
      // confidence because each played their effective highest.
      const trumpPlays = plays.filter(p2 => gameState._is_trump_tile(p2.tile));
      if(trumpPlays.length >= 2){
        trumpPlays.sort((a, b) => getTrumpRankNum(b.tile) - getTrumpRankNum(a.tile));
        const winner = trumpPlays[0]; // highest trump won

        // Collect all non-double trump ranks played in this trick (for exclusion)
        const trickTrumpRanks = trumpPlays
          .filter(tp => tp.tile[0] !== tp.tile[1])
          .map(tp => getTrumpRankNum(tp.tile));

        for(let i = 1; i < trumpPlays.length; i++){
          const loser = trumpPlays[i];
          if(loser.seat === p) continue;
          const rank = getTrumpRankNum(loser.tile);
          if(rank >= 2){
            // Effective top rank: global non-double ranks MINUS ranks played by
            // OTHER seats in this same trick (they weren't available to this player)
            const otherTrickRanks = trumpPlays
              .filter(tp => tp.seat !== loser.seat && tp.tile[0] !== tp.tile[1])
              .map(tp => getTrumpRankNum(tp.tile));
            const availableRanks = allTrumpTiles
              .filter(t => t[0] !== t[1])
              .map(t => getTrumpRankNum(t))
              .filter(r => !otherTrickRanks.includes(r))
              .sort((a,b) => b - a);
            const effectiveTopRank = availableRanks.length > 0 ? availableRanks[0] : 0;
            let confidence;
            if(rank >= effectiveTopRank){
              confidence = 0.9; // played the highest AVAILABLE non-double trump
            } else if(effectiveTopRank > 0 && rank >= effectiveTopRank * 0.7){
              confidence = 0.7; // very high relative to available
            } else {
              confidence = 0.5; // mid-range
            }
            trumpVoidLikely[loser.seat] = Math.min(1, (trumpVoidLikely[loser.seat] || 0) + confidence);
          }
        }
      }""")


# ===========================================================================
# PATCH 3: Retroactive cross-trick void analysis
# After scanning all tricks individually, do a second pass:
# If we now know (from later tricks) that a partner held a higher trump during
# an earlier trick, then an opponent who played a high trump in that earlier
# trick was definitely playing their highest — upgrade their void confidence.
# ===========================================================================

# Insert the retroactive analysis AFTER the completed tricks loop (after the closing `}` of the for-team loop)
# and BEFORE the trump control detection section.

patch("P3: Retroactive cross-trick void analysis",
    """  // ═══════════════════════════════════════════════════════════════════
  //  TRUMP CONTROL DETECTION
  // ═══════════════════════════════════════════════════════════════════
  // We have trump control if ALL opponents are void in trump (confirmed or highly likely)
  let opponentsVoidInTrump = true;""",
    """  // ═══════════════════════════════════════════════════════════════════
  //  RETROACTIVE CROSS-TRICK VOID ANALYSIS
  // ═══════════════════════════════════════════════════════════════════
  // After scanning all tricks, re-evaluate earlier tricks using information
  // from later tricks. If a partner revealed a high trump in trick N, and an
  // opponent played a lower trump in trick M (M < N), the opponent couldn't
  // have had the partner's higher trump → their play was their actual highest.
  //
  // Build a timeline of when each seat revealed trump tiles.
  {
    const trumpReveals = {}; // seat → [{rank, trickIdx}]
    let retroTrickIdx = 0;
    for(let team = 0; team < 2; team++){
      for(const record of (gameState.tricks_team[team] || [])){
        for(let seat = 0; seat < record.length; seat++){
          const t = record[seat];
          if(!t || !gameState._is_trump_tile(t)) continue;
          if(!trumpReveals[seat]) trumpReveals[seat] = [];
          trumpReveals[seat].push({ rank: getTrumpRankNum(t), trickIdx: retroTrickIdx, tile: t });
        }
        retroTrickIdx++;
      }
    }

    // For each opponent's trump play, check if higher trumps were later revealed
    // to belong to OTHER players (partners or different opponents).
    // If so, the opponent's play was genuinely their highest → upgrade confidence.
    for(let s = 0; s < gameState.player_count; s++){
      if(s === p) continue;
      if(s % 2 === myTeam) continue; // only analyze opponents
      if(trumpVoidConfirmed[s]) continue; // already confirmed void
      const plays = trumpReveals[s] || [];
      for(const play of plays){
        // Find all trump reveals from OTHER players that happened in LATER tricks
        // and had HIGHER rank than this play
        let higherRevealedByOthers = false;
        for(let otherSeat = 0; otherSeat < gameState.player_count; otherSeat++){
          if(otherSeat === s) continue; // skip same player
          if(otherSeat === p) continue; // skip us (we know our own hand)
          const otherPlays = trumpReveals[otherSeat] || [];
          for(const op of otherPlays){
            if(op.rank > play.rank){
              // Someone else had a higher trump. Did they play it AFTER this trick?
              // If yes, the opponent couldn't have known about it, but WE now know
              // that this higher trump was NOT available to the opponent.
              // Actually, the key insight: if another player HELD a higher trump
              // during this opponent's trick, the opponent couldn't have had it.
              // The other player revealed it at some point (same trick or later).
              higherRevealedByOthers = true;
              break;
            }
          }
          if(higherRevealedByOthers) break;
        }
        if(higherRevealedByOthers){
          // This opponent played a trump that was NOT the global highest,
          // but we now know the global highest was held by someone else.
          // This means the opponent's play was their actual best → upgrade confidence.
          const currentConf = trumpVoidLikely[s] || 0;
          if(currentConf < 0.9){
            trumpVoidLikely[s] = Math.min(1, Math.max(currentConf, 0.85));
          }
        }
      }
    }
  }

  // ═══════════════════════════════════════════════════════════════════
  //  TRUMP CONTROL DETECTION
  // ═══════════════════════════════════════════════════════════════════
  // We have trump control if ALL opponents are void in trump (confirmed or highly likely)
  let opponentsVoidInTrump = true;""")


# ===========================================================================
# PATCH 4: Add HINT_MODE variable next to PASS_AND_PLAY_MODE
# ===========================================================================

patch("P4: Add HINT_MODE variable",
    """let PASS_AND_PLAY_MODE = false;""",
    """let PASS_AND_PLAY_MODE = false;
let HINT_MODE = false;""")


# ===========================================================================
# PATCH 5: Add CSS for hint shadow (white glow instead of dark shadow)
# ===========================================================================

patch("P5: Add CSS for hint shadow",
    """.dominoShadow .shadowShape{
    width:100%; height:100%;
    border-radius: var(--r);
    background: rgba(0,0,0,0.28);
    filter: blur(11px);
    transform: translateY(10px);
  }""",
    """.dominoShadow .shadowShape{
    width:100%; height:100%;
    border-radius: var(--r);
    background: rgba(0,0,0,0.28);
    filter: blur(11px);
    transform: translateY(10px);
  }
  .dominoShadow.hintGlow .shadowShape{
    background: rgba(255,255,255,0.75);
    filter: blur(14px);
    transform: translateY(0px);
  }""")


# ===========================================================================
# PATCH 6: Add Hint toggle to settings menu (after Pass & Play)
# ===========================================================================

patch("P6: Add Hint toggle to settings menu",
    """<div class="settingsItem" id="menuPassPlay">Pass & Play: OFF</div>""",
    """<div class="settingsItem" id="menuPassPlay">Pass & Play: OFF</div>
  <div class="settingsItem" id="menuHint">Hint: OFF</div>""")


# ===========================================================================
# PATCH 7: Add Hint toggle event listener (after Pass & Play listener)
# ===========================================================================

patch("P7: Add Hint toggle event listener",
    """document.getElementById('menuPassPlay').addEventListener('click', () => {
  PASS_AND_PLAY_MODE = !PASS_AND_PLAY_MODE;
  document.getElementById('menuPassPlay').textContent = `Pass & Play: ${PASS_AND_PLAY_MODE ? 'ON' : 'OFF'}`;
  document.getElementById('settingsMenu').classList.remove('open');
});""",
    """document.getElementById('menuPassPlay').addEventListener('click', () => {
  PASS_AND_PLAY_MODE = !PASS_AND_PLAY_MODE;
  document.getElementById('menuPassPlay').textContent = `Pass & Play: ${PASS_AND_PLAY_MODE ? 'ON' : 'OFF'}`;
  document.getElementById('settingsMenu').classList.remove('open');
});

document.getElementById('menuHint').addEventListener('click', () => {
  HINT_MODE = !HINT_MODE;
  document.getElementById('menuHint').textContent = `Hint: ${HINT_MODE ? 'ON' : 'OFF'}`;
  document.getElementById('settingsMenu').classList.remove('open');
  // If hint was just enabled and it's player's turn, show hint immediately
  if(HINT_MODE && waitingForPlayer1 && session.phase === PHASE_PLAYING && session.game.current_player === 0){
    showHint();
  } else if(!HINT_MODE){
    clearHint();
  }
});""")


# ===========================================================================
# PATCH 8: Add showHint() and clearHint() functions
# Insert after updatePlayer1ValidStates function
# ===========================================================================

patch("P8: Add showHint and clearHint functions",
    """// Process AI bid for a seat
function processAIBid(seat) {""",
    """// ═══════════════════════════════════════════════════════════════════
//  HINT SYSTEM — highlight AI-recommended domino with white shadow
// ═══════════════════════════════════════════════════════════════════
function showHint(){
  clearHint(); // clear any previous hint
  if(!HINT_MODE) return;
  if(session.phase !== PHASE_PLAYING) return;
  if(session.game.current_player !== 0) return;

  try {
    const aiRec = choose_tile_ai(session.game, 0, session.contract, true, session.current_bid);
    if(!aiRec || !aiRec.tile) return;

    const hintTile = aiRec.tile;
    const p1Sprites = sprites[0] || [];

    for(const data of p1Sprites){
      if(!data || !data.sprite || !data.tile) continue;
      if((data.tile[0] === hintTile[0] && data.tile[1] === hintTile[1]) ||
         (data.tile[0] === hintTile[1] && data.tile[1] === hintTile[0])){
        // Found the matching sprite — apply white glow to its shadow
        if(data.sprite._shadow){
          data.sprite._shadow.classList.add('hintGlow');
        }
        break;
      }
    }
  } catch(e) {
    console.log("Hint error:", e);
  }
}

function clearHint(){
  const p1Sprites = sprites[0] || [];
  for(const data of p1Sprites){
    if(data && data.sprite && data.sprite._shadow){
      data.sprite._shadow.classList.remove('hintGlow');
    }
  }
}

// Process AI bid for a seat
function processAIBid(seat) {""")


# ===========================================================================
# PATCH 9: Call showHint() when it's P1's turn (initial hand start)
# ===========================================================================

patch("P9: Show hint at initial hand start",
    """  // Start play
  if(session.game.current_player === 0){
    waitingForPlayer1 = true;
    enablePlayer1Clicks();
    updatePlayer1ValidStates();
  } else {""",
    """  // Start play
  if(session.game.current_player === 0){
    waitingForPlayer1 = true;
    enablePlayer1Clicks();
    updatePlayer1ValidStates();
    showHint();
  } else {""")


# ===========================================================================
# PATCH 10: Call showHint() when AI loop returns to P1
# ===========================================================================

patch("P10: Show hint when AI loop returns to P1",
    """  if(session.phase === PHASE_PLAYING && session.game.current_player === 0){
    waitingForPlayer1 = true;
    enablePlayer1Clicks();
    updatePlayer1ValidStates();
    setStatus(`Trick ${session.game.trick_number + 1} - Click a domino to play`);
  }""",
    """  if(session.phase === PHASE_PLAYING && session.game.current_player === 0){
    waitingForPlayer1 = true;
    enablePlayer1Clicks();
    updatePlayer1ValidStates();
    showHint();
    setStatus(`Trick ${session.game.trick_number + 1} - Click a domino to play`);
  }""")


# ===========================================================================
# PATCH 11: Clear hint when P1 clicks a domino
# ===========================================================================

patch("P11: Clear hint on P1 click",
    """  isAnimating = true;
  waitingForPlayer1 = false;
  disablePlayer1Clicks();

  setStatus('You play...');""",
    """  isAnimating = true;
  waitingForPlayer1 = false;
  disablePlayer1Clicks();
  clearHint();

  setStatus('You play...');""")


# ===========================================================================
# PATCH 12: Also show hint after resuming a saved game
# Search for the resume game logic that enables P1 clicks
# ===========================================================================

# Check if there's a resume path that also enables P1:
# The patch at 4190 (initial hand start) covers the main path.
# The patch at 6631 (AI loop return) covers mid-hand.
# The loadFromState function at ~6398 also checks:

patch("P12: Show hint on game state restore",
    """  // Update player hand clickability
  if(phase === PHASE_PLAYING && session.game.current_player === 0){
    waitingForPlayer1 = true;
    enablePlayer1Clicks();
    updatePlayer1ValidStates();
  } else {""",
    """  // Update player hand clickability
  if(phase === PHASE_PLAYING && session.game.current_player === 0){
    waitingForPlayer1 = true;
    enablePlayer1Clicks();
    updatePlayer1ValidStates();
    showHint();
  } else {""")


# ===========================================================================
# Write output
# ===========================================================================

with open(DST, "w", encoding="utf-8") as f:
    f.write(code)

print(f"\nDone — {patches_applied} patches applied → {DST}")
print(f"Output size: {len(code):,} bytes")
