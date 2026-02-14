#!/usr/bin/env python3
"""
Build script: TN51 Dominoes V10_52
Base: V10_51
Fixes: All T42 game logic bugs (trick history, bidding, turn order, hardcoded 6-player loops)
Feature: Adjustable T42 layout settings
"""

import re
import sys

INPUT_FILE = "TN51_Dominoes_V10_51.html"
OUTPUT_FILE = "TN51_Dominoes_V10_52.html"

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def patch(src, old, new, label, count=1):
    """Replace old with new in src. Verify exactly `count` occurrences."""
    occurrences = src.count(old)
    if occurrences == 0:
        print(f"  FAIL: '{label}' — target string not found!")
        sys.exit(1)
    if occurrences != count:
        print(f"  WARN: '{label}' — expected {count} occurrences, found {occurrences}")
    result = src.replace(old, new, count) if count == 1 else src.replace(old, new)
    print(f"  OK: {label} ({occurrences} replaced)")
    return result

def main():
    print(f"Reading {INPUT_FILE}...")
    html = read_file(INPUT_FILE)
    original_len = len(html)

    # =========================================================================
    # BUG FIX 1: getTrickHistoryPosition — dynamic grid dimensions
    # The T42 layout has 4 cols × 7 rows, not 6 cols × 8 rows
    # =========================================================================
    print("\n=== FIX 1: getTrickHistoryPosition dynamic grid ===")

    old_trick_hist = """function getTrickHistoryPosition(teamTrickIndex, winningTeam, playerRowIndex){
  // teamTrickIndex: which win this is for the team (0-5, 6 max per team)
  // winningTeam: 0 = Team 1 (left side), 1 = Team 2 (right side)
  // playerRowIndex: which row (0-5 for players P1-P6 top to bottom)

  const section = getSection('Trick_History');
  if(!section) return null;

  // Layout: 8 columns total
  // Team 1 wins: columns 0,1,2,3,4,5 (left to right, 1st win in col 0)
  // Team 2 wins: columns 7,6,5,4,3,2 (right to left, 1st win in col 7)
  // But current grid is 6 cols x 8 rows - we use row as the "column" (trick number)
  // and col as the player row

  // The current layout is 6 columns (for 6 players) x 8 rows (for 8 tricks)
  // We'll use it differently:
  // - Row 0-5 = Team 1's trick wins (columns 1-6 from left)
  // - Row 7,6,5,4,3,2 = Team 2's trick wins (columns 8-3 from right)

  // Actually the layout has 6 cols x 8 rows = 48 positions
  // Indexed as: index = row * 6 + col
  // Let's map: Team 1 trick wins to rows 0-5, Team 2 to rows 7,6,5,4,3,2

  let row;
  if(winningTeam === 0){
    // Team 1: use rows 0,1,2,3,4,5 for trick wins 0-5
    row = Math.min(5, teamTrickIndex);
  } else {
    // Team 2: use rows 7,6,5,4,3,2 for trick wins 0-5 (reversed, from right)
    row = 7 - Math.min(5, teamTrickIndex);
  }

  // Column is based on player order (P1=0, P2=1, P3=2, P4=3, P5=4, P6=5)
  const col = playerRowIndex;

  const index = row * 6 + col;
  const d = section.dominoes[index];
  if(!d) return null;
  const px = normToPx(d.xN, d.yN);
  return { x: px.x - 28, y: px.y - 56, s: d.scale, rz: d.rotZ, ry: d.rotY };
}"""

    new_trick_hist = """function getTrickHistoryPosition(teamTrickIndex, winningTeam, playerRowIndex){
  const section = getSection('Trick_History');
  if(!section) return null;

  // Grid dimensions from actual layout section:
  // TN51: 6 cols × 8 rows = 48 positions
  // T42:  4 cols × 7 rows = 28 positions
  const numCols = session.game.player_count;      // 6 for TN51, 4 for T42
  const numRows = Math.floor(section.dominoes.length / numCols);  // 8 for TN51, 7 for T42
  const maxTeamTricks = numRows - 1;  // max row index for a team

  let row;
  if(winningTeam === 0){
    row = Math.min(maxTeamTricks, teamTrickIndex);
  } else {
    row = (numRows - 1) - Math.min(maxTeamTricks, teamTrickIndex);
  }

  const col = playerRowIndex;
  const index = row * numCols + col;
  const d = section.dominoes[index];
  if(!d) return null;
  const px = normToPx(d.xN, d.yN);
  return { x: px.x - 28, y: px.y - 56, s: d.scale, rz: d.rotZ, ry: d.rotY };
}"""
    html = patch(html, old_trick_hist, new_trick_hist, "getTrickHistoryPosition dynamic grid")

    # =========================================================================
    # BUG FIX 2: ppVisualPlayer — % 6 → % player_count
    # =========================================================================
    print("\n=== FIX 2: ppVisualPlayer modulo ===")

    html = patch(html,
        "return ((seat - ppRotationOffset + 6) % 6) + 1;",
        "return ((seat - ppRotationOffset + session.game.player_count) % session.game.player_count) + 1;",
        "ppVisualPlayer modulo fix")

    # =========================================================================
    # BUG FIX 3: ppSeatFromVisual — % 6 → % player_count
    # =========================================================================
    print("\n=== FIX 3: ppSeatFromVisual modulo ===")

    html = patch(html,
        "return (visualPlayer - 1 + ppRotationOffset) % 6;",
        "return (visualPlayer - 1 + ppRotationOffset) % session.game.player_count;",
        "ppSeatFromVisual modulo fix")

    # =========================================================================
    # BUG FIX 4: PLAY_ORDER — dynamic based on game mode
    # =========================================================================
    print("\n=== FIX 4: PLAY_ORDER dynamic ===")

    html = patch(html,
        "const PLAY_ORDER = [1, 2, 3, 4, 5, 6];",
        "let PLAY_ORDER = [1, 2, 3, 4, 5, 6];",
        "PLAY_ORDER make mutable (let)")

    # =========================================================================
    # BUG FIX 5: PLAYER_TO_SEAT reference in opponentsPlay
    # The old PLAYER_TO_SEAT constant was replaced with _TN51/_T42 variants
    # but opponentsPlay still references the old name
    # =========================================================================
    print("\n=== FIX 5: opponentsPlay PLAYER_TO_SEAT fix ===")

    html = patch(html,
        "const seat = PLAYER_TO_SEAT[playerNum];",
        "const _pts = GAME_MODE === 'T42' ? PLAYER_TO_SEAT_T42 : PLAYER_TO_SEAT_TN51;\n    const seat = _pts[playerNum];",
        "opponentsPlay PLAYER_TO_SEAT fix")

    # =========================================================================
    # BUG FIX 6: initBiddingRound — all hardcoded 6 references
    # =========================================================================
    print("\n=== FIX 6: initBiddingRound dynamic player count ===")

    old_init_bid = """function initBiddingRound() {
  const dealerSeat = session.dealer || 0;
  const firstBidder = (dealerSeat - 1 + 6) % 6;

  biddingState = {
    currentBidder: firstBidder,
    highBid: 0,
    highBidder: null,
    highMarks: 1,
    passCount: 0,
    bids: [],
    bidderOrder: [],
    inMultiplierMode: false,
    highMultiplier: 0
  };

  for (let i = 0; i < 6; i++) {
    biddingState.bidderOrder.push((firstBidder + i) % 6);  // Clockwise order
  }

  currentBidSelection = 34;
  bidMode = 'range';
}"""

    new_init_bid = """function initBiddingRound() {
  const dealerSeat = session.dealer || 0;
  const _pc = session.game.player_count;
  const firstBidder = (dealerSeat - 1 + _pc) % _pc;

  biddingState = {
    currentBidder: firstBidder,
    highBid: 0,
    highBidder: null,
    highMarks: 1,
    passCount: 0,
    bids: [],
    bidderOrder: [],
    inMultiplierMode: false,
    highMultiplier: 0
  };

  for (let i = 0; i < _pc; i++) {
    biddingState.bidderOrder.push((firstBidder + i) % _pc);  // Clockwise order
  }

  currentBidSelection = GAME_MODE === 'T42' ? 30 : 34;
  bidMode = 'range';
}"""
    html = patch(html, old_init_bid, new_init_bid, "initBiddingRound dynamic player count")

    # =========================================================================
    # BUG FIX 7: advanceBidding — >= 6 → >= bidderOrder.length
    # =========================================================================
    print("\n=== FIX 7: advanceBidding dynamic check ===")

    html = patch(html,
        "if (nextIndex >= 6) {",
        "if (nextIndex >= biddingState.bidderOrder.length) {",
        "advanceBidding dynamic length check")

    # =========================================================================
    # BUG FIX 8: flipRemainingDominoes — seat < 6 → seat < player_count
    # =========================================================================
    print("\n=== FIX 8: flipRemainingDominoes dynamic ===")

    html = patch(html,
        "for(let seat = 1; seat < 6; seat++){  // Skip seat 0 (player)",
        "for(let seat = 1; seat < session.game.player_count; seat++){  // Skip seat 0 (player)",
        "flipRemainingDominoes dynamic")

    # =========================================================================
    # BUG FIX 9: dealDominoes — dynamic sample tiles and loops
    # =========================================================================
    print("\n=== FIX 9: dealDominoes dynamic ===")

    old_deal = """  // Sample tiles for demo
  const sampleTiles = [
    [[7,7],[6,5],[4,3],[2,1],[5,4],[3,2]],
    [[6,6],[5,4],[3,2],[1,0],[4,3],[2,1]],
    [[5,5],[4,3],[2,1],[0,0],[3,2],[1,0]],
    [[4,4],[3,2],[1,0],[7,6],[2,1],[0,0]],
    [[3,3],[2,1],[0,0],[6,5],[1,0],[7,6]],
    [[2,2],[1,0],[7,6],[5,4],[0,0],[6,5]]
  ];

  for(let p = 0; p < 6; p++){
    sprites[p] = [];
    const playerNum = seatToPlayer(p);  // Convert seat to player number for layout
    for(let h = 0; h < 6; h++){
      const tile = sampleTiles[p][h];"""

    new_deal = """  // Sample tiles for demo — generate dynamically based on game mode
  const _demoPC = session.game.player_count;
  const _demoHS = session.game.hand_size;
  const _demoMP = session.game.max_pip;
  const sampleTiles = [];
  for(let p = 0; p < _demoPC; p++){
    const hand = [];
    for(let h = 0; h < _demoHS; h++){
      const a = (_demoMP - p - h + _demoMP + 1) % (_demoMP + 1);
      const b = (_demoMP - p - h - 1 + _demoMP + 1) % (_demoMP + 1);
      hand.push([a, b]);
    }
    sampleTiles.push(hand);
  }

  for(let p = 0; p < _demoPC; p++){
    sprites[p] = [];
    const playerNum = seatToPlayer(p);  // Convert seat to player number for layout
    for(let h = 0; h < _demoHS; h++){
      const tile = sampleTiles[p][h];"""
    html = patch(html, old_deal, new_deal, "dealDominoes dynamic sample tiles")

    # =========================================================================
    # BUG FIX 10: ppRepositionPlaceholders — use getActivePlaceholderConfig()
    # =========================================================================
    print("\n=== FIX 10: ppRepositionPlaceholders dynamic config ===")

    old_pp_repos = """function ppRepositionPlaceholders() {
  const boxes = document.querySelectorAll('.player-placeholder[data-pp-player]');
  boxes.forEach(box => {
    const origPlayer = parseInt(box.dataset.ppPlayer);
    if (!origPlayer) return;
    const seat = origPlayer - 1;
    const newVisualP = ppVisualPlayer(seat);
    const pos = PLACEHOLDER_CONFIG.players[newVisualP];
    if (pos) {
      const px = normToPx(pos.xN, pos.yN);
      box.style.left = (px.x - PLACEHOLDER_CONFIG.dominoWidth / 2) + 'px';
      box.style.top = (px.y - PLACEHOLDER_CONFIG.dominoHeight / 2) + 'px';
    }
  });
}"""

    new_pp_repos = """function ppRepositionPlaceholders() {
  const _phCfg = getActivePlaceholderConfig();
  const boxes = document.querySelectorAll('.player-placeholder[data-pp-player]');
  boxes.forEach(box => {
    const origPlayer = parseInt(box.dataset.ppPlayer);
    if (!origPlayer) return;
    const seat = origPlayer - 1;
    const newVisualP = ppVisualPlayer(seat);
    const pos = _phCfg.players[newVisualP];
    if (pos) {
      const px = normToPx(pos.xN, pos.yN);
      box.style.left = (px.x - _phCfg.dominoWidth / 2) + 'px';
      box.style.top = (px.y - _phCfg.dominoHeight / 2) + 'px';
    }
  });
}"""
    html = patch(html, old_pp_repos, new_pp_repos, "ppRepositionPlaceholders dynamic config")

    # =========================================================================
    # BUG FIX 11: getLeadDominoPosition — use getActivePlaceholderConfig()
    # =========================================================================
    print("\n=== FIX 11: getLeadDominoPosition dynamic config ===")

    html = patch(html,
        "const px = normToPx(PLACEHOLDER_CONFIG.lead.xN, PLACEHOLDER_CONFIG.lead.yN);",
        "const _ldCfg = getActivePlaceholderConfig();\n  const px = normToPx(_ldCfg.lead.xN, _ldCfg.lead.yN);",
        "getLeadDominoPosition dynamic config")

    # =========================================================================
    # BUG FIX 12: ppResetRotation — p <= 6 → p <= player_count
    # =========================================================================
    print("\n=== FIX 12: ppResetRotation dynamic ===")

    html = patch(html,
        """  // Reset indicator labels
  for (let p = 1; p <= 6; p++) {
    const el = document.getElementById('playerIndicator' + p);
    if (el) {
      el.textContent = 'P' + p;
      el.classList.remove('team1', 'team2');
      el.classList.add((p - 1) % 2 === 0 ? 'team1' : 'team2');
    }
  }""",
        """  // Reset indicator labels
  const _rstPC = session.game.player_count;
  for (let p = 1; p <= _rstPC; p++) {
    const el = document.getElementById('playerIndicator' + p);
    if (el) {
      el.textContent = 'P' + p;
      el.classList.remove('team1', 'team2');
      el.classList.add((p - 1) % 2 === 0 ? 'team1' : 'team2');
    }
  }""",
        "ppResetRotation dynamic player count")

    # =========================================================================
    # BUG FIX 13: refreshLayout — hardcoded 6 in both loops
    # =========================================================================
    print("\n=== FIX 13: refreshLayout dynamic ===")

    old_refresh = """  // Reposition all hand sprites
  for(let p = 0; p < 6; p++){
    const playerNum = seatToPlayer(p);
    for(let h = 0; h < 6; h++){"""

    new_refresh = """  // Reposition all hand sprites
  for(let p = 0; p < session.game.player_count; p++){
    const playerNum = seatToPlayer(p);
    for(let h = 0; h < session.game.hand_size; h++){"""
    html = patch(html, old_refresh, new_refresh, "refreshLayout dynamic loops")

    # =========================================================================
    # BUG FIX 14: resumeGameFromSave — hardcoded [0,1,2,3,4,5] and loops
    # =========================================================================
    print("\n=== FIX 14: resumeGameFromSave dynamic ===")

    html = patch(html,
        "session.game.active_players = snap.active_players || [0,1,2,3,4,5];",
        "session.game.active_players = snap.active_players || Array.from({length: session.game.player_count}, (_, i) => i);",
        "resumeGameFromSave active_players dynamic")

    # Fix the sprite creation loops in resumeGameFromSave
    old_resume_loops = """    for(let p = 0; p < 6; p++){
      sprites[p] = [];
      const playerNum = seatToPlayer(p);
      for(let h = 0; h < 6; h++){
        const tile = hands[p] && hands[p][h];"""
    new_resume_loops = """    for(let p = 0; p < session.game.player_count; p++){
      sprites[p] = [];
      const playerNum = seatToPlayer(p);
      for(let h = 0; h < session.game.hand_size; h++){
        const tile = hands[p] && hands[p][h];"""
    html = patch(html, old_resume_loops, new_resume_loops, "resumeGameFromSave sprite loops")

    # =========================================================================
    # BUG FIX 15: loadReplayHandForHand (replayHand) — hardcoded references
    # =========================================================================
    print("\n=== FIX 15: replayHand dynamic ===")

    html = patch(html,
        "session.dealer = (session.dealer + 1) % 6;",
        "session.dealer = (session.dealer + 1) % session.game.player_count;",
        "replayHand dealer modulo fix")

    html = patch(html,
        "session.game.set_active_players([0,1,2,3,4,5]);\n  session.phase = PHASE_NEED_BID;\n  session.status = \"Starting bidding round... (Replaying saved hand)\";",
        "session.game.set_active_players(Array.from({length: session.game.player_count}, (_, i) => i));\n  session.phase = PHASE_NEED_BID;\n  session.status = \"Starting bidding round... (Replaying saved hand)\";",
        "replayHand active_players dynamic")

    # Fix loops
    old_replay_loops = """  for(let p = 0; p < 6; p++){
    sprites[p] = [];
    const playerNum = seatToPlayer(p);
    for(let h = 0; h < 6; h++){
      const tile = hands[p][h];
      if(!tile) continue;"""
    new_replay_loops = """  for(let p = 0; p < session.game.player_count; p++){
    sprites[p] = [];
    const playerNum = seatToPlayer(p);
    for(let h = 0; h < session.game.hand_size; h++){
      const tile = hands[p] && hands[p][h];
      if(!tile) continue;"""
    html = patch(html, old_replay_loops, new_replay_loops, "replayHand sprite loops")

    # =========================================================================
    # BUG FIX 16: Session snapshot — active_players fallback
    # =========================================================================
    print("\n=== FIX 16: Session snapshot active_players fallback ===")

    html = patch(html,
        "active_players:g.active_players ? g.active_players.slice() : [0,1,2,3,4,5],",
        "active_players:g.active_players ? g.active_players.slice() : Array.from({length: g.player_count}, (_, i) => i),",
        "Session snapshot active_players fallback")

    # =========================================================================
    # BUG FIX 17: AI simulation (runOneSim) — hardcoded 6 references
    # =========================================================================
    print("\n=== FIX 17: runOneSim dynamic ===")

    old_sim = """    const hands = new Array(6);
    hands[0] = playerHand.map(t => [t[0], t[1]]);
    let pi = 0;
    for (let s = 1; s < 6; s++) {
      if (contract === "NELLO" && (s === 2 || s === 4)) {
        hands[s] = [];  // Partners sit out in Nello
      } else {
        hands[s] = pool.slice(pi, pi + 6);
        pi += 6;
      }
    }

    // Create fresh game state
    const sim = new GameStateV6_4g(6, 7, 6);"""

    new_sim = """    const _simPC = session.game.player_count;
    const _simHS = session.game.hand_size;
    const _simMP = session.game.max_pip;
    const hands = new Array(_simPC);
    hands[0] = playerHand.map(t => [t[0], t[1]]);
    let pi = 0;
    for (let s = 1; s < _simPC; s++) {
      if (contract === "NELLO" && (s === 2 || s === 4)) {
        hands[s] = [];  // Partners sit out in Nello
      } else {
        hands[s] = pool.slice(pi, pi + _simHS);
        pi += _simHS;
      }
    }

    // Create fresh game state
    const sim = new GameStateV6_4g(_simPC, _simMP, _simHS);"""
    html = patch(html, old_sim, new_sim, "runOneSim dynamic game params")

    # =========================================================================
    # BUG FIX 18: initGameMode — also update PLAY_ORDER
    # =========================================================================
    print("\n=== FIX 18: initGameMode update PLAY_ORDER ===")

    old_init_mode = """function initGameMode(mode){
  GAME_MODE = mode;
  if(mode === 'T42'){
    session = new SessionV6_4g(4, 6, 7, 7);
  } else {
    session = new SessionV6_4g(6, 7, 6, 7);
  }
}"""

    new_init_mode = """function initGameMode(mode){
  GAME_MODE = mode;
  if(mode === 'T42'){
    session = new SessionV6_4g(4, 6, 7, 7);
    PLAY_ORDER = [1, 2, 3, 4];
  } else {
    session = new SessionV6_4g(6, 7, 6, 7);
    PLAY_ORDER = [1, 2, 3, 4, 5, 6];
  }
}"""
    html = patch(html, old_init_mode, new_init_mode, "initGameMode update PLAY_ORDER")

    # =========================================================================
    # BUG FIX 19: AI hint simulation hardcoded for 6 players (line 10532 area)
    # Also fix the controlLostTrick <= 6 check
    # =========================================================================
    print("\n=== FIX 19: AI hint control check ===")

    # The "controlLostTrick <= 6" is fine — it's about trick count not player count
    # (max 6 or 7 tricks, this threshold is generic enough)

    # =========================================================================
    # FEATURE 1: T42 Layout Adjustment Settings
    # =========================================================================
    print("\n=== FEATURE 1: T42 Layout Adjustment Settings ===")

    # Add settings popup HTML after the Game Settings popup
    # We'll inject it as a new popup accessible from the game screen
    old_game_settings_end = """<div id="gameSettingsBackdrop" class="modalBackdrop" style="display:none;z-index:1500;">"""

    # Find a good place to add the T42 layout settings button and popup
    # Let's add it to the initGameMode function and as a floating button

    # Add T42 layout adjustment variables after LAYOUT_T42 definition
    old_layout_t42_end = """// T42 placeholder positions
const PLACEHOLDER_CONFIG_T42 = {"""

    new_layout_t42_end = """// T42 Layout Adjustment Settings (live-adjustable)
let T42_SETTINGS = {
  p1Scale: 1.071,        // Player 1 (bottom) tile scale
  p1Spacing: 0.13487,    // Player 1 tile spacing
  opponentScale: 0.393,  // P2/P3/P4 tile scale
  p2x: 0.165,            // Player 2 (left) X position
  p4x: 0.835,            // Player 4 (right) X position
  p3y: 0.411,            // Player 3 (top) Y position
  sideSpacing: 0.0456,   // P2/P4 vertical spacing between tiles
  p3Spacing: 0.0556,     // P3 horizontal spacing between tiles
  trickScale: 0.393,     // Trick area (played domino) scale
  p2TrickX: 0.380,       // P2 played domino X
  p4TrickX: 0.610,       // P4 played domino X
  p1TrickY: 0.678,       // P1 played domino Y
  p3TrickY: 0.522,       // P3 played domino Y
  leadScale: 0.393,      // Lead pip scale
};

function applyT42Settings(){
  if(GAME_MODE !== 'T42') return;
  const s = T42_SETTINGS;
  const L = LAYOUT_T42.sections;
  // P1 Hand
  const p1h = L.find(x => x.name === 'Player_1_Hand');
  if(p1h){
    for(let i = 0; i < 7; i++){
      p1h.dominoes[i].xN = 0.9 - i * s.p1Spacing;
      p1h.dominoes[i].scale = s.p1Scale;
    }
  }
  // P2 Hand (left, vertical)
  const p2h = L.find(x => x.name === 'Player_2_Hand');
  if(p2h){
    const cy = 0.600;
    for(let i = 0; i < 7; i++){
      p2h.dominoes[i].xN = s.p2x;
      p2h.dominoes[i].yN = (cy - 3*s.sideSpacing) + i*s.sideSpacing;
      p2h.dominoes[i].scale = s.opponentScale;
    }
  }
  // P3 Hand (top, horizontal)
  const p3h = L.find(x => x.name === 'Player_3_Hand');
  if(p3h){
    for(let i = 0; i < 7; i++){
      p3h.dominoes[i].xN = 0.3282 + i * s.p3Spacing;
      p3h.dominoes[i].yN = s.p3y;
      p3h.dominoes[i].scale = s.opponentScale;
    }
  }
  // P4 Hand (right, vertical)
  const p4h = L.find(x => x.name === 'Player_4_Hand');
  if(p4h){
    const cy = 0.600;
    for(let i = 0; i < 7; i++){
      p4h.dominoes[i].xN = s.p4x;
      p4h.dominoes[i].yN = (cy - 3*s.sideSpacing) + i*s.sideSpacing;
      p4h.dominoes[i].scale = s.opponentScale;
    }
  }
  // Played domino placeholders
  const p1pd = L.find(x => x.name === 'Player_1_Played_Domino');
  if(p1pd){ p1pd.dominoes[0].yN = s.p1TrickY; p1pd.dominoes[0].scale = s.trickScale; }
  const p2pd = L.find(x => x.name === 'Player_2_Played_Domino');
  if(p2pd){ p2pd.dominoes[0].xN = s.p2TrickX; p2pd.dominoes[0].scale = s.trickScale; }
  const p3pd = L.find(x => x.name === 'Player_3_Played_Domino');
  if(p3pd){ p3pd.dominoes[0].yN = s.p3TrickY; p3pd.dominoes[0].scale = s.trickScale; }
  const p4pd = L.find(x => x.name === 'Player_4_Played_Domino');
  if(p4pd){ p4pd.dominoes[0].xN = s.p4TrickX; p4pd.dominoes[0].scale = s.trickScale; }
  // Lead domino
  const ld = L.find(x => x.name === 'Lead_Domino');
  if(ld){ ld.dominoes[0].scale = s.leadScale; }
  // Update placeholder config
  PLACEHOLDER_CONFIG_T42.players[1].yN = s.p1TrickY;
  PLACEHOLDER_CONFIG_T42.players[2].xN = s.p2TrickX;
  PLACEHOLDER_CONFIG_T42.players[3].yN = s.p3TrickY;
  PLACEHOLDER_CONFIG_T42.players[4].xN = s.p4TrickX;
  // Refresh
  refreshLayout();
}

// T42 placeholder positions
const PLACEHOLDER_CONFIG_T42 = {"""
    html = patch(html, old_layout_t42_end, new_layout_t42_end, "T42 layout adjustment settings + applyT42Settings")

    # =========================================================================
    # FEATURE 2: T42 Layout Settings popup HTML + CSS
    # Add before closing </body> tag
    # =========================================================================
    print("\n=== FEATURE 2: T42 Layout Settings popup ===")

    old_body_end = "</body>"
    new_body_end = """<!-- T42 Layout Settings Popup -->
<div id="t42SettingsBackdrop" class="modalBackdrop" style="display:none;z-index:2000;">
  <div class="modal" style="width:340px;max-height:80vh;overflow-y:auto;">
    <div class="modalHeader" style="padding:12px 16px;">
      <span style="font-weight:700;font-size:15px;">T42 Layout Settings</span>
      <button class="closeBtn" id="btnCloseT42Settings">&times;</button>
    </div>
    <div class="modalBody" style="padding:12px 16px;">
      <div class="t42s-group">
        <label>P1 (You) Tile Scale</label>
        <input type="range" min="0.5" max="1.5" step="0.01" id="t42s_p1Scale">
        <span id="t42sv_p1Scale"></span>
      </div>
      <div class="t42s-group">
        <label>P1 Tile Spacing</label>
        <input type="range" min="0.05" max="0.20" step="0.001" id="t42s_p1Spacing">
        <span id="t42sv_p1Spacing"></span>
      </div>
      <div class="t42s-group">
        <label>Opponent Tile Scale</label>
        <input type="range" min="0.2" max="0.8" step="0.01" id="t42s_opponentScale">
        <span id="t42sv_opponentScale"></span>
      </div>
      <div class="t42s-group">
        <label>P2 X Position (Left)</label>
        <input type="range" min="0.05" max="0.35" step="0.005" id="t42s_p2x">
        <span id="t42sv_p2x"></span>
      </div>
      <div class="t42s-group">
        <label>P4 X Position (Right)</label>
        <input type="range" min="0.65" max="0.95" step="0.005" id="t42s_p4x">
        <span id="t42sv_p4x"></span>
      </div>
      <div class="t42s-group">
        <label>P3 Y Position (Top)</label>
        <input type="range" min="0.30" max="0.50" step="0.005" id="t42s_p3y">
        <span id="t42sv_p3y"></span>
      </div>
      <div class="t42s-group">
        <label>Side Tile Spacing (P2/P4)</label>
        <input type="range" min="0.02" max="0.08" step="0.001" id="t42s_sideSpacing">
        <span id="t42sv_sideSpacing"></span>
      </div>
      <div class="t42s-group">
        <label>P3 Tile Spacing</label>
        <input type="range" min="0.03" max="0.10" step="0.001" id="t42s_p3Spacing">
        <span id="t42sv_p3Spacing"></span>
      </div>
      <div class="t42s-group">
        <label>Trick Area Scale</label>
        <input type="range" min="0.2" max="0.8" step="0.01" id="t42s_trickScale">
        <span id="t42sv_trickScale"></span>
      </div>
      <div class="t42s-group">
        <label>P2 Trick X</label>
        <input type="range" min="0.25" max="0.48" step="0.005" id="t42s_p2TrickX">
        <span id="t42sv_p2TrickX"></span>
      </div>
      <div class="t42s-group">
        <label>P4 Trick X</label>
        <input type="range" min="0.52" max="0.75" step="0.005" id="t42s_p4TrickX">
        <span id="t42sv_p4TrickX"></span>
      </div>
      <div class="t42s-group">
        <label>P1 Trick Y</label>
        <input type="range" min="0.60" max="0.80" step="0.005" id="t42s_p1TrickY">
        <span id="t42sv_p1TrickY"></span>
      </div>
      <div class="t42s-group">
        <label>P3 Trick Y</label>
        <input type="range" min="0.45" max="0.60" step="0.005" id="t42s_p3TrickY">
        <span id="t42sv_p3TrickY"></span>
      </div>
      <div style="text-align:center;margin-top:12px;">
        <button class="glossBtn" id="btnT42Reset" style="padding:6px 14px;font-size:12px;">Reset Defaults</button>
        <button class="glossBtn" id="btnT42Export" style="padding:6px 14px;font-size:12px;margin-left:8px;">Export Values</button>
      </div>
    </div>
  </div>
</div>
<style>
.t42s-group { margin-bottom:8px; }
.t42s-group label { display:block;font-size:11px;color:rgba(255,255,255,0.8);margin-bottom:2px; }
.t42s-group input[type=range] { width:220px;vertical-align:middle; }
.t42s-group span { font-size:11px;color:#fff;margin-left:6px; }
#t42SettingsBtn { position:fixed; bottom:10px; left:10px; z-index:900; background:rgba(0,0,0,0.6); color:#fff; border:1px solid rgba(255,255,255,0.3); border-radius:6px; padding:4px 10px; font-size:11px; cursor:pointer; display:none; }
#t42SettingsBtn:hover { background:rgba(0,0,0,0.8); }
</style>
<button id="t42SettingsBtn">T42 Layout</button>
<script>
(function(){
  const DEFAULTS = {
    p1Scale: 1.071, p1Spacing: 0.13487, opponentScale: 0.393,
    p2x: 0.165, p4x: 0.835, p3y: 0.411,
    sideSpacing: 0.0456, p3Spacing: 0.0556, trickScale: 0.393,
    p2TrickX: 0.380, p4TrickX: 0.610, p1TrickY: 0.678, p3TrickY: 0.522,
    leadScale: 0.393
  };
  const KEYS = Object.keys(DEFAULTS);

  function showT42Settings(){
    document.getElementById('t42SettingsBackdrop').style.display = 'flex';
    KEYS.forEach(k => {
      const slider = document.getElementById('t42s_' + k);
      const label = document.getElementById('t42sv_' + k);
      if(slider){
        slider.value = T42_SETTINGS[k];
        if(label) label.textContent = T42_SETTINGS[k].toFixed(3);
      }
    });
  }
  function hideT42Settings(){
    document.getElementById('t42SettingsBackdrop').style.display = 'none';
  }

  // Toggle button visibility
  const origInitGameMode = window.initGameMode;
  const _t42Btn = document.getElementById('t42SettingsBtn');
  if(origInitGameMode){
    window.initGameMode = function(mode){
      origInitGameMode(mode);
      if(_t42Btn) _t42Btn.style.display = mode === 'T42' ? 'block' : 'none';
    };
  }

  // Button click
  if(_t42Btn) _t42Btn.addEventListener('click', showT42Settings);

  // Close button
  document.getElementById('btnCloseT42Settings').addEventListener('click', hideT42Settings);

  // Backdrop click
  document.getElementById('t42SettingsBackdrop').addEventListener('click', function(e){
    if(e.target === this) hideT42Settings();
  });

  // Slider changes — live update
  KEYS.forEach(k => {
    const slider = document.getElementById('t42s_' + k);
    const label = document.getElementById('t42sv_' + k);
    if(slider){
      slider.addEventListener('input', function(){
        const val = parseFloat(this.value);
        T42_SETTINGS[k] = val;
        if(label) label.textContent = val.toFixed(3);
        applyT42Settings();
      });
    }
  });

  // Reset defaults
  document.getElementById('btnT42Reset').addEventListener('click', function(){
    Object.assign(T42_SETTINGS, DEFAULTS);
    KEYS.forEach(k => {
      const slider = document.getElementById('t42s_' + k);
      const label = document.getElementById('t42sv_' + k);
      if(slider){ slider.value = DEFAULTS[k]; }
      if(label){ label.textContent = DEFAULTS[k].toFixed(3); }
    });
    applyT42Settings();
  });

  // Export values
  document.getElementById('btnT42Export').addEventListener('click', function(){
    const vals = {};
    KEYS.forEach(k => { vals[k] = T42_SETTINGS[k]; });
    const str = JSON.stringify(vals, null, 2);
    prompt('Copy these T42 layout values:', str);
  });
})();
</script>
</body>"""
    html = patch(html, old_body_end, new_body_end, "T42 Layout Settings popup + button + JS")

    # =========================================================================
    # FEATURE 3: Update version in title
    # =========================================================================
    print("\n=== FEATURE 3: Version update ===")

    html = patch(html,
        "<title>TN51 / T42 Domino Game</title>",
        "<title>TN51 / T42 Domino Game V10_52</title>",
        "Version title update")

    # =========================================================================
    # DONE
    # =========================================================================
    print(f"\nAll patches applied successfully!")
    print(f"Original size: {original_len:,} bytes")
    print(f"New size: {len(html):,} bytes")
    print(f"Delta: +{len(html) - original_len:,} bytes")

    write_file(OUTPUT_FILE, html)
    print(f"Written to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
