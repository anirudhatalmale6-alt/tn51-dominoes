#!/usr/bin/env python3
"""Build V10_17 — Comprehensive AI + Log Fixes
1. Better inferred trump void scoring (rank-based, not flat 50%)
2. Fix false void-in-blanks on trump-led completed tricks
3. Fix seat vs player label mismatch in void tracking debug
4. Fix 'Only legal move' undefined trump fields
5. Fix trick point display (use game engine scoring)
6. Add end-of-trick void/state summary in advanced log
7. Partner-holds-remaining-trump detection (treat as trump control)
"""

import sys, os

SRC = "/var/lib/freelancer/projects/40101953/TN51_Dominoes_V10_16.html"
DST = "/var/lib/freelancer/projects/40101953/TN51_Dominoes_V10_17.html"

with open(SRC, "r", encoding="utf-8") as f:
    html = f.read()

patches = 0

# ============================================================
# PATCH 1: Better inferred trump void scoring
# Current: flat +0.5 for any losing trump with rank >= 3
# New: scale by how high the trump was vs what's remaining
# If they played the HIGHEST remaining non-double trump on a
# losing trick, that's ~90%. If mid-range, ~60%.
# ============================================================

old_inferred = """      // Inferred trump void: player played high trump on a losing trick
      // = they were forced to play it (probably their only/last trump)
      const trumpPlays = plays.filter(p2 => gameState._is_trump_tile(p2.tile));
      if(trumpPlays.length >= 2){
        // Sort by trump rank descending
        trumpPlays.sort((a, b) => getTrumpRankNum(b.tile) - getTrumpRankNum(a.tile));
        const winner = trumpPlays[0]; // highest trump won
        // Players who played high trump but lost — likely forced
        for(let i = 1; i < trumpPlays.length; i++){
          const loser = trumpPlays[i];
          if(loser.seat === p) continue;
          const rank = getTrumpRankNum(loser.tile);
          // If they played a fairly high trump (rank > 50 means non-double with pip > 4
          // in PIP mode, or a high double in DOUBLES mode) and still lost, likely forced
          if(rank >= 3){
            // Increase likelihood they're void (not confirmed, but likely)
            trumpVoidLikely[loser.seat] = Math.min(1, (trumpVoidLikely[loser.seat] || 0) + 0.5);
          }
        }
      }"""

new_inferred = """      // Inferred trump void: player played high trump on a losing trick
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
      }"""

if old_inferred not in html:
    print("ERROR: Could not find inferred void block")
    sys.exit(1)
html = html.replace(old_inferred, new_inferred, 1)
patches += 1
print(f"PATCH {patches}: Better inferred trump void scoring")

# ============================================================
# PATCH 2: Fix false void-in-blanks on trump-led tricks
# Skip suit-void analysis when most tiles in a completed trick are trump
# (heuristic: if more than half the tiles are trump, it was trump-led)
# ============================================================

old_false_void = """      if(likelyLedPip !== null){
        for(const p2 of plays){
          const t = p2.tile;
          const seat = p2.seat;
          if(seat === p) continue;
          const hasSuit = t[0] === likelyLedPip || t[1] === likelyLedPip;
          const isTrump = gameState._is_trump_tile(t);
          if(!hasSuit && !isTrump){
            voidIn[seat].add(likelyLedPip);
            trumpVoidConfirmed[seat] = true;
          } else if(!hasSuit && isTrump){
            voidIn[seat].add(likelyLedPip);
          }
        }
      }"""

new_false_void = """      // Skip suit-void analysis if this was a trump-led trick
      // (most tiles are trump → the non-trump tiles are dumps, not suit indicators)
      const trumpCount = plays.filter(p2 => gameState._is_trump_tile(p2.tile)).length;
      const wasTrumpLedTrick = trumpCount > plays.length / 2;

      if(likelyLedPip !== null && !wasTrumpLedTrick){
        for(const p2 of plays){
          const t = p2.tile;
          const seat = p2.seat;
          if(seat === p) continue;
          const hasSuit = t[0] === likelyLedPip || t[1] === likelyLedPip;
          const isTrump = gameState._is_trump_tile(t);
          if(!hasSuit && !isTrump){
            voidIn[seat].add(likelyLedPip);
            trumpVoidConfirmed[seat] = true;
          } else if(!hasSuit && isTrump){
            voidIn[seat].add(likelyLedPip);
          }
        }
      }
      // For trump-led tricks: detect trump voids (players who played non-trump)
      if(wasTrumpLedTrick){
        for(const p2 of plays){
          const t = p2.tile;
          const seat = p2.seat;
          if(seat === p) continue;
          if(!gameState._is_trump_tile(t)){
            trumpVoidConfirmed[seat] = true;
          }
        }
      }"""

if old_false_void not in html:
    print("ERROR: Could not find false void block")
    sys.exit(1)
html = html.replace(old_false_void, new_false_void, 1)
patches += 1
print(f"PATCH {patches}: Fixed false void-in-blanks on trump-led tricks")

# ============================================================
# PATCH 3: Fix seat vs player label mismatch in void tracking debug
# Change _dbg.voidTracking['P'+s] to use seatToPlayer
# ============================================================

old_void_debug = """    _dbg.voidTracking = {};
    for(let s = 0; s < gameState.player_count; s++){
      if(s === p) continue;
      const voids = Array.from(voidIn[s]);
      if(voids.length > 0 || trumpVoidConfirmed[s] || trumpVoidLikely[s] > 0){
        _dbg.voidTracking['P'+s] = {
          team: s % 2 === myTeam ? 'ours' : 'opp',
          voidSuits: voids,
          trumpVoidConfirmed: trumpVoidConfirmed[s],
          trumpVoidLikely: trumpVoidLikely[s]
        };
      }
    }"""

# We need seatToPlayer in the AI function. It's a global function, so we can call it.
# But wait — seatToPlayer is defined AFTER the AI function. Let's check if it's accessible.
# Actually, JS hoisting: function declarations are hoisted, but seatToPlayer is defined
# after the AI function. Since choose_tile_ai is called at runtime (not parse time),
# seatToPlayer will be available. Good.

new_void_debug = """    _dbg.voidTracking = {};
    for(let s = 0; s < gameState.player_count; s++){
      if(s === p) continue;
      const voids = Array.from(voidIn[s]);
      if(voids.length > 0 || trumpVoidConfirmed[s] || trumpVoidLikely[s] > 0){
        const pLabel = (typeof seatToPlayer === 'function') ? ('P'+seatToPlayer(s)) : ('P'+(s+1));
        _dbg.voidTracking[pLabel] = {
          team: s % 2 === myTeam ? 'ours' : 'opp',
          voidSuits: voids,
          trumpVoidConfirmed: trumpVoidConfirmed[s],
          trumpVoidLikely: trumpVoidLikely[s]
        };
      }
    }"""

if old_void_debug not in html:
    print("ERROR: Could not find void debug block")
    sys.exit(1)
html = html.replace(old_void_debug, new_void_debug, 1)
patches += 1
print(f"PATCH {patches}: Fixed seat vs player labels in void tracking")

# ============================================================
# PATCH 4: Fix 'Only legal move' undefined trump fields
# The early exit debug captures trumpMode and trumpSuit but doesn't
# compute trumpsInHand etc. Let's add basic trump computation.
# ============================================================

old_early_dbg = """  // Populate basic debug info BEFORE early returns so "Only legal move" still shows context
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
  }"""

new_early_dbg = """  // Populate basic debug info BEFORE early returns so "Only legal move" still shows context
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
    // Basic trump info for early exit
    const _ts = gameState.trump_suit;
    const _tm = gameState.trump_mode;
    const _earlyTrumpsInHand = hand.filter(t => gameState._is_trump_tile(t));
    _dbg.trumpsInHand = _earlyTrumpsInHand.map(t => t[0]+'-'+t[1]);
    _dbg.trumpsRemaining = []; // can't compute without full memory scan
    _dbg.iHaveHighestTrump = '(n/a - only legal move)';
    _dbg.myHighestTrumpRank = '(n/a)';
    _dbg.highestRemainingTrumpRank = '(n/a)';
  }"""

if old_early_dbg not in html:
    print("ERROR: Could not find early debug block")
    sys.exit(1)
html = html.replace(old_early_dbg, new_early_dbg, 1)
patches += 1
print(f"PATCH {patches}: Fixed 'Only legal move' undefined trump fields")

# ============================================================
# PATCH 5: Fix trick point display in log
# Replace the raw pip-sum formula with the game engine's scoring
# ============================================================

old_points = """  // Log trick end with points scored this trick
  const pointsThisTrick = playedThisTrick.reduce((sum, p) => {
    return sum + (p.tile[0] === p.tile[1] ? 0 : (p.tile[0] + p.tile[1]));
  }, 0);
  logTrickEnd(winnerSeat, pointsThisTrick);"""

new_points = """  // Log trick end with points scored this trick
  // Use the same formula as the game engine: 1 base + 5 for pip sum=5, + 10 for pip sum=10
  let pointsThisTrick = 1; // base point per trick
  for(const p of playedThisTrick){
    if(!p.tile) continue;
    const s = p.tile[0] + p.tile[1];
    if(s === 5) pointsThisTrick += 5;
    else if(s === 10) pointsThisTrick += 10;
  }
  logTrickEnd(winnerSeat, pointsThisTrick);"""

if old_points not in html:
    print("ERROR: Could not find pointsThisTrick formula")
    sys.exit(1)
html = html.replace(old_points, new_points, 1)
patches += 1
print(f"PATCH {patches}: Fixed trick point display to use game engine scoring")

# ============================================================
# PATCH 6: Add end-of-trick void/state summary to log
# Modify logTrickEnd to capture current void/trump state
# and modify formatAdvancedLog to display it
# ============================================================

# First, modify logTrickEnd to accept and store extra state info
old_logTrickEnd = """function logTrickEnd(winnerSeat, points){
  const playsString = currentTrickPlays.map(p => `P${seatToPlayer(p.seat)}:${p.tilePlayed}`).join(' → ');

  const entry = {
    type: "TRICK_END",
    handId: handNumber,
    trickId: trickNumber,
    winnerSeat: winnerSeat,
    winnerTeam: winnerSeat % 2 === 0 ? 1 : 2,
    pointsInTrick: points,
    playsString: playsString,
    timestamp: new Date().toISOString()
  };

  gameLog.push(entry);
  trickNumber++;
  currentTrickPlays = [];
  saveGameLog();
}"""

new_logTrickEnd = """function logTrickEnd(winnerSeat, points){
  const playsString = currentTrickPlays.map(p => `P${seatToPlayer(p.seat)}:${p.tilePlayed}`).join(' → ');

  // Capture end-of-trick state summary by running AI analysis from seat 0's perspective
  // This gives us the void tracking, trump control, and bid safety state AFTER this trick
  let trickEndState = null;
  try {
    // Run AI from seat 0 just to get the debug info (won't actually play)
    const debugRec = choose_tile_ai(session.game, 0, session.contract, true, session.current_bid);
    if(debugRec && debugRec.debugInfo){
      const d = debugRec.debugInfo;
      trickEndState = {
        teamScores: [session.game.team_points[0], session.game.team_points[1]],
        voidTracking: d.voidTracking || {},
        trumpControl: d.weHaveTrumpControl || false,
        opponentsVoidInTrump: d.opponentsVoidInTrump || false,
        partnersHaveTrump: d.partnersHaveTrump,
        trumpsRemaining: d.trumpsRemaining || [],
        bidSafety: d.bidSafety || null,
        trumpsInHand: d.trumpsInHand || []
      };
    }
  } catch(e) {
    // If AI fails (e.g., hand is over), just skip
  }

  const entry = {
    type: "TRICK_END",
    handId: handNumber,
    trickId: trickNumber,
    winnerSeat: winnerSeat,
    winnerTeam: winnerSeat % 2 === 0 ? 1 : 2,
    pointsInTrick: points,
    playsString: playsString,
    trickEndState: trickEndState,
    timestamp: new Date().toISOString()
  };

  gameLog.push(entry);
  trickNumber++;
  currentTrickPlays = [];
  saveGameLog();
}"""

if old_logTrickEnd not in html:
    print("ERROR: Could not find logTrickEnd function")
    sys.exit(1)
html = html.replace(old_logTrickEnd, new_logTrickEnd, 1)
patches += 1
print(f"PATCH {patches}: Enhanced logTrickEnd with end-of-trick state summary")

# Now update formatAdvancedLog to display the trick-end state
# There are TWO TRICK_END renderers: one in formatGameLog (line ~7100) and one in formatAdvancedLog (line ~7308)
# We only update the advanced log one.

old_adv_trick_end = """    else if(entry.type === "TRICK_END"){
      text += "  >> Winner: P" + seatToPlayer(entry.winnerSeat) + " (Team " + entry.winnerTeam + ") +" + entry.pointsInTrick + " pts\\n";
      text += "  >> " + entry.playsString + "\\n";
    }
    else if(entry.type === "HAND_END"){"""

new_adv_trick_end = """    else if(entry.type === "TRICK_END"){
      text += "  >> Winner: P" + seatToPlayer(entry.winnerSeat) + " (Team " + entry.winnerTeam + ") +" + entry.pointsInTrick + " pts\\n";
      text += "  >> " + entry.playsString + "\\n";

      // End-of-trick state summary
      const ts = entry.trickEndState;
      if(ts){
        text += "  ┌─── END OF TRICK STATE ───\\n";
        text += "  │ Scores: Team1=" + ts.teamScores[0] + " Team2=" + ts.teamScores[1] + "\\n";

        if(ts.bidSafety){
          const b = ts.bidSafety;
          text += "  │ Bid: " + b.currentBid + " | Need: " + b.pointsNeeded + " | ";
          if(b.bidIsSafe) text += "SAFE";
          else if(b.bidIsClose) text += "CLOSE!";
          else text += "still working";
          text += " | Tricks left: " + b.tricksLeft + "\\n";
        }

        if(ts.trumpsInHand && ts.trumpsInHand.length > 0){
          text += "  │ P1 trumps: [" + ts.trumpsInHand.join(", ") + "]\\n";
        }
        if(ts.trumpsRemaining && ts.trumpsRemaining.length > 0){
          text += "  │ Trumps still out: [" + ts.trumpsRemaining.join(", ") + "]\\n";
        } else {
          text += "  │ Trumps still out: none (all accounted for)\\n";
        }

        text += "  │ Trump control: " + (ts.trumpControl ? "YES" : "NO");
        text += " (opps void: " + ts.opponentsVoidInTrump;
        if(ts.partnersHaveTrump !== undefined) text += ", partners trump: " + ts.partnersHaveTrump;
        text += ")\\n";

        const vt = ts.voidTracking;
        if(vt && Object.keys(vt).length > 0){
          text += "  │ KNOWN VOIDS:\\n";
          for(const [seat, info] of Object.entries(vt)){
            text += "  │   " + seat + " (" + info.team + "):";
            if(info.voidSuits && info.voidSuits.length > 0) text += " void in suits [" + info.voidSuits.join(",") + "]";
            if(info.trumpVoidConfirmed) text += " | TRUMP VOID";
            else if(info.trumpVoidLikely > 0) text += " | trump void " + Math.round(info.trumpVoidLikely*100) + "%";
            text += "\\n";
          }
        } else {
          text += "  │ KNOWN VOIDS: none detected yet\\n";
        }
        text += "  └────────────────────────\\n";
      }
    }
    else if(entry.type === "HAND_END"){"""

if old_adv_trick_end not in html:
    print("ERROR: Could not find advanced log TRICK_END renderer")
    sys.exit(1)
html = html.replace(old_adv_trick_end, new_adv_trick_end, 1)
patches += 1
print(f"PATCH {patches}: Added end-of-trick state summary to advanced log")

# ============================================================
# PATCH 7: Partner-holds-remaining-trump detection
# If all remaining trumps (not in our hand) are held by partners
# (all opponents confirmed/likely void in trump), treat as trump control
# even if partners still have trump. The key insight: don't pull
# partner's trumps, play doubles instead.
# ============================================================

# The current trump control logic is:
#   weHaveTrumpControl = opponentsVoidInTrump && (trumpsInHand.length > 0 || partnersHaveTrump)
# This already does what we want IF opponentsVoidInTrump is correct.
# The issue is opponentsVoidInTrump threshold: trumpVoidLikely < 0.8 means not void.
# With our new 0.9 confidence for highest-trump plays, this should be better.
# But let's also add: if all remaining trumps NOT in our hand are accounted for
# (opponent confirmed void), then we have trump control regardless.

old_trump_control = """  // ═══════════════════════════════════════════════════════════════════
  //  TRUMP CONTROL DETECTION
  // ═══════════════════════════════════════════════════════════════════
  // We have trump control if ALL opponents are void in trump (confirmed or highly likely)
  let opponentsVoidInTrump = true;
  for(let s = 0; s < gameState.player_count; s++){
    if(s % 2 === myTeam) continue; // skip teammates
    if(!gameState.active_players.includes(s)) continue; // skip inactive
    if(!trumpVoidConfirmed[s] && trumpVoidLikely[s] < 0.8){
      opponentsVoidInTrump = false;
      break;
    }
  }

  // Also: if all trump tiles are accounted for (in our hand + played), opponents are void
  if(trumpTilesRemaining.length === 0 && trumpMode !== "NONE"){
    // All trumps are either played or in our hand — we have full trump control
    opponentsVoidInTrump = true;
  }

  // Partners have trump = check if any partners still have trump tiles
  let partnersHaveTrump = false;
  for(let s = 0; s < gameState.player_count; s++){
    if(s % 2 !== myTeam || s === p) continue;
    if(!trumpVoidConfirmed[s] && trumpVoidLikely[s] < 0.5){
      // Partner might still have trump
      partnersHaveTrump = true;
      break;
    }
  }

  const weHaveTrumpControl = opponentsVoidInTrump && (trumpsInHand.length > 0 || partnersHaveTrump);"""

new_trump_control = """  // ═══════════════════════════════════════════════════════════════════
  //  TRUMP CONTROL DETECTION
  // ═══════════════════════════════════════════════════════════════════
  // We have trump control if ALL opponents are void in trump (confirmed or highly likely)
  let opponentsVoidInTrump = true;
  for(let s = 0; s < gameState.player_count; s++){
    if(s % 2 === myTeam) continue; // skip teammates
    if(!gameState.active_players.includes(s)) continue; // skip inactive
    if(!trumpVoidConfirmed[s] && trumpVoidLikely[s] < 0.8){
      opponentsVoidInTrump = false;
      break;
    }
  }

  // Also: if all trump tiles are accounted for (in our hand + played), opponents are void
  if(trumpTilesRemaining.length === 0 && trumpMode !== "NONE"){
    // All trumps are either played or in our hand — we have full trump control
    opponentsVoidInTrump = true;
  }

  // Partners have trump = check if any partners still have trump tiles
  let partnersHaveTrump = false;
  for(let s = 0; s < gameState.player_count; s++){
    if(s % 2 !== myTeam || s === p) continue;
    if(!trumpVoidConfirmed[s] && trumpVoidLikely[s] < 0.5){
      // Partner might still have trump
      partnersHaveTrump = true;
      break;
    }
  }

  // ENHANCED: Even if trumpTilesRemaining > 0, if all opponents are confirmed/likely
  // void in trump, the remaining trumps must be held by partners.
  // Don't waste high trumps pulling partner trumps — treat as trump control.
  let partnersHoldRemainingTrumps = false;
  if(opponentsVoidInTrump && trumpTilesRemaining.length > 0){
    // All remaining trumps are held by partners
    partnersHoldRemainingTrumps = true;
  }

  const weHaveTrumpControl = opponentsVoidInTrump && (trumpsInHand.length > 0 || partnersHaveTrump);"""

if old_trump_control not in html:
    print("ERROR: Could not find trump control detection block")
    sys.exit(1)
html = html.replace(old_trump_control, new_trump_control, 1)
patches += 1
print(f"PATCH {patches}: Added partner-holds-remaining-trump detection")

# Now update the P2 lead logic: when leading with high trump (pulling), skip if
# remaining trumps are only with partners
old_p2_lead = """      // P2: Lead high trump IF we have the highest remaining
      // BUT respect last-trump protection
      if(otherTrumps.length > 0 && iHaveHighestTrump && !shouldSaveLastTrump){
        let bestIdx = otherTrumps[0], bestR = -1;
        for(const idx of otherTrumps){
          const r = getTrumpRankNum(hand[idx]);
          if(r > bestR){ bestR = r; bestIdx = idx; }
        }
        return makeResult(bestIdx, "Lead: high trump (pulling remaining trumps)");
      }"""

new_p2_lead = """      // P2: Lead high trump IF we have the highest remaining
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

if old_p2_lead not in html:
    print("ERROR: Could not find P2 lead trump block")
    sys.exit(1)
html = html.replace(old_p2_lead, new_p2_lead, 1)
patches += 1
print(f"PATCH {patches}: P2 lead skips pulling when only partners have trump")

# Also update P3 early trump aggression to skip when partners hold remaining trumps
old_p3_lead = """      // P3: Early game trump aggression — lead trump even without highest
      // if we have 2+ trumps, it's trick 0 or 1, and bid isn't safe yet
      if(otherTrumps.length >= 2 && trickNum <= 1 && !bidIsSafe){
        // Lead highest trump to force opponents' trumps out early
        let bestIdx = otherTrumps[0], bestR = -1;
        for(const idx of otherTrumps){
          const r = getTrumpRankNum(hand[idx]);
          if(r > bestR){ bestR = r; bestIdx = idx; }
        }
        return makeResult(bestIdx, "Lead: early trump (forcing opponent trumps)");
      }"""

new_p3_lead = """      // P3: Early game trump aggression — lead trump even without highest
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

if old_p3_lead not in html:
    print("ERROR: Could not find P3 early trump block")
    sys.exit(1)
html = html.replace(old_p3_lead, new_p3_lead, 1)
patches += 1
print(f"PATCH {patches}: P3 early aggression skips when only partners have trump")

# Add partnersHoldRemainingTrumps to debug output
old_trump_ctrl_dbg = """    _dbg.opponentsVoidInTrump = opponentsVoidInTrump;"""
new_trump_ctrl_dbg = """    _dbg.opponentsVoidInTrump = opponentsVoidInTrump;
    _dbg.partnersHoldRemainingTrumps = partnersHoldRemainingTrumps;"""

if old_trump_ctrl_dbg not in html:
    print("ERROR: Could not find trump control debug line")
    sys.exit(1)
html = html.replace(old_trump_ctrl_dbg, new_trump_ctrl_dbg, 1)
patches += 1
print(f"PATCH {patches}: Added partnersHoldRemainingTrumps to debug")

# Update the advanced log formatter to show this new field
old_ctrl_display = """        text += "    │ TRUMP CONTROL: " + (d.weHaveTrumpControl ? "YES ✓" : "NO");
        text += " (opps void: " + d.opponentsVoidInTrump + ", partners have trump: " + d.partnersHaveTrump + ")\\n";"""

new_ctrl_display = """        text += "    │ TRUMP CONTROL: " + (d.weHaveTrumpControl ? "YES ✓" : "NO");
        text += " (opps void: " + d.opponentsVoidInTrump + ", partners have trump: " + d.partnersHaveTrump;
        if(d.partnersHoldRemainingTrumps) text += ", PARTNERS HOLD ALL REMAINING TRUMPS";
        text += ")\\n";"""

if old_ctrl_display not in html:
    print("ERROR: Could not find trump control display in formatter")
    sys.exit(1)
html = html.replace(old_ctrl_display, new_ctrl_display, 1)
patches += 1
print(f"PATCH {patches}: Updated formatter to show partnersHoldRemainingTrumps")

# ============================================================
# Verification
# ============================================================
checks = [
    ("partnersHoldRemainingTrumps", "Partner trump detection"),
    ("wasTrumpLedTrick", "Trump-led trick detection"),
    ("confidence = 0.9", "90% confidence for highest trump"),
    ("seatToPlayer(s))", "Player labels in void tracking"),
    ("_earlyTrumpsInHand", "Early exit trump info"),
    ("let pointsThisTrick = 1", "Fixed points formula"),
    ("trickEndState", "End-of-trick state"),
    ("END OF TRICK STATE", "End-of-trick display"),
    ("PARTNERS HOLD ALL REMAINING", "Partner trump display"),
]

all_ok = True
for pattern, desc in checks:
    if pattern not in html:
        print(f"  ✗ Missing: {desc}")
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
print(f"\nPatches applied: {patches}")
print(f"Source: {src_size:,} bytes")
print(f"Output: {dst_size:,} bytes")
print(f"Delta:  {dst_size - src_size:+,} bytes")
print(f"Written to: {DST}")
print("SUCCESS!")
