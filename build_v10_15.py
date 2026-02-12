#!/usr/bin/env python3
"""Build V10_15 — Advanced AI Debug Log
Adds comprehensive AI reasoning log that captures:
- Tile memory state
- Suit analysis (danger scores per suit)
- Trump analysis (trumps in hand, remaining, highest)
- Void tracking (confirmed/inferred per opponent)
- Trump control status
- Bid safety calculation
- Candidate tile scores with detailed breakdown
- Final decision reasoning
"""

import sys, os

SRC = "/var/lib/freelancer/projects/40101953/TN51_Dominoes_V10_14.html"
DST = "/var/lib/freelancer/projects/40101953/TN51_Dominoes_V10_15.html"

with open(SRC, "r", encoding="utf-8") as f:
    html = f.read()

# ============================================================
# PATCH 1: Add debugInfo collection to choose_tile_ai
# We inject debug data gathering right after the analysis sections
# and modify makeResult to include it
# ============================================================

# Replace makeResult to include debugInfo
old_makeResult = r"""  const makeResult = (idx, reason) => {
    if(!returnRec) return idx;
    return { index: idx, tile: hand[idx], reason: reason };
  };"""

new_makeResult = r"""  // Debug info collector
  const _dbg = { enabled: returnRec };
  const _dbgCandidates = [];

  const makeResult = (idx, reason) => {
    if(!returnRec) return idx;
    return { index: idx, tile: hand[idx], reason: reason, debugInfo: _dbg.enabled ? _dbg : null };
  };"""

if old_makeResult not in html:
    print("ERROR: Could not find makeResult block")
    sys.exit(1)
html = html.replace(old_makeResult, new_makeResult, 1)
print("Patched makeResult with debug collector")

# After TILE MEMORY section (after "const isPlayed = ..."), inject debug snapshot
old_isPlayed = """  const isPlayed = (a, b) => playedSet.has(Math.min(a,b) + ',' + Math.max(a,b));"""
new_isPlayed = old_isPlayed + """

  // Debug: snapshot tile memory
  if(_dbg.enabled){
    _dbg.playedCount = playedSet.size;
    _dbg.handTiles = hand.map(t => t[0]+'-'+t[1]);
    _dbg.legalTiles = legal.map(i => hand[i][0]+'-'+hand[i][1]);
    _dbg.trickNum = trickNum;
    _dbg.isLead = isLead;
    _dbg.ledPip = ledPip;
    _dbg.myTeam = myTeam;
    _dbg.seat = p;
  }"""

if old_isPlayed not in html:
    print("ERROR: Could not find isPlayed line")
    sys.exit(1)
html = html.replace(old_isPlayed, new_isPlayed, 1)
print("Patched tile memory debug snapshot")

# After SUIT ANALYSIS section, inject suit info debug
old_suit_end = """  // ═══════════════════════════════════════════════════════════════════
  //  TRUMP ANALYSIS
  // ═══════════════════════════════════════════════════════════════════"""

new_suit_end = """  // Debug: suit analysis
  if(_dbg.enabled){
    _dbg.suitAnalysis = {};
    for(const [pip, info] of Object.entries(suitInfo)){
      _dbg.suitAnalysis[pip] = {
        tilesLeft: info.tilesLeft,
        countExposure: info.countRemaining,
        doubleOut: info.winnerPlayed,
        doubleCount: info.winnerCount
      };
    }
  }

  // ═══════════════════════════════════════════════════════════════════
  //  TRUMP ANALYSIS
  // ═══════════════════════════════════════════════════════════════════"""

if old_suit_end not in html:
    print("ERROR: Could not find TRUMP ANALYSIS header")
    sys.exit(1)
html = html.replace(old_suit_end, new_suit_end, 1)
print("Patched suit analysis debug")

# After TRUMP ANALYSIS section (after iHaveHighestTrump), inject trump debug
old_trump_end = """  // ═══════════════════════════════════════════════════════════════════
  //  VOID TRACKING — detect which players are void in which suits
  // ═══════════════════════════════════════════════════════════════════"""

new_trump_end = """  // Debug: trump analysis
  if(_dbg.enabled){
    _dbg.trumpMode = trumpMode;
    _dbg.trumpSuit = trumpSuit;
    _dbg.trumpsInHand = trumpsInHand.map(t => t[0]+'-'+t[1]);
    _dbg.trumpsRemaining = trumpTilesRemaining.map(t => t[0]+'-'+t[1]);
    _dbg.iHaveHighestTrump = iHaveHighestTrump;
    _dbg.myHighestTrumpRank = myHighestTrump;
    _dbg.highestRemainingTrumpRank = highestRemainingTrump;
  }

  // ═══════════════════════════════════════════════════════════════════
  //  VOID TRACKING — detect which players are void in which suits
  // ═══════════════════════════════════════════════════════════════════"""

if old_trump_end not in html:
    print("ERROR: Could not find VOID TRACKING header")
    sys.exit(1)
html = html.replace(old_trump_end, new_trump_end, 1)
print("Patched trump analysis debug")

# After TRUMP CONTROL DETECTION (after weHaveTrumpControl), inject debug
old_bid_safety = """  // ═══════════════════════════════════════════════════════════════════
  //  BID SAFETY — how many points do we still need?
  // ═══════════════════════════════════════════════════════════════════"""

new_bid_safety = """  // Debug: void tracking + trump control
  if(_dbg.enabled){
    _dbg.voidTracking = {};
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
    }
    _dbg.opponentsVoidInTrump = opponentsVoidInTrump;
    _dbg.partnersHaveTrump = partnersHaveTrump;
    _dbg.weHaveTrumpControl = weHaveTrumpControl;
  }

  // ═══════════════════════════════════════════════════════════════════
  //  BID SAFETY — how many points do we still need?
  // ═══════════════════════════════════════════════════════════════════"""

if old_bid_safety not in html:
    print("ERROR: Could not find BID SAFETY header")
    sys.exit(1)
html = html.replace(old_bid_safety, new_bid_safety, 1)
print("Patched void tracking + trump control debug")

# After LAST TRUMP PROTECTION (after shouldSaveLastTrump), inject debug
old_nello = """  // ═══════════════════════════════════════════════════════════════════
  //  NEL-O LOGIC (unchanged from v2)
  // ═══════════════════════════════════════════════════════════════════"""

new_nello = """  // Debug: bid safety + last trump
  if(_dbg.enabled){
    _dbg.bidSafety = {
      currentBid: currentBid,
      ourScore: ourScore,
      pointsNeeded: pointsNeeded,
      bidIsSafe: bidIsSafe,
      bidIsClose: bidIsClose,
      tricksLeft: tricksLeft
    };
    _dbg.lastTrump = {
      isLastTrump: isLastTrump,
      shouldSaveLastTrump: shouldSaveLastTrump
    };
  }

  // ═══════════════════════════════════════════════════════════════════
  //  NEL-O LOGIC (unchanged from v2)
  // ═══════════════════════════════════════════════════════════════════"""

if old_nello not in html:
    print("ERROR: Could not find NEL-O LOGIC header")
    sys.exit(1)
html = html.replace(old_nello, new_nello, 1)
print("Patched bid safety + last trump debug")

# Now we need to add candidate scoring debug at each major decision point.
# Instead of modifying every single return statement (risky), we'll add
# a debug wrapper that logs candidates for the LEAD and FOLLOW sections.

# For LEAD: inject candidate logging in Phase C danger scoring (the most complex one)
# This is the "Lead non-trump singles — DANGER SCORING" block

old_danger_start = """    // Lead non-trump singles — DANGER SCORING
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
    }"""

new_danger_start = """    // Lead non-trump singles — DANGER SCORING
    if(nonTrumpSingles.length > 0){
      let bestIdx = nonTrumpSingles[0], bestScore = -Infinity;
      const _leadCandidates = [];

      for(const idx of nonTrumpSingles){
        const tile = hand[idx];
        const pipSum = tile[0] + tile[1];
        const myCount = (pipSum === 5) ? 5 : (pipSum === 10) ? 10 : 0;
        const ledSuit = Math.max(tile[0], tile[1]);
        const info = suitInfo[ledSuit];
        let score = 0;
        const _breakdown = {};

        if(!info){
          score -= 50;
          _breakdown.noInfo = -50;
        } else {
          if(!info.winnerPlayed){
            score -= 30;
            score -= info.winnerCount * 2;
            _breakdown.doubleNotOut = -30;
            _breakdown.doubleCountPenalty = -(info.winnerCount * 2);
          } else {
            score += 10;
            _breakdown.doubleOut = +10;
          }
          score -= myCount * 3;
          _breakdown.myCountPenalty = -(myCount * 3);
          if(!info.winnerPlayed){
            score -= info.countRemaining;
            _breakdown.suitCountRisk = -(info.countRemaining);
          } else {
            score += Math.floor(info.countRemaining * 0.5);
            _breakdown.suitCountBonus = Math.floor(info.countRemaining * 0.5);
          }
          score -= info.tilesLeft * 2;
          _breakdown.tilesLeftPenalty = -(info.tilesLeft * 2);

          // NEW: Check if opponents are void in this suit (they'll have to play off-suit or trump)
          let oppsVoid = 0;
          for(let s = 0; s < gameState.player_count; s++){
            if(s % 2 === myTeam || !gameState.active_players.includes(s)) continue;
            if(voidIn[s].has(ledSuit)) oppsVoid++;
          }
          // If some opponents are void and might trump, that's dangerous
          if(oppsVoid > 0 && !opponentsVoidInTrump){ score -= oppsVoid * 10; _breakdown.oppVoidTrumpRisk = -(oppsVoid * 10); }
          // If opponents are void in this suit AND void in trump, they can't threaten
          if(oppsVoid > 0 && opponentsVoidInTrump){ score += 10; _breakdown.oppVoidSafe = +10; }
          _breakdown.oppsVoidInSuit = oppsVoid;
        }

        score -= ledSuit;
        _breakdown.pipPenalty = -ledSuit;
        score -= Math.floor(pipSum * 0.5);
        _breakdown.sumPenalty = -Math.floor(pipSum * 0.5);

        _leadCandidates.push({
          tile: tile[0]+'-'+tile[1],
          suit: ledSuit,
          count: myCount,
          totalScore: score,
          breakdown: _breakdown
        });
        if(score > bestScore){ bestScore = score; bestIdx = idx; }
      }
      if(_dbg.enabled) _dbg.leadCandidates = _leadCandidates;
      return makeResult(bestIdx, "Lead: safest non-trump");
    }"""

if old_danger_start not in html:
    print("ERROR: Could not find danger scoring lead block")
    sys.exit(1)
html = html.replace(old_danger_start, new_danger_start, 1)
print("Patched lead danger scoring with candidate debug")

# Also add candidate scoring for the DUMP section
old_dump = """  // ── Cannot win: smart dump (suit-voiding + avoid count + save trumps) ──
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
  }"""

new_dump = """  // ── Cannot win: smart dump (suit-voiding + avoid count + save trumps) ──
  {
    let bestIdx = legal[0], bestScore = -Infinity;
    const _dumpCandidates = [];
    for(const idx of legal){
      const tile = hand[idx];
      const pipSum = tile[0] + tile[1];
      const myCount = (pipSum === 5) ? 5 : (pipSum === 10) ? 10 : 0;
      let score = 0;
      const _bd = {};

      // Prefer tiles that void a suit
      const pA = tile[0], pB = tile[1];
      let cntA = 0, cntB = 0;
      for(const h of hand){
        if(h[0] === pA || h[1] === pA) cntA++;
        if(h[0] === pB || h[1] === pB) cntB++;
      }
      const minCnt = Math.min(cntA, cntB);
      if(minCnt <= 1){ score += 15; _bd.voidBonus = 15; }
      else if(minCnt <= 2){ score += 8; _bd.voidBonus = 8; }
      _bd.suitCounts = cntA+'|'+cntB;

      // Don't give opponents our count
      score -= myCount * 3;
      _bd.countPenalty = -(myCount * 3);

      // Prefer lower pip sum
      score -= Math.floor(pipSum * 0.5);
      _bd.sumPenalty = -Math.floor(pipSum * 0.5);

      // Save trumps (especially the last one!)
      if(gameState._is_trump_tile(tile)){
        score -= 20;
        _bd.trumpPenalty = -20;
        if(isLastTrump){ score -= 30; _bd.lastTrumpPenalty = -30; }
      }

      _dumpCandidates.push({
        tile: tile[0]+'-'+tile[1],
        count: myCount,
        totalScore: score,
        breakdown: _bd
      });
      if(score > bestScore){ bestScore = score; bestIdx = idx; }
    }
    if(_dbg.enabled) _dbg.dumpCandidates = _dumpCandidates;
    return makeResult(bestIdx, "Cannot win, play low");
  }"""

if old_dump not in html:
    print("ERROR: Could not find dump block")
    sys.exit(1)
html = html.replace(old_dump, new_dump, 1)
print("Patched dump section with candidate debug")

# Also add candidate debug for the follow-suit section
old_follow = """  // ── Follow suit: only play high if we can beat the current winner ──
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
  }"""

new_follow = """  // ── Follow suit: only play high if we can beat the current winner ──
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
    const _followCandidates = [];
    for(const idx of legal){
      const tile = hand[idx];
      if((tile[0] === ledPip || tile[1] === ledPip) && !gameState._is_trump_tile(tile)){
        const r = gameState._suit_rank(tile, ledPip);
        const rank = r[0] * 100 + r[1];
        _followCandidates.push({ tile: tile[0]+'-'+tile[1], rank: rank, isDouble: tile[0]===tile[1] });
        if(rank > highRank){ highRank = rank; highIdx = idx; }
        if(rank < lowRank){ lowRank = rank; lowIdx = idx; }
      }
    }

    if(_dbg.enabled){
      _dbg.followSuit = {
        ledPip: ledPip,
        currentWinnerSeat: winnerSeat,
        winnerRank: winnerRank,
        winnerIsTrump: winnerIsTrump,
        candidates: _followCandidates,
        highRank: highRank,
        lowRank: lowRank,
        canBeat: highRank > winnerRank
      };
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
  }"""

if old_follow not in html:
    print("ERROR: Could not find follow-suit block")
    sys.exit(1)
html = html.replace(old_follow, new_follow, 1)
print("Patched follow-suit with candidate debug")

# Add trump-in debug
old_trump_in = """  // ── Off-suit: trump in ──
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
    if(partnerHasTrumpInTrick && !opponentHasTrumpInTrick){"""

new_trump_in = """  // ── Off-suit: trump in ──
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
    const _trumpCandidates = [];
    for(const idx of legal){
      const tile = hand[idx];
      if(gameState._is_trump_tile(tile)){
        const r = getTrumpRankNum(tile);
        _trumpCandidates.push({ tile: tile[0]+'-'+tile[1], rank: r, canWin: r > highestTrickTrump });
        if(r < anyTrumpRank){ anyTrumpRank = r; anyTrumpIdx = idx; }
        if(r > highestTrickTrump && r < winTrumpRank){ winTrumpRank = r; winTrumpIdx = idx; }
      }
    }

    if(_dbg.enabled){
      _dbg.trumpIn = {
        highestTrickTrump: highestTrickTrump,
        oppHasTrump: opponentHasTrumpInTrick,
        partnerHasTrump: partnerHasTrumpInTrick,
        candidates: _trumpCandidates
      };
    }

    // If partner already trumped and is winning, DON'T over-trump — throw count or play low
    if(partnerHasTrumpInTrick && !opponentHasTrumpInTrick){"""

if old_trump_in not in html:
    print("ERROR: Could not find trump-in block")
    sys.exit(1)
html = html.replace(old_trump_in, new_trump_in, 1)
print("Patched trump-in with candidate debug")

# Add lead phase categorization debug
old_lead_cats = """    const trumpDoubles = [];
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
    }"""

new_lead_cats = """    const trumpDoubles = [];
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

    if(_dbg.enabled){
      _dbg.leadCategories = {
        trumpDoubles: trumpDoubles.map(i => hand[i][0]+'-'+hand[i][1]),
        otherTrumps: otherTrumps.map(i => hand[i][0]+'-'+hand[i][1]),
        nonTrumpDoubles: nonTrumpDoubles.map(i => hand[i][0]+'-'+hand[i][1]),
        nonTrumpSingles: nonTrumpSingles.map(i => hand[i][0]+'-'+hand[i][1]),
        phase: weHaveTrumpControl ? 'B (trump control)' : 'A/C (no control)'
      };
    }"""

if old_lead_cats not in html:
    print("ERROR: Could not find lead categories block")
    sys.exit(1)
html = html.replace(old_lead_cats, new_lead_cats, 1)
print("Patched lead categories debug")

# ============================================================
# PATCH 2: Store debugInfo in log entries
# ============================================================

# Modify logPlay to accept and store debugInfo
old_logplay_entry = """  const entry = {
    type: "PLAY",
    handId: handNumber,
    trickId: trickNumber,
    seat: player,
    tilePlayed: _tileStr(tile),
    isAISeat: isAISeat,
    wasOverride: wasOverride,
    aiSuggestedTile: aiTile ? _tileStr(aiTile) : null,
    aiReason: aiRec ? aiRec.reason : (reason || null),
    legalMoves: ctx.legalTiles ? _tilesStr(ctx.legalTiles) : null,
    partnerCurrentlyWinning: ctx.currentWinner ? (_partnerSeats(player).includes(ctx.currentWinner.seat)) : false,
    positionInTrick: currentTrickPlays.length,
    timestamp: new Date().toISOString()
  };"""

new_logplay_entry = """  const entry = {
    type: "PLAY",
    handId: handNumber,
    trickId: trickNumber,
    seat: player,
    tilePlayed: _tileStr(tile),
    isAISeat: isAISeat,
    wasOverride: wasOverride,
    aiSuggestedTile: aiTile ? _tileStr(aiTile) : null,
    aiReason: aiRec ? aiRec.reason : (reason || null),
    aiDebug: aiRec && aiRec.debugInfo ? aiRec.debugInfo : null,
    legalMoves: ctx.legalTiles ? _tilesStr(ctx.legalTiles) : null,
    partnerCurrentlyWinning: ctx.currentWinner ? (_partnerSeats(player).includes(ctx.currentWinner.seat)) : false,
    positionInTrick: currentTrickPlays.length,
    timestamp: new Date().toISOString()
  };"""

if old_logplay_entry not in html:
    print("ERROR: Could not find logPlay entry block")
    sys.exit(1)
html = html.replace(old_logplay_entry, new_logplay_entry, 1)
print("Patched logPlay to store debugInfo")

# ============================================================
# PATCH 3: Add Advanced Log formatter + UI
# ============================================================

# Find the formatGameLog function and add formatAdvancedLog after it
old_format_end = """document.getElementById('menuGameLog').addEventListener('click', () => {
  document.getElementById('settingsMenu').classList.remove('open');
  document.getElementById('gameLogContent').textContent = formatGameLog() || 'No log entries yet.';
  document.getElementById('gameLogBackdrop').style.display = 'flex';
});"""

new_format_end = """function formatAdvancedLog(){
  let text = "=== TENNESSEE 51 — ADVANCED AI DEBUG LOG ===\\n";
  text += "=== Generated: " + new Date().toISOString() + " ===\\n\\n";

  for(const entry of gameLog){
    if(entry.type === "HAND_START"){
      text += "\\n" + "=".repeat(70) + "\\n";
      text += " HAND " + (entry.handId + 1) + "\\n";
      text += "=".repeat(70) + "\\n";
      const c = entry.contract || {};
      text += "Contract: " + (c.mode||"NORMAL") + " | Trump: " + (c.trumpDisplay||"?");
      text += " | Bid: " + (c.bid||"?") + " by P" + seatToPlayer(c.bidderSeat||0);
      text += " (Team " + (c.bidderTeam||"?") + ")\\n";
      const scores = entry.scoresBeforeHand || {};
      text += "Scores Before: Team1=" + (scores.team1||0) + " Team2=" + (scores.team2||0) + "\\n";
      if(entry.hands){
        text += "Hands:\\n";
        for(const h of entry.hands){
          if(h.tiles && h.tiles.length > 0){
            text += "  P" + seatToPlayer(h.seat) + " (T" + h.team + "): " + h.tiles.join(", ") + "\\n";
          }
        }
      }
    }
    else if(entry.type === "TRICK_START"){
      text += "\\n--- Trick " + (entry.trickId + 1) + " ---\\n";
      text += "  Leader: P" + seatToPlayer(entry.leaderSeat) + " (Team " + entry.leaderTeam + ")\\n";
    }
    else if(entry.type === "PLAY"){
      const actor = entry.isAISeat ? "[AI]" : "[Human]";
      text += "\\n  P" + seatToPlayer(entry.seat) + " " + actor + " plays: " + entry.tilePlayed;
      if(entry.aiReason) text += " — " + entry.aiReason;
      if(entry.wasOverride) text += " [OVERRIDE! AI wanted: " + entry.aiSuggestedTile + "]";
      text += "\\n";
      if(entry.legalMoves && entry.legalMoves.length > 1){
        text += "    Legal moves: " + entry.legalMoves.join(", ") + "\\n";
      }

      // === ADVANCED DEBUG ===
      const d = entry.aiDebug;
      if(d){
        text += "    ┌─── AI REASONING ───\\n";
        text += "    │ Seat: " + d.seat + " | Team: " + d.myTeam + " | Trick: " + d.trickNum;
        text += " | " + (d.isLead ? "LEADING" : "FOLLOWING (led pip: " + d.ledPip + ")") + "\\n";
        text += "    │ Hand: [" + (d.handTiles||[]).join(", ") + "]\\n";
        text += "    │ Legal: [" + (d.legalTiles||[]).join(", ") + "]\\n";
        text += "    │ Played tiles tracked: " + d.playedCount + "\\n";

        // Trump info
        if(d.trumpMode && d.trumpMode !== "NONE"){
          text += "    │\\n";
          text += "    │ TRUMP: mode=" + d.trumpMode + " suit=" + d.trumpSuit + "\\n";
          text += "    │   In hand: [" + (d.trumpsInHand||[]).join(", ") + "]\\n";
          text += "    │   Remaining (not in hand): [" + (d.trumpsRemaining||[]).join(", ") + "]\\n";
          text += "    │   I have highest trump: " + d.iHaveHighestTrump;
          text += " (my rank: " + d.myHighestTrumpRank + " vs remaining: " + d.highestRemainingTrumpRank + ")\\n";
        }

        // Suit analysis
        if(d.suitAnalysis){
          const sa = d.suitAnalysis;
          const pips = Object.keys(sa).sort((a,b) => Number(a)-Number(b));
          if(pips.length > 0){
            text += "    │\\n";
            text += "    │ SUIT ANALYSIS:\\n";
            for(const pip of pips){
              const s = sa[pip];
              text += "    │   Suit " + pip + ": " + s.tilesLeft + " tiles left";
              text += ", count exposure=" + s.countExposure;
              text += ", double " + (s.doubleOut ? "OUT" : "still in (" + s.doubleCount + "pts)") + "\\n";
            }
          }
        }

        // Void tracking
        if(d.voidTracking && Object.keys(d.voidTracking).length > 0){
          text += "    │\\n";
          text += "    │ VOID TRACKING:\\n";
          for(const [seat, info] of Object.entries(d.voidTracking)){
            text += "    │   " + seat + " (" + info.team + "): void in suits [" + info.voidSuits.join(",") + "]";
            if(info.trumpVoidConfirmed) text += " | TRUMP VOID (confirmed)";
            else if(info.trumpVoidLikely > 0) text += " | trump void likely (" + Math.round(info.trumpVoidLikely*100) + "%)";
            text += "\\n";
          }
        }

        // Trump control
        text += "    │\\n";
        text += "    │ TRUMP CONTROL: " + (d.weHaveTrumpControl ? "YES ✓" : "NO");
        text += " (opps void: " + d.opponentsVoidInTrump + ", partners have trump: " + d.partnersHaveTrump + ")\\n";

        // Bid safety
        if(d.bidSafety){
          const b = d.bidSafety;
          text += "    │ BID: " + b.currentBid + " | Our score: " + b.ourScore;
          text += " | Need: " + b.pointsNeeded + " | ";
          if(b.bidIsSafe) text += "SAFE";
          else if(b.bidIsClose) text += "CLOSE!";
          else text += "still working";
          text += " | Tricks left: " + b.tricksLeft + "\\n";
        }

        // Last trump
        if(d.lastTrump){
          text += "    │ LAST TRUMP: " + (d.lastTrump.isLastTrump ? "YES, only 1 left" : "No");
          if(d.lastTrump.isLastTrump) text += " → " + (d.lastTrump.shouldSaveLastTrump ? "SAVING IT" : "will use if needed");
          text += "\\n";
        }

        // Lead categories
        if(d.leadCategories){
          const lc = d.leadCategories;
          text += "    │\\n";
          text += "    │ LEAD PHASE: " + lc.phase + "\\n";
          if(lc.trumpDoubles.length) text += "    │   Trump doubles: [" + lc.trumpDoubles.join(", ") + "]\\n";
          if(lc.otherTrumps.length) text += "    │   Other trumps: [" + lc.otherTrumps.join(", ") + "]\\n";
          if(lc.nonTrumpDoubles.length) text += "    │   Non-trump doubles: [" + lc.nonTrumpDoubles.join(", ") + "]\\n";
          if(lc.nonTrumpSingles.length) text += "    │   Non-trump singles: [" + lc.nonTrumpSingles.join(", ") + "]\\n";
        }

        // Lead candidates (danger scoring)
        if(d.leadCandidates && d.leadCandidates.length > 0){
          text += "    │\\n";
          text += "    │ LEAD CANDIDATE SCORES (danger scoring):\\n";
          const sorted = [...d.leadCandidates].sort((a,b) => b.totalScore - a.totalScore);
          for(const c of sorted){
            text += "    │   " + c.tile + " (suit " + c.suit + "): SCORE=" + c.totalScore;
            if(c.count) text += " [count=" + c.count + "pts]";
            text += "\\n";
            const bk = c.breakdown;
            const parts = [];
            if(bk.doubleNotOut !== undefined) parts.push("dbl-not-out=" + bk.doubleNotOut);
            if(bk.doubleOut !== undefined) parts.push("dbl-out=+" + bk.doubleOut);
            if(bk.doubleCountPenalty) parts.push("dbl-count=" + bk.doubleCountPenalty);
            if(bk.myCountPenalty) parts.push("my-count=" + bk.myCountPenalty);
            if(bk.suitCountRisk) parts.push("suit-risk=" + bk.suitCountRisk);
            if(bk.suitCountBonus) parts.push("suit-bonus=+" + bk.suitCountBonus);
            if(bk.tilesLeftPenalty) parts.push("tiles-left=" + bk.tilesLeftPenalty);
            if(bk.oppVoidTrumpRisk) parts.push("opp-trump-risk=" + bk.oppVoidTrumpRisk);
            if(bk.oppVoidSafe) parts.push("opp-safe=+" + bk.oppVoidSafe);
            parts.push("pip=" + bk.pipPenalty);
            parts.push("sum=" + bk.sumPenalty);
            if(parts.length) text += "    │     → " + parts.join(", ") + "\\n";
          }
        }

        // Follow suit debug
        if(d.followSuit){
          const fs = d.followSuit;
          text += "    │\\n";
          text += "    │ FOLLOW SUIT: led pip=" + fs.ledPip;
          text += " | winner=P" + fs.currentWinnerSeat + " (rank " + fs.winnerRank + (fs.winnerIsTrump ? " TRUMP" : "") + ")\\n";
          text += "    │   Can beat winner: " + fs.canBeat + "\\n";
          for(const c of fs.candidates){
            text += "    │   " + c.tile + ": rank=" + c.rank + (c.isDouble ? " (DOUBLE)" : "") + "\\n";
          }
        }

        // Trump-in debug
        if(d.trumpIn){
          const ti = d.trumpIn;
          text += "    │\\n";
          text += "    │ TRUMP IN: highest in trick=" + ti.highestTrickTrump;
          text += " | opp trumped=" + ti.oppHasTrump + " | partner trumped=" + ti.partnerHasTrump + "\\n";
          for(const c of ti.candidates){
            text += "    │   " + c.tile + ": rank=" + c.rank + (c.canWin ? " (WINS)" : " (loses)") + "\\n";
          }
        }

        // Dump candidates
        if(d.dumpCandidates && d.dumpCandidates.length > 0){
          text += "    │\\n";
          text += "    │ DUMP CANDIDATE SCORES:\\n";
          const sorted = [...d.dumpCandidates].sort((a,b) => b.totalScore - a.totalScore);
          for(const c of sorted){
            text += "    │   " + c.tile + ": SCORE=" + c.totalScore;
            if(c.count) text += " [count=" + c.count + "pts]";
            text += "\\n";
            const bk = c.breakdown;
            const parts = [];
            if(bk.voidBonus) parts.push("void=+" + bk.voidBonus);
            if(bk.suitCounts) parts.push("suits=" + bk.suitCounts);
            if(bk.countPenalty) parts.push("count=" + bk.countPenalty);
            parts.push("sum=" + bk.sumPenalty);
            if(bk.trumpPenalty) parts.push("trump=" + bk.trumpPenalty);
            if(bk.lastTrumpPenalty) parts.push("last-trump=" + bk.lastTrumpPenalty);
            if(parts.length) text += "    │     → " + parts.join(", ") + "\\n";
          }
        }

        text += "    └─────────────────────\\n";
      }
    }
    else if(entry.type === "TRICK_END"){
      text += "  >> Winner: P" + seatToPlayer(entry.winnerSeat) + " (Team " + entry.winnerTeam + ") +" + entry.pointsInTrick + " pts\\n";
      text += "  >> " + entry.playsString + "\\n";
    }
    else if(entry.type === "HAND_END"){
      const scores = entry.finalScores || {};
      text += "\\n  ====== HAND " + (entry.handId + 1) + " RESULT ======\\n";
      text += "  Final: Team1=" + (scores.team1||0) + " Team2=" + (scores.team2||0) + "\\n";
      text += "  " + (entry.winner || "") + "\\n";
      text += "  Bid made: " + (entry.bidMade ? "Yes" : "No") + "\\n";
    }
  }

  return text || 'No log entries yet.';
}

document.getElementById('menuGameLog').addEventListener('click', () => {
  document.getElementById('settingsMenu').classList.remove('open');
  document.getElementById('gameLogContent').textContent = formatGameLog() || 'No log entries yet.';
  document.getElementById('gameLogBackdrop').style.display = 'flex';
});"""

if old_format_end not in html:
    print("ERROR: Could not find menuGameLog click handler")
    sys.exit(1)
html = html.replace(old_format_end, new_format_end, 1)
print("Added formatAdvancedLog function")

# ============================================================
# PATCH 4: Add UI elements — Advanced Log button in menu + modal
# ============================================================

# Add menu item after Game Log
old_menu_gamelog = '  <div class="settingsItem" id="menuGameLog">Game Log</div>'

if old_menu_gamelog not in html:
    print("ERROR: Could not find Game Log menu item")
    sys.exit(1)

new_menu_gamelog = old_menu_gamelog + '\n  <div class="settingsItem" id="menuAdvancedLog">Advanced AI Log</div>'

html = html.replace(old_menu_gamelog, new_menu_gamelog, 1)
print("Added Advanced AI Log menu item")

# Add the advanced log modal HTML (after the game log modal)
old_gamelog_modal_end = """<button id="gameLogCopyBtn" style="width:100%;padding:10px;background:rgba(59,130,246,0.8);border:none;border-radius:8px;color:#fff;font-weight:600;cursor:pointer;">Copy Log to Clipboard</button>"""

new_gamelog_modal_end = old_gamelog_modal_end + """
    </div>
  </div>
</div>
<div class="modalBackdrop" id="advLogBackdrop" style="display:none;">
  <div class="modalBody" style="max-width:720px;width:95vw;">
    <div class="modalInner">
      <button class="modalCloseBtn" id="advLogCloseBtn">&times;</button>
      <h3 style="color:#fff;margin-bottom:10px;">Advanced AI Debug Log</h3>
      <p style="font-size:11px;color:rgba(255,255,255,0.6);margin-bottom:10px;">Full AI reasoning for every play. Copy and share for analysis.</p>
      <pre id="advLogContent" style="font-size:10px;white-space:pre-wrap;word-break:break-word;color:rgba(255,255,255,0.9);max-height:60vh;overflow-y:auto;"></pre>
      <div style="display:flex;gap:8px;margin-top:10px;">
        <button id="advLogCopyBtn" style="flex:1;padding:10px;background:rgba(59,130,246,0.8);border:none;border-radius:8px;color:#fff;font-weight:600;cursor:pointer;">Copy to Clipboard</button>
        <button id="advLogDownloadBtn" style="flex:1;padding:10px;background:rgba(34,197,94,0.8);border:none;border-radius:8px;color:#fff;font-weight:600;cursor:pointer;">Download .txt</button>
      </div>"""

# But we need to be careful not to duplicate the closing tags.
# The existing modal structure likely has </div></div></div> after the copy button.
# Let's just add the new modal AFTER the entire game log modal backdrop.

# Actually let's find the game log backdrop end tag more precisely
old_gamelog_backdrop_end = """document.getElementById('gameLogCloseBtn').addEventListener('click', () => {
  document.getElementById('gameLogBackdrop').style.display = 'none';
});

document.getElementById('gameLogCopyBtn').addEventListener('click', () => {
  const text = formatGameLog();
  navigator.clipboard.writeText(text).then(() => {
    document.getElementById('gameLogCopyBtn').textContent = 'Copied!';
    setTimeout(() => {
      document.getElementById('gameLogCopyBtn').textContent = 'Copy Log to Clipboard';
    }, 1500);
  }).catch(e => {
    console.error('Copy failed:', e);
  });
});"""

new_gamelog_backdrop_end = old_gamelog_backdrop_end + """

// Advanced AI Log handlers
document.getElementById('menuAdvancedLog').addEventListener('click', () => {
  document.getElementById('settingsMenu').classList.remove('open');
  document.getElementById('advLogContent').textContent = formatAdvancedLog() || 'No log entries yet.';
  document.getElementById('advLogBackdrop').style.display = 'flex';
});

document.getElementById('advLogCloseBtn').addEventListener('click', () => {
  document.getElementById('advLogBackdrop').style.display = 'none';
});

document.getElementById('advLogCopyBtn').addEventListener('click', () => {
  const text = formatAdvancedLog();
  navigator.clipboard.writeText(text).then(() => {
    document.getElementById('advLogCopyBtn').textContent = 'Copied!';
    setTimeout(() => {
      document.getElementById('advLogCopyBtn').textContent = 'Copy to Clipboard';
    }, 1500);
  }).catch(e => {
    console.error('Copy failed:', e);
  });
});

document.getElementById('advLogDownloadBtn').addEventListener('click', () => {
  const text = formatAdvancedLog();
  const blob = new Blob([text], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'tn51_ai_debug_' + new Date().toISOString().slice(0,10) + '.txt';
  a.click();
  URL.revokeObjectURL(url);
});"""

if old_gamelog_backdrop_end not in html:
    print("ERROR: Could not find gameLog event handlers")
    sys.exit(1)
html = html.replace(old_gamelog_backdrop_end, new_gamelog_backdrop_end, 1)
print("Added Advanced Log event handlers")

# Now add the advanced log modal HTML. Find the game log modal and add after it.
# Let's find the closing of the gameLogBackdrop div
old_modal_html = """<button id="gameLogCopyBtn" style="width:100%;padding:10px;background:rgba(59,130,246,0.8);border:none;border-radius:8px;color:#fff;font-weight:600;cursor:pointer;">Copy Log to Clipboard</button>
    </div>
  </div>
</div>"""

new_modal_html = """<button id="gameLogCopyBtn" style="width:100%;padding:10px;background:rgba(59,130,246,0.8);border:none;border-radius:8px;color:#fff;font-weight:600;cursor:pointer;">Copy Log to Clipboard</button>
    </div>
  </div>
</div>

<div class="modalBackdrop" id="advLogBackdrop" style="display:none;">
  <div class="modalBody" style="max-width:720px;width:95vw;">
    <div class="modalInner">
      <button class="modalCloseBtn" id="advLogCloseBtn">&times;</button>
      <h3 style="color:#fff;margin-bottom:10px;">Advanced AI Debug Log</h3>
      <p style="font-size:11px;color:rgba(255,255,255,0.6);margin-bottom:10px;">Full AI reasoning for every play. Copy and share for analysis.</p>
      <pre id="advLogContent" style="font-size:10px;white-space:pre-wrap;word-break:break-word;color:rgba(255,255,255,0.9);max-height:60vh;overflow-y:auto;"></pre>
      <div style="display:flex;gap:8px;margin-top:10px;">
        <button id="advLogCopyBtn" style="flex:1;padding:10px;background:rgba(59,130,246,0.8);border:none;border-radius:8px;color:#fff;font-weight:600;cursor:pointer;">Copy to Clipboard</button>
        <button id="advLogDownloadBtn" style="flex:1;padding:10px;background:rgba(34,197,94,0.8);border:none;border-radius:8px;color:#fff;font-weight:600;cursor:pointer;">Download .txt</button>
      </div>
    </div>
  </div>
</div>"""

if old_modal_html not in html:
    print("ERROR: Could not find game log modal closing HTML")
    sys.exit(1)
html = html.replace(old_modal_html, new_modal_html, 1)
print("Added Advanced Log modal HTML")

# ============================================================
# Final verification
# ============================================================

checks = [
    ("formatAdvancedLog", "Advanced log formatter"),
    ("advLogBackdrop", "Advanced log modal"),
    ("menuAdvancedLog", "Advanced log menu item"),
    ("_dbg.enabled", "Debug collector"),
    ("aiDebug:", "Debug in log entries"),
    ("AI REASONING", "Advanced log output"),
    ("advLogDownloadBtn", "Download button"),
]

all_ok = True
for pattern, desc in checks:
    if pattern not in html:
        print(f"ERROR: Missing {desc} ({pattern})")
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
print(f"\nSource: {src_size:,} bytes")
print(f"Output: {dst_size:,} bytes")
print(f"Delta:  {dst_size - src_size:+,} bytes")
print(f"Written to: {DST}")
print("SUCCESS!")
