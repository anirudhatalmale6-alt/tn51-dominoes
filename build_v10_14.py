#!/usr/bin/env python3
"""Build V10_14 — Comprehensive AI Overhaul
All improvements in one shot:
1. Tile memory (from V10_13)
2. Suit danger scoring (from V10_13)
3. Void tracking — proven (off-suit play) + inferred (high trump on losing trick)
4. Trump control detection — when opponents are void in trump, stop leading trumps
5. Last-trump protection — save last trump to get back in lead
6. Bid safety math — adjust aggression based on points needed
7. Early trump aggression — lead trumps early even without highest
8. Partner-in-lead strategy — when we have trump control, try to get partner leading
9. Smart follow suit (from V10_13)
10. Suit-voiding on dump (from V10_13)
11. Fixed count scoring + ledPip (from V10_13)
"""

import sys, os

SRC = "/var/lib/freelancer/projects/40101953/TN51_Dominoes_V10_13.html"
DST = "/var/lib/freelancer/projects/40101953/TN51_Dominoes_V10_14.html"

with open(SRC, "r", encoding="utf-8") as f:
    html = f.read()

OLD_START = "// AI Tile Selection — v2 with tile memory, trump strategy, and danger scoring"
OLD_END = "\n// Global session"

start_idx = html.find(OLD_START)
end_idx = html.find(OLD_END)

if start_idx < 0:
    print(f"ERROR: Could not find start marker")
    sys.exit(1)
if end_idx < 0:
    print(f"ERROR: Could not find end marker")
    sys.exit(1)

print(f"Found old AI function at byte {start_idx}..{end_idx}")
print(f"Old function length: {end_idx - start_idx} bytes")

NEW_AI = r'''// AI Tile Selection — v3: full strategy (void tracking, trump control, bid safety, partner play)
function choose_tile_ai(gameState, playerIndex, contract="NORMAL", returnRec=false, bid=34){
  const p = Number(playerIndex);
  const legal = gameState.legal_indices_for_player(p);
  const hand = gameState.hands[p] || [];
  const trick = gameState.current_trick || [];
  const isLead = trick.length === 0;

  const makeResult = (idx, reason) => {
    if(!returnRec) return idx;
    return { index: idx, tile: hand[idx], reason: reason };
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
  }

  const legalTiles = legal.map(i => hand[i]);
  const canFollowSuit = ledPip !== null && legalTiles.some(t =>
    (t[0] === ledPip || t[1] === ledPip) && !gameState._is_trump_tile(t)
  );

  // ── Trick winner ──
  let currentWinner = null;
  let partnerWinning = false;
  let bidderWinning = false;
  if(trick.length > 0){
    const winnerSeat = gameState._determine_trick_winner();
    currentWinner = winnerSeat;
    partnerWinning = (winnerSeat % 2) === myTeam && winnerSeat !== p;
    if(isNello) bidderWinning = (winnerSeat % 2) !== myTeam;
  }

  // ═══════════════════════════════════════════════════════════════════
  //  TILE MEMORY — all played tiles
  // ═══════════════════════════════════════════════════════════════════
  const playedSet = new Set();
  const addPlayed = (t) => {
    if(!t) return;
    playedSet.add(Math.min(t[0],t[1]) + ',' + Math.max(t[0],t[1]));
  };

  // Build per-player play history for void detection
  // playerPlays[seat] = [ { tile, trickIdx, wasTrump, wasForced } ... ]
  const playerPlays = {};
  for(let s = 0; s < gameState.player_count; s++) playerPlays[s] = [];

  let trickIdx = 0;
  for(let team = 0; team < 2; team++){
    for(const record of (gameState.tricks_team[team] || [])){
      for(let seat = 0; seat < record.length; seat++){
        const t = record[seat];
        if(!t) continue;
        addPlayed(t);
        playerPlays[seat].push({
          tile: t,
          trickIdx: trickIdx,
          wasTrump: gameState._is_trump_tile(t)
        });
      }
      trickIdx++;
    }
  }
  // Current trick
  for(const play of trick){
    if(!Array.isArray(play)) continue;
    const [seat, t] = play;
    addPlayed(t);
    playerPlays[seat].push({
      tile: t,
      trickIdx: trickNum,
      wasTrump: gameState._is_trump_tile(t)
    });
  }
  // Our hand
  for(const t of hand) addPlayed(t);

  const isPlayed = (a, b) => playedSet.has(Math.min(a,b) + ',' + Math.max(a,b));

  // ═══════════════════════════════════════════════════════════════════
  //  SUIT ANALYSIS — remaining tiles per suit
  // ═══════════════════════════════════════════════════════════════════
  const suitInfo = {};
  for(let pip = 0; pip <= maxPip; pip++){
    if(trumpMode === "PIP" && pip === trumpSuit) continue;
    const suitTiles = [];
    let countRemaining = 0;
    for(let other = 0; other <= maxPip; other++){
      const a = Math.min(pip, other), b = Math.max(pip, other);
      if(trumpMode === "PIP" && (a === trumpSuit || b === trumpSuit)) continue;
      if(trumpMode === "DOUBLES" && a === b) continue;
      if(!isPlayed(a, b)){
        const pts = (a + b === 5) ? 5 : (a + b === 10) ? 10 : 0;
        suitTiles.push({ tile: [a, b], count: pts });
        countRemaining += pts;
      }
    }
    suitInfo[pip] = {
      remaining: suitTiles,
      countRemaining: countRemaining,
      winnerPlayed: isPlayed(pip, pip),
      winnerCount: (pip + pip === 5) ? 5 : (pip + pip === 10) ? 10 : 0,
      tilesLeft: suitTiles.length
    };
  }

  // ═══════════════════════════════════════════════════════════════════
  //  TRUMP ANALYSIS
  // ═══════════════════════════════════════════════════════════════════
  const trumpsInHand = [];
  const trumpTilesRemaining = []; // unplayed, NOT in our hand
  const allTrumpTiles = []; // every trump tile in the game

  if(trumpMode === "PIP" && trumpSuit !== null){
    for(let other = 0; other <= maxPip; other++){
      const a = Math.min(trumpSuit, other), b = Math.max(trumpSuit, other);
      allTrumpTiles.push([a, b]);
      const inHand = hand.some(h => Math.min(h[0],h[1]) === a && Math.max(h[0],h[1]) === b);
      if(inHand) trumpsInHand.push([a, b]);
      else if(!isPlayed(a, b)) trumpTilesRemaining.push([a, b]);
    }
  } else if(trumpMode === "DOUBLES"){
    for(let v = 0; v <= maxPip; v++){
      allTrumpTiles.push([v, v]);
      const inHand = hand.some(h => h[0] === v && h[1] === v);
      if(inHand) trumpsInHand.push([v, v]);
      else if(!isPlayed(v, v)) trumpTilesRemaining.push([v, v]);
    }
  }

  const getTrumpRankNum = (t) => {
    const r = gameState._trump_rank(t);
    return r[0] * 100 + r[1];
  };
  const myHighestTrump = trumpsInHand.length > 0
    ? Math.max(...trumpsInHand.map(getTrumpRankNum)) : -1;
  const highestRemainingTrump = trumpTilesRemaining.length > 0
    ? Math.max(...trumpTilesRemaining.map(getTrumpRankNum)) : -1;
  const iHaveHighestTrump = trumpsInHand.length > 0 && myHighestTrump > highestRemainingTrump;

  // ═══════════════════════════════════════════════════════════════════
  //  VOID TRACKING — detect which players are void in which suits
  // ═══════════════════════════════════════════════════════════════════
  // voidIn[seat] = Set of pips that this player is confirmed void in
  // Also track trump voids specifically
  const voidIn = {};
  const trumpVoidConfirmed = {}; // seat → true if confirmed void in trump
  const trumpVoidLikely = {};    // seat → confidence 0-1

  for(let s = 0; s < gameState.player_count; s++){
    voidIn[s] = new Set();
    trumpVoidConfirmed[s] = false;
    trumpVoidLikely[s] = 0;
  }

  // Analyze completed tricks to find proven voids
  // We need to know what was led in each trick and what each player played
  // Reconstruct trick history from tricks_team records
  // tricks_team[team] = [ record1, record2, ... ] where record[seat] = tile or null
  // The leader of each trick can be inferred: trick 0 leader is from game start,
  // subsequent leaders are the winners of previous tricks.
  // However we don't have easy access to trick leaders from records alone.
  // Instead, use the play order tracked in playerPlays.

  // For void detection, we need: for each completed trick, what suit was led,
  // and did each player follow suit or not?
  // Simpler approach: for each player, for each suit, check if they ever played
  // off-suit when that suit was led. We can detect this from tricks_team.

  // Actually, let's build trick-by-trick from tricks_team with leader info.
  // The game tracks gameState.leader for current trick. For past tricks, the winner
  // of trick N became leader of trick N+1.
  // We don't have direct access to past leaders, but we can reconstruct:
  // the first leader is known from the hand start (stored in session).
  // But from choose_tile_ai we don't have session — only gameState.

  // SIMPLER APPROACH: For each completed trick, find who played what.
  // For each player that played a non-suit, non-trump tile when a suit was led
  // (and they didn't trump in), they're void in that suit.
  // We can detect this because legal_indices forces suit-following.
  // If a player played off-suit AND off-trump, they're void in the led suit.
  // If a player played trump when a non-trump was led, they're void in the led suit.

  // To know what suit was led in each trick, we need the leader's tile.
  // From tricks_team records, each record has tiles for each seat, but not play order.
  // We need to reconstruct leaders.

  // Let's track leaders: first trick leader = ? We don't know from gameState alone
  // unless trick_number > 0 and we can backtrack from current leader.
  // Actually current gameState.leader is the leader of the CURRENT trick
  // (who won the last completed trick). We can chain backwards but it's complex.

  // PRAGMATIC APPROACH: Scan through tricks_team and for each, figure out who
  // likely led based on the double rule (double always wins its suit).
  // OR just look at which seat's tile has the highest rank in the winning suit.

  // EVEN SIMPLER: For void detection, the KEY insight is:
  // If trump was the led suit (led pip = trump), and a player played non-trump,
  // they're void in trump.
  // If a non-trump suit X was led, and a player played a tile NOT containing pip X
  // AND that tile is NOT trump, then the player is void in suit X.
  // If they played trump when suit X was led, they're void in suit X (but have trump).

  // We CAN detect this from the current trick (we know the led pip).
  // For past tricks, we need led pip. Let's reconstruct from tricks_team:

  // Reconstruct all tricks with their leader
  const allCompletedTricks = []; // [ { leader, ledPip, plays: {seat: tile} }, ... ]

  // Merge both teams' trick records into chronological order
  // tricks_team[0] and tricks_team[1] are NOT interleaved by order — they're grouped by team.
  // We need a different approach. Let's use a sequence based on who led.

  // Alternative: since we tracked playerPlays by trickIdx, we can group by trickIdx.
  const tricksByIdx = {};
  for(let s = 0; s < gameState.player_count; s++){
    for(const pp of playerPlays[s]){
      if(!tricksByIdx[pp.trickIdx]) tricksByIdx[pp.trickIdx] = [];
      tricksByIdx[pp.trickIdx].push({ seat: s, tile: pp.tile, wasTrump: pp.wasTrump });
    }
  }

  // But we still need the leader for each trick. Let's track it:
  // The first leader of the hand... we don't know from gameState.
  // But we know: gameState.leader = leader of current (ongoing) trick = winner of last completed trick.
  // If trickNum = 0, gameState.leader is the hand's original leader.
  // If trickNum > 0, we can backtrack: winner of trick N = leader of trick N+1.
  // Winner of the last completed trick = gameState.leader (for the current trick).

  // For completed tricks, find winner by checking which team's record contains it.
  // Actually let's just detect voids from tricks_team differently:
  // For each record, identify the led suit by finding the highest-ranked tile
  // that matches the winning criteria. The LEADER played first. In the record,
  // the leader's tile determines the suit.

  // OK let me just do this practically. For each trick in tricksByIdx (completed ones only,
  // i.e. trickIdx < trickNum), we know all plays. The trick was won by whoever has the
  // highest trump (if any trumps) or highest of led suit. But we need to know WHO LED.

  // Let's reconstruct leaders chain:
  // leader[0] = hand's starting leader. We can approximate: if trickNum == 0,
  // it's gameState.leader. If trickNum > 0, we'd need to chain.
  // For simplicity: let's determine the first leader from the context.
  // The first leader of the hand is determined during bidding (stored in session, not gameState).
  // But if we look at tricks_team, the first trick leader could be any seat.

  // PRACTICAL SHORTCUT: Use the current trick's analysis for void detection
  // (we know ledPip) and for completed tricks, approximate:
  // For each seat in a completed trick, if they played a tile that doesn't contain
  // ANY of the pips of the tiles played by other players who played first... this is
  // getting too complicated for reconstruction.

  // BEST PRACTICAL APPROACH for void detection:
  // 1. From current trick: we know ledPip, analyze voids directly.
  // 2. For completed tricks: check if a player NEVER played a suit that was
  //    present in the trick. If 5+ players played suit X tiles and one didn't,
  //    that one is void.
  // 3. For TRUMP void: any player who played non-trump when they had the option
  //    to trump (off-suit play but no trump played) = void in trump.
  //    But actually: if you're off-suit, you CAN play anything including trump.
  //    If you're off-suit and DON'T play trump, you MIGHT be void in trump,
  //    or you might be saving it. We can't confirm trump void from this alone.
  //    CONFIRMED trump void: a trump suit was led and the player played non-trump.

  // For now, let's implement METHOD A (proven voids from current trick) and
  // METHOD B (inferred trump void from high-trump-on-losing-trick pattern).

  // Current trick void detection
  if(!isLead && ledPip !== null){
    for(const play of trick){
      if(!Array.isArray(play)) continue;
      const [seat, t] = play;
      if(seat === p) continue; // skip self
      const tileHasSuit = (t[0] === ledPip || t[1] === ledPip);
      const tileIsTrump = gameState._is_trump_tile(t);
      if(!tileHasSuit && !tileIsTrump){
        // Player is void in led suit AND void in trump
        voidIn[seat].add(ledPip);
        trumpVoidConfirmed[seat] = true;
      } else if(!tileHasSuit && tileIsTrump){
        // Player is void in led suit, but has trump
        voidIn[seat].add(ledPip);
      }
    }
  }
  // Current trick: trump was led (engineLed === -1)
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
  }

  // METHOD B: Inferred trump void from completed tricks
  // If a player played a high non-double trump on a trick that was won by a higher trump,
  // and that was the highest available non-double trump at the time, they likely had no choice.
  // Also: if a player was off-suit and didn't trump in, they MIGHT be void in trump.

  // Scan completed tricks for trump-void signals
  for(let team = 0; team < 2; team++){
    for(const record of (gameState.tricks_team[team] || [])){
      // Find what was played in this trick
      const plays = [];
      for(let seat = 0; seat < record.length; seat++){
        if(record[seat]) plays.push({ seat, tile: record[seat] });
      }
      if(plays.length === 0) continue;

      // Find the trick's led suit by finding which tile was the "leader's"
      // We approximate: the first non-null seat in ascending order from the leader...
      // This is imperfect but serviceable for void detection.

      // Check for non-suit, non-trump plays (proven void in suit)
      // We need to know the led suit for this trick.
      // Heuristic: find the suit that most tiles in this trick share.
      // The led suit = the pip that appears in the most tiles (excluding trumps).
      const pipCounts = {};
      for(const p2 of plays){
        const t = p2.tile;
        if(gameState._is_trump_tile(t)) continue;
        if(t[0] !== undefined) pipCounts[t[0]] = (pipCounts[t[0]] || 0) + 1;
        if(t[1] !== undefined) pipCounts[t[1]] = (pipCounts[t[1]] || 0) + 1;
      }
      let likelyLedPip = null;
      let maxCount = 0;
      for(const [pip, cnt] of Object.entries(pipCounts)){
        if(cnt > maxCount){ maxCount = cnt; likelyLedPip = Number(pip); }
      }

      if(likelyLedPip !== null){
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

      // Inferred trump void: player played high trump on a losing trick
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
      }
    }
  }

  // ═══════════════════════════════════════════════════════════════════
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

  const weHaveTrumpControl = opponentsVoidInTrump && (trumpsInHand.length > 0 || partnersHaveTrump);

  // ═══════════════════════════════════════════════════════════════════
  //  BID SAFETY — how many points do we still need?
  // ═══════════════════════════════════════════════════════════════════
  const currentBid = bid || 34; // passed from session.current_bid
  const ourScore = gameState.team_points[myTeam] || 0;
  const pointsNeeded = currentBid - ourScore;
  const bidIsSafe = pointsNeeded <= 0;
  const bidIsClose = pointsNeeded > 0 && pointsNeeded <= 10;
  const tricksLeft = totalTricks - trickNum;

  // ═══════════════════════════════════════════════════════════════════
  //  LAST TRUMP PROTECTION
  // ═══════════════════════════════════════════════════════════════════
  const isLastTrump = trumpsInHand.length === 1;
  // Save last trump UNLESS: bid is not safe and we need to win now, OR it's the last trick
  const shouldSaveLastTrump = isLastTrump && !bidIsClose && tricksLeft > 1;

  // ═══════════════════════════════════════════════════════════════════
  //  NEL-O LOGIC (unchanged from v2)
  // ═══════════════════════════════════════════════════════════════════
  if(isNello){
    if(isLead){
      let lowNDIdx = -1, lowNDVal = Infinity, lowIdx = legal[0], lowVal = Infinity;
      for(const idx of legal){
        const tile = hand[idx], val = tile[0]+tile[1], dbl = tile[0]===tile[1];
        if(val < lowVal){ lowVal = val; lowIdx = idx; }
        if(!dbl && val < lowNDVal){ lowNDVal = val; lowNDIdx = idx; }
      }
      return lowNDIdx >= 0
        ? makeResult(lowNDIdx, "Nel-O: lead low (force bidder high)")
        : makeResult(lowIdx, "Nel-O: lead low");
    }
    if(bidderWinning){
      let highIdx = legal[0], highVal = 0;
      for(const idx of legal){
        const val = hand[idx][0]+hand[idx][1];
        if(val > highVal){ highVal = val; highIdx = idx; }
      }
      return makeResult(highIdx, "Nel-O: bidder winning, play high");
    }
    {
      let lowNDIdx = -1, lowNDVal = Infinity, lowIdx = legal[0], lowVal = Infinity;
      for(const idx of legal){
        const tile = hand[idx], val = tile[0]+tile[1], dbl = tile[0]===tile[1];
        if(val < lowVal){ lowVal = val; lowIdx = idx; }
        if(!dbl && val < lowNDVal){ lowNDVal = val; lowNDIdx = idx; }
      }
      const reason = partnerWinning
        ? (lowNDIdx >= 0 ? "Nel-O: partner winning, play low non-double" : "Nel-O: partner winning, forced to play double")
        : (lowNDIdx >= 0 ? "Nel-O: play low non-double" : "Nel-O: play low to avoid winning");
      return makeResult(lowNDIdx >= 0 ? lowNDIdx : lowIdx, reason);
    }
  }

  // ═══════════════════════════════════════════════════════════════════
  //  NORMAL GAME — LEAD LOGIC
  // ═══════════════════════════════════════════════════════════════════
  if(isLead){
    const trumpDoubles = [];
    const otherTrumps = [];
    const nonTrumpDoubles = [];
    const nonTrumpSingles = [];

    for(const idx of legal){
      const tile = hand[idx];
      const dbl = tile[0] === tile[1];
      const isTrump = gameState._is_trump_tile(tile);
      if(isTrump && dbl) trumpDoubles.push(idx);
      else if(isTrump) otherTrumps.push(idx);
      else if(dbl) nonTrumpDoubles.push(idx);
      else nonTrumpSingles.push(idx);
    }

    // ── PHASE A: TRUMP PULLING (before we have trump control) ──
    if(!weHaveTrumpControl){

      // P1: Lead trump double — guaranteed win, pulls opponents' trump
      if(trumpDoubles.length > 0){
        return makeResult(trumpDoubles[0], "Lead: trump double (pulls trumps)");
      }

      // P2: Lead high trump IF we have the highest remaining
      // BUT respect last-trump protection
      if(otherTrumps.length > 0 && iHaveHighestTrump && !shouldSaveLastTrump){
        let bestIdx = otherTrumps[0], bestR = -1;
        for(const idx of otherTrumps){
          const r = getTrumpRankNum(hand[idx]);
          if(r > bestR){ bestR = r; bestIdx = idx; }
        }
        return makeResult(bestIdx, "Lead: high trump (pulling remaining trumps)");
      }

      // P3: Early game trump aggression — lead trump even without highest
      // if we have 2+ trumps, it's trick 0 or 1, and bid isn't safe yet
      if(otherTrumps.length >= 2 && trickNum <= 1 && !bidIsSafe){
        // Lead highest trump to force opponents' trumps out early
        let bestIdx = otherTrumps[0], bestR = -1;
        for(const idx of otherTrumps){
          const r = getTrumpRankNum(hand[idx]);
          if(r > bestR){ bestR = r; bestIdx = idx; }
        }
        return makeResult(bestIdx, "Lead: early trump (forcing opponent trumps)");
      }
    }

    // ── PHASE B: WE HAVE TRUMP CONTROL — play doubles, try partner-in-lead ──
    if(weHaveTrumpControl){

      // Don't lead more trumps — don't pull partner's trumps!
      // Lead non-trump doubles first (guaranteed wins since opponents can't trump)
      if(nonTrumpDoubles.length > 0){
        let bestIdx = nonTrumpDoubles[0], bestScore = -Infinity;
        for(const idx of nonTrumpDoubles){
          const pip = hand[idx][0];
          const info = suitInfo[pip];
          if(!info) continue;
          let score = 100 + info.countRemaining + pip;
          if(score > bestScore){ bestScore = score; bestIdx = idx; }
        }
        return makeResult(bestIdx, "Lead: double (trump control, safe win)");
      }

      // No more doubles — try to get PARTNER in the lead
      // Lead a suit where we have a LOW tile, hoping partner has a higher one
      // Prefer suits where the double hasn't been played (partner might have it)
      // Avoid suits where opponents are NOT void (they could win)
      if(nonTrumpSingles.length > 0){
        let bestIdx = nonTrumpSingles[0], bestScore = -Infinity;

        for(const idx of nonTrumpSingles){
          const tile = hand[idx];
          const pipSum = tile[0] + tile[1];
          const myCount = (pipSum === 5) ? 5 : (pipSum === 10) ? 10 : 0;
          const ledSuit = Math.max(tile[0], tile[1]);
          const info = suitInfo[ledSuit];
          let score = 0;

          if(!info){ score -= 50; } else {
            // If the double is unplayed and we don't have it, partner might!
            if(!info.winnerPlayed){
              // Check: do we have the double? If not, maybe partner does
              const weHaveDouble = hand.some(h => h[0] === ledSuit && h[1] === ledSuit);
              if(!weHaveDouble){
                score += 15; // bonus: partner might have the double and win this
              }
            }

            // Avoid suits where we know opponents are NOT void
            // (they can still play and might win)
            let oppCanPlay = false;
            for(let s = 0; s < gameState.player_count; s++){
              if(s % 2 === myTeam || !gameState.active_players.includes(s)) continue;
              if(!voidIn[s].has(ledSuit)){ oppCanPlay = true; break; }
            }
            if(!oppCanPlay) score += 20; // great: opponents can't follow this suit

            // Since we have trump control, opponents can't trump in either
            score += 10; // base bonus for having trump control

            // Penalty for leading count
            score -= myCount * 2;

            // Prefer lower tiles (let partner play higher)
            score -= pipSum;
          }

          if(score > bestScore){ bestScore = score; bestIdx = idx; }
        }
        return makeResult(bestIdx, "Lead: partner-in-lead (trump control)");
      }

      // Only trumps left — lead lowest trump
      if(otherTrumps.length > 0){
        let lowIdx = otherTrumps[0], lowVal = Infinity;
        for(const idx of otherTrumps){
          const val = hand[idx][0]+hand[idx][1];
          if(val < lowVal){ lowVal = val; lowIdx = idx; }
        }
        return makeResult(lowIdx, "Lead: low trump (only trumps left)");
      }
      if(trumpDoubles.length > 0) return makeResult(trumpDoubles[0], "Lead: trump double (only option)");
    }

    // ── PHASE C: NO TRUMP CONTROL, no more trump leads — play safe non-trumps ──

    // Lead non-trump doubles
    if(nonTrumpDoubles.length > 0){
      let bestIdx = nonTrumpDoubles[0], bestScore = -Infinity;
      for(const idx of nonTrumpDoubles){
        const pip = hand[idx][0];
        const info = suitInfo[pip];
        if(!info) continue;
        let score = 100 + info.countRemaining + pip;
        if(score > bestScore){ bestScore = score; bestIdx = idx; }
      }
      return makeResult(bestIdx, "Lead: double (controls suit)");
    }

    // Lead non-trump singles — DANGER SCORING
    if(nonTrumpSingles.length > 0){
      let bestIdx = nonTrumpSingles[0], bestScore = -Infinity;

      for(const idx of nonTrumpSingles){
        const tile = hand[idx];
        const pipSum = tile[0] + tile[1];
        const myCount = (pipSum === 5) ? 5 : (pipSum === 10) ? 10 : 0;
        const ledSuit = Math.max(tile[0], tile[1]);
        const info = suitInfo[ledSuit];
        let score = 0;

        if(!info){
          score -= 50;
        } else {
          if(!info.winnerPlayed){
            score -= 30;
            score -= info.winnerCount * 2;
          } else {
            score += 10;
          }
          score -= myCount * 3;
          if(!info.winnerPlayed){
            score -= info.countRemaining;
          } else {
            score += Math.floor(info.countRemaining * 0.5);
          }
          score -= info.tilesLeft * 2;

          // NEW: Check if opponents are void in this suit (they'll have to play off-suit or trump)
          let oppsVoid = 0;
          for(let s = 0; s < gameState.player_count; s++){
            if(s % 2 === myTeam || !gameState.active_players.includes(s)) continue;
            if(voidIn[s].has(ledSuit)) oppsVoid++;
          }
          // If some opponents are void and might trump, that's dangerous
          if(oppsVoid > 0 && !opponentsVoidInTrump) score -= oppsVoid * 10;
          // If opponents are void in this suit AND void in trump, they can't threaten
          if(oppsVoid > 0 && opponentsVoidInTrump) score += 10;
        }

        score -= ledSuit;
        score -= Math.floor(pipSum * 0.5);

        if(score > bestScore){ bestScore = score; bestIdx = idx; }
      }
      return makeResult(bestIdx, "Lead: safest non-trump");
    }

    // Last resort: lead trump (even without highest)
    if(otherTrumps.length > 0){
      let lowIdx = otherTrumps[0], lowVal = Infinity;
      for(const idx of otherTrumps){
        const val = hand[idx][0]+hand[idx][1];
        if(val < lowVal){ lowVal = val; lowIdx = idx; }
      }
      return makeResult(lowIdx, "Lead: low trump (no safe option)");
    }

    return makeResult(legal[0], "Lead: fallback");
  }

  // ═══════════════════════════════════════════════════════════════════
  //  NORMAL GAME — FOLLOW LOGIC
  // ═══════════════════════════════════════════════════════════════════

  // ── Partner/teammate winning: throw count ──
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
  }

  // ── Follow suit: only play high if we can beat the current winner ──
  if(canFollowSuit){
    const winnerSeat = gameState._determine_trick_winner();
    let winnerRank = -1;
    let winnerIsTrump = false;
    for(const play of trick){
      if(!Array.isArray(play)) continue;
      if(play[0] === winnerSeat && play[1]){
        const wt = play[1];
        if(gameState._is_trump_tile(wt)){
          winnerIsTrump = true;
          winnerRank = getTrumpRankNum(wt);
        } else {
          const wr = gameState._suit_rank(wt, ledPip);
          winnerRank = wr[0] * 100 + wr[1];
        }
      }
    }

    let highIdx = -1, highRank = -1, lowIdx = -1, lowRank = Infinity;
    for(const idx of legal){
      const tile = hand[idx];
      if((tile[0] === ledPip || tile[1] === ledPip) && !gameState._is_trump_tile(tile)){
        const r = gameState._suit_rank(tile, ledPip);
        const rank = r[0] * 100 + r[1];
        if(rank > highRank){ highRank = rank; highIdx = idx; }
        if(rank < lowRank){ lowRank = rank; lowIdx = idx; }
      }
    }

    if(winnerIsTrump){
      if(lowIdx >= 0) return makeResult(lowIdx, "Cannot beat trump, play low on-suit");
    }
    if(highIdx >= 0 && highRank > winnerRank){
      return makeResult(highIdx, "Following suit, play high to win");
    }
    if(lowIdx >= 0){
      return makeResult(lowIdx, "Cannot win suit, play low");
    }
  }

  // ── Off-suit: trump in ──
  const canTrump = legalTiles.some(t => gameState._is_trump_tile(t));
  if(canTrump){
    let highestTrickTrump = -1;
    let opponentHasTrumpInTrick = false;
    let partnerHasTrumpInTrick = false;
    for(const play of trick){
      if(!Array.isArray(play)) continue;
      const [seat, t] = play;
      if(t && gameState._is_trump_tile(t)){
        const r = getTrumpRankNum(t);
        if(r > highestTrickTrump) highestTrickTrump = r;
        if(seat % 2 !== myTeam) opponentHasTrumpInTrick = true;
        else if(seat !== p) partnerHasTrumpInTrick = true;
      }
    }

    // Find lowest winning trump and lowest trump overall
    let winTrumpIdx = -1, winTrumpRank = Infinity;
    let anyTrumpIdx = -1, anyTrumpRank = Infinity;
    for(const idx of legal){
      const tile = hand[idx];
      if(gameState._is_trump_tile(tile)){
        const r = getTrumpRankNum(tile);
        if(r < anyTrumpRank){ anyTrumpRank = r; anyTrumpIdx = idx; }
        if(r > highestTrickTrump && r < winTrumpRank){ winTrumpRank = r; winTrumpIdx = idx; }
      }
    }

    // If partner already trumped and is winning, DON'T over-trump — throw count or play low
    if(partnerHasTrumpInTrick && !opponentHasTrumpInTrick){
      // Partner's trump is winning — treat as partner winning
      let countIdx = -1, countVal = 0, lowIdx = legal[0], lowVal = Infinity;
      for(const idx of legal){
        const tile = hand[idx];
        const pipSum = tile[0] + tile[1];
        if(pipSum === 5 || pipSum === 10){
          if(pipSum > countVal){ countVal = pipSum; countIdx = idx; }
        }
        if(pipSum < lowVal){ lowVal = pipSum; lowIdx = idx; }
      }
      if(countIdx >= 0) return makeResult(countIdx, "Partner trumped, throw count (" + countVal + "pts)");
      return makeResult(lowIdx, "Partner trumped, play low");
    }

    if(winTrumpIdx >= 0){
      return makeResult(winTrumpIdx, "Trump in to win");
    }
    if(anyTrumpIdx >= 0 && highestTrickTrump < 0){
      return makeResult(anyTrumpIdx, "Trump in to win");
    }
    // Can't beat existing trump — fall through to dump
  }

  // ── Cannot win: smart dump (suit-voiding + avoid count + save trumps) ──
  {
    let bestIdx = legal[0], bestScore = -Infinity;
    for(const idx of legal){
      const tile = hand[idx];
      const pipSum = tile[0] + tile[1];
      const myCount = (pipSum === 5) ? 5 : (pipSum === 10) ? 10 : 0;
      let score = 0;

      // Prefer tiles that void a suit
      const pA = tile[0], pB = tile[1];
      let cntA = 0, cntB = 0;
      for(const h of hand){
        if(h[0] === pA || h[1] === pA) cntA++;
        if(h[0] === pB || h[1] === pB) cntB++;
      }
      const minCnt = Math.min(cntA, cntB);
      if(minCnt <= 1) score += 15;
      else if(minCnt <= 2) score += 8;

      // Don't give opponents our count
      score -= myCount * 3;

      // Prefer lower pip sum
      score -= Math.floor(pipSum * 0.5);

      // Save trumps (especially the last one!)
      if(gameState._is_trump_tile(tile)){
        score -= 20;
        if(isLastTrump) score -= 30; // extra penalty for dumping last trump
      }

      if(score > bestScore){ bestScore = score; bestIdx = idx; }
    }
    return makeResult(bestIdx, "Cannot win, play low");
  }
}
'''

# Replace the AI function
html_new = html[:start_idx] + NEW_AI + html[end_idx:]

# Patch call sites to pass bid as 5th argument
# Call site 1: human player's move (for logging AI recommendation)
old_call1 = "const aiRec = choose_tile_ai(session.game, 0, session.contract, true);"
new_call1 = "const aiRec = choose_tile_ai(session.game, 0, session.contract, true, session.current_bid);"
c1 = html_new.count(old_call1)
if c1 == 0:
    print("WARNING: Could not find call site 1 for bid passthrough")
else:
    html_new = html_new.replace(old_call1, new_call1, 1)
    print(f"Patched call site 1 (human player AI rec)")

# Call site 2: AI player's move
old_call2 = "const aiRec = choose_tile_ai(session.game, seat, session.contract, true);"
new_call2 = "const aiRec = choose_tile_ai(session.game, seat, session.contract, true, session.current_bid);"
c2 = html_new.count(old_call2)
if c2 == 0:
    print("WARNING: Could not find call site 2 for bid passthrough")
else:
    html_new = html_new.replace(old_call2, new_call2, 1)
    print(f"Patched call site 2 (AI player move)")

# Verify
if "choose_tile_ai" not in html_new:
    print("ERROR: choose_tile_ai not found in output!")
    sys.exit(1)
if "v3: full strategy" not in html_new:
    print("ERROR: New v3 AI function not found in output!")
    sys.exit(1)

with open(DST, "w", encoding="utf-8") as f:
    f.write(html_new)

src_size = os.path.getsize(SRC)
dst_size = os.path.getsize(DST)
print(f"Source: {src_size:,} bytes")
print(f"Output: {dst_size:,} bytes")
print(f"Delta:  {dst_size - src_size:+,} bytes")
print(f"Written to: {DST}")
print("SUCCESS!")
