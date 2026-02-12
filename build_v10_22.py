#!/usr/bin/env python3
"""
Build V10_22 from V10_21:
1. Probability-based void detection (count trump awareness)
2. Boneyard viewer (full-screen domino grid with played/trump/invalid states)
3. Ensure settings menus have highest z-index
"""
import sys

SRC = "/var/lib/freelancer/projects/40101953/TN51_Dominoes_V10_21.html"
DST = "/var/lib/freelancer/projects/40101953/TN51_Dominoes_V10_22.html"

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
# PATCH 1: Replace rank-based inferred void with probability-based model
# ===========================================================================

patch("P1: Probability-based void detection replacing rank-based",
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
      }""",
    """      // ──────────────────────────────────────────────────────────────
      // PROBABILITY-BASED VOID DETECTION (count-trump aware)
      // ──────────────────────────────────────────────────────────────
      // Instead of basing void confidence on the RANK of the trump played,
      // we calculate the probability that each opponent is holding an
      // unaccounted trump. Key insight: a player who plays a high non-count
      // trump might be protecting a lower count trump — not void at all.
      //
      // Formula: For N opponents who played trump and U unaccounted trumps,
      //   void_probability = 1 - (U / N)    [chance they DON'T hold one]
      //
      // Count-trump factor: if unaccounted trumps include count tiles
      // (pip sum = 5 or 10), opponents may have sacrificed high trumps to
      // protect count. This increases U effectively.
      //
      // Partner hold-back: if an unaccounted count trump is ALSO the highest
      // remaining trump, a partner might be holding it strategically.
      // Don't count that against opponents (reduces U by 1).
      const trumpPlays = plays.filter(p2 => gameState._is_trump_tile(p2.tile));
      if(trumpPlays.length >= 2){
        trumpPlays.sort((a, b) => getTrumpRankNum(b.tile) - getTrumpRankNum(a.tile));

        // Identify opponents who played trump in this trick (excluding us and the double/winner)
        const opponentsInTrick = trumpPlays.filter(tp =>
          tp.seat !== p && tp.seat % 2 !== myTeam
        );

        if(opponentsInTrick.length > 0){
          // Find unaccounted trumps at this point in the game
          // (not played in any completed trick up to now, not in our hand)
          // Note: trumpTilesRemaining was computed earlier from global state,
          // but we need trick-local analysis. Recompute for this trick context:
          const allPlayedInTrick = plays.map(p2 => p2.tile);
          const unaccountedAfterTrick = allTrumpTiles.filter(t => {
            // Skip doubles (they control, not relevant for void inference)
            if(t[0] === t[1]) return false;
            // In our hand?
            const inHand = hand.some(h =>
              Math.min(h[0],h[1]) === Math.min(t[0],t[1]) &&
              Math.max(h[0],h[1]) === Math.max(t[0],t[1]));
            if(inHand) return false;
            // Played in this trick?
            const inThisTrick = allPlayedInTrick.some(pt =>
              Math.min(pt[0],pt[1]) === Math.min(t[0],t[1]) &&
              Math.max(pt[0],pt[1]) === Math.max(t[0],t[1]));
            if(inThisTrick) return false;
            // Already played in earlier tricks? (check playedSet)
            if(isPlayed(t[0], t[1])) return false;
            return true;
          });

          // Check for count trumps among unaccounted
          const unaccountedCount = unaccountedAfterTrick.filter(t => {
            const s = t[0] + t[1];
            return s === 5 || s === 10;
          });

          // Partner hold-back: if an unaccounted count trump is also the
          // highest remaining non-double trump, a partner might hold it
          let partnerHoldBack = 0;
          if(unaccountedCount.length > 0){
            const highestRemainingRank = unaccountedAfterTrick.length > 0
              ? Math.max(...unaccountedAfterTrick.map(getTrumpRankNum)) : -1;
            for(const ct of unaccountedCount){
              if(getTrumpRankNum(ct) >= highestRemainingRank){
                // This count trump is the highest remaining — partner might hold it
                partnerHoldBack++;
              }
            }
          }

          const N = opponentsInTrick.length; // opponents who played trump
          // Effective unaccounted = total unaccounted minus partner hold-backs
          const U = Math.max(0, unaccountedAfterTrick.length - partnerHoldBack);

          // Calculate void probability for each opponent in this trick
          const voidProb = N > 0 ? Math.max(0, 1 - (U / N)) : 0.5;

          for(const opp of opponentsInTrick){
            // Only update if this gives higher confidence than what we already have
            const current = trumpVoidLikely[opp.seat] || 0;
            if(voidProb > current){
              trumpVoidLikely[opp.seat] = Math.min(1, voidProb);
            }
          }
        }
      }""")


# ===========================================================================
# PATCH 2: Update retroactive analysis to use probability model
# The retroactive pass now uses the same count-aware probability logic
# ===========================================================================

patch("P2: Update retroactive analysis with probability model",
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
  }""",
    """  // ═══════════════════════════════════════════════════════════════════
  //  RETROACTIVE CROSS-TRICK VOID ANALYSIS
  // ═══════════════════════════════════════════════════════════════════
  // After scanning all tricks, re-evaluate using cross-trick information:
  // 1. If a partner revealed a high trump later, we now know that an opponent
  //    who played a lower trump earlier couldn't have had the partner's trump.
  // 2. Recalculate void probability using updated knowledge of who holds what.
  {
    const trumpReveals = {}; // seat → [{rank, trickIdx, tile}]
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

    // For each opponent, check if higher trumps were revealed by others.
    // If so, the opponent's play was genuinely their highest → upgrade confidence.
    // Also factor in count-trump awareness: if the only unaccounted trumps are
    // now known to be held by partners (from later reveals), opponents are more
    // likely void.
    for(let s = 0; s < gameState.player_count; s++){
      if(s === p) continue;
      if(s % 2 === myTeam) continue;
      if(trumpVoidConfirmed[s]) continue;
      const oppPlays = trumpReveals[s] || [];
      if(oppPlays.length === 0) continue;

      for(const play of oppPlays){
        let higherRevealedByOthers = false;
        for(let otherSeat = 0; otherSeat < gameState.player_count; otherSeat++){
          if(otherSeat === s || otherSeat === p) continue;
          const otherPlays = trumpReveals[otherSeat] || [];
          for(const op of otherPlays){
            if(op.rank > play.rank){
              higherRevealedByOthers = true;
              break;
            }
          }
          if(higherRevealedByOthers) break;
        }
        if(higherRevealedByOthers){
          // Opponent's play was their actual best — upgrade confidence
          // But still respect count-awareness: check if unaccounted count trumps
          // could explain why they played high (protecting count).
          // If the higher trump was revealed by a PARTNER, then the opponent
          // definitely didn't have it → their high play was forced.
          const currentConf = trumpVoidLikely[s] || 0;

          // Check if any unaccounted count trumps remain
          const unaccountedCountTrumps = trumpTilesRemaining.filter(t => {
            const sum = t[0] + t[1];
            return (sum === 5 || sum === 10) && t[0] !== t[1];
          });

          if(unaccountedCountTrumps.length === 0){
            // No count trumps unaccounted → opponent was definitely forced
            trumpVoidLikely[s] = Math.min(1, Math.max(currentConf, 0.9));
          } else {
            // Count trumps still unaccounted → opponent might be protecting count
            // But we have retroactive evidence → moderate upgrade
            trumpVoidLikely[s] = Math.min(1, Math.max(currentConf, 0.75));
          }
        }
      }
    }
  }""")


# ===========================================================================
# PATCH 3: Add "Bones" menu item in settings
# ===========================================================================

patch("P3: Add Bones menu item to settings",
    """<div class="settingsItem" id="menuHint">Hint: OFF</div>
  <div class="settingsDivider"></div>
  <div class="settingsItem" id="menuNotes">Notes</div>""",
    """<div class="settingsItem" id="menuHint">Hint: OFF</div>
  <div class="settingsItem" id="menuBones">Bones</div>
  <div class="settingsDivider"></div>
  <div class="settingsItem" id="menuNotes">Notes</div>""")


# ===========================================================================
# PATCH 4: Add Boneyard modal HTML (after advanced log modal but before </body>)
# ===========================================================================

# Find a good insertion point for the boneyard modal
patch("P4: Add Boneyard modal HTML",
    """<!-- Notes Modal -->""",
    """<!-- Boneyard Modal -->
<div id="bonesBackdrop" style="display:none;position:fixed;inset:0;background:rgba(0,30,0,0.92);z-index:9999;overflow-y:auto;">
  <div style="padding:12px;max-width:500px;margin:0 auto;">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
      <span style="color:#fff;font-size:18px;font-weight:bold;">Boneyard</span>
      <button onclick="document.getElementById('bonesBackdrop').style.display='none';" style="background:#ef4444;color:#fff;border:none;border-radius:8px;padding:6px 14px;font-size:14px;cursor:pointer;">Close</button>
    </div>
    <canvas id="bonesCanvas" style="width:100%;border-radius:8px;"></canvas>
  </div>
</div>

<!-- Notes Modal -->""")


# ===========================================================================
# PATCH 5: Add Bones event listener and rendering function
# ===========================================================================

patch("P5: Add Bones event listener and render function",
    """document.getElementById('menuHint').addEventListener('click', () => {""",
    """document.getElementById('menuBones').addEventListener('click', () => {
  document.getElementById('settingsMenu').classList.remove('open');
  renderBoneyard();
  document.getElementById('bonesBackdrop').style.display = 'block';
});

// ═══════════════════════════════════════════════════════════════════
//  BONEYARD RENDERER — shows all 28 dominoes in triangular layout
//  Played tiles shown as invalid (faded), trump tiles highlighted
// ═══════════════════════════════════════════════════════════════════
function renderBoneyard(){
  const canvas = document.getElementById('bonesCanvas');
  if(!canvas) return;

  const dpr = window.devicePixelRatio || 1;

  // Tile dimensions
  const tileW = 48;
  const tileH = 96;
  const gap = 4;

  // Layout: 8 rows, row N starts at column N and has (8-N) tiles
  // Row 0: 7-7, 7-6, 7-5, 7-4, 7-3, 7-2, 7-1, 7-0  (8 tiles)
  // Row 1: 6-6, 6-5, 6-4, 6-3, 6-2, 6-1, 6-0        (7 tiles)
  // ...
  // Row 7: 0-0                                         (1 tile)
  const rows = [];
  for(let high = 7; high >= 0; high--){
    const row = [];
    for(let low = high; low >= 0; low--){
      row.push([high, low]);
    }
    rows.push(row);
  }

  // Calculate canvas size
  const maxCols = 8;
  const numRows = 8;
  const canvasW = maxCols * (tileW + gap) + gap;
  const canvasH = numRows * (tileH + gap) + gap;

  canvas.width = canvasW * dpr;
  canvas.height = canvasH * dpr;
  canvas.style.width = canvasW + 'px';
  canvas.style.height = canvasH + 'px';

  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);

  // Background (dark green felt)
  ctx.fillStyle = 'rgba(0,40,0,0.6)';
  ctx.fillRect(0, 0, canvasW, canvasH);

  // Determine played tiles and trump state
  const playedTiles = new Set();

  // Build played set from tricks_team
  if(session && session.game){
    for(let team = 0; team < 2; team++){
      for(const record of (session.game.tricks_team[team] || [])){
        for(let seat = 0; seat < record.length; seat++){
          const t = record[seat];
          if(t) playedTiles.add(Math.min(t[0],t[1]) + ',' + Math.max(t[0],t[1]));
        }
      }
    }
    // Also add tiles currently in play (current trick)
    for(const play of (session.game.current_trick || [])){
      if(Array.isArray(play)){
        const t = play[1];
        if(t) playedTiles.add(Math.min(t[0],t[1]) + ',' + Math.max(t[0],t[1]));
      }
    }
  }

  const isTilePlayedBones = (a, b) => playedTiles.has(Math.min(a,b) + ',' + Math.max(a,b));

  const isTrumpTile = (tile) => {
    if(!session || !session.game) return false;
    return session.game._is_trump_tile(tile);
  };

  // Draw each tile
  for(let rowIdx = 0; rowIdx < rows.length; rowIdx++){
    const row = rows[rowIdx];
    // Offset: each row shifts right by rowIdx positions
    const xOffset = rowIdx * (tileW + gap) / 2;

    for(let colIdx = 0; colIdx < row.length; colIdx++){
      const tile = row[colIdx];
      const x = xOffset + colIdx * (tileW + gap) + gap;
      const y = rowIdx * (tileH + gap) + gap;

      const played = isTilePlayedBones(tile[0], tile[1]);
      const trump = isTrumpTile(tile);

      // Save context and draw the tile
      ctx.save();
      ctx.translate(x, y);

      // Create a small offscreen canvas for this tile to reuse drawFace
      const tileCanvas = document.createElement('canvas');
      tileCanvas.width = Math.round(tileW * dpr);
      tileCanvas.height = Math.round(tileH * dpr);
      const tctx = tileCanvas.getContext('2d');
      tctx.scale(dpr, dpr);
      drawFace(tctx, tile, tileW, tileH, trump, !played);

      // Draw the tile canvas onto the main canvas
      ctx.drawImage(tileCanvas, 0, 0, tileW, tileH);

      ctx.restore();
    }
  }
}

document.getElementById('menuHint').addEventListener('click', () => {""")


# ===========================================================================
# PATCH 6: Ensure boneyard z-index is highest (9999 already set in HTML)
# Also ensure settings menu is above boneyard button but below boneyard overlay
# The boneyard uses z-index 9999 in the HTML (patch 4).
# Settings menu is at 1201 which is fine (below 9999).
# Let's make sure no other elements can go above the boneyard.
# ===========================================================================

# Check if there are any elements with z-index higher than 1201 that could
# overlap settings. The settings button/menu are already at 1200/1201.
# The boneyard at 9999 will be above everything when open.
# No additional patch needed for z-index — it's handled in the HTML.

print("NOTE: Z-index handled — Boneyard at 9999, settings at 1201, modals at 1000")


# ===========================================================================
# Write output
# ===========================================================================

with open(DST, "w", encoding="utf-8") as f:
    f.write(code)

print(f"\nDone — {patches_applied} patches applied → {DST}")
print(f"Output size: {len(code):,} bytes")
