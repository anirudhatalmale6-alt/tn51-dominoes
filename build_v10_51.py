#!/usr/bin/env python3
"""
Build script: TN51 Dominoes V10_51
Base: V10_50
Feature: Texas 42 game mode
"""

import re
import sys

INPUT_FILE = "TN51_Dominoes_V10_50.html"
OUTPUT_FILE = "TN51_Dominoes_V10_51.html"

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
    actual = (len(src) - len(src.replace(old, ''))) // len(old) if count > 1 else 1
    print(f"  OK: {label} ({occurrences} replaced)")
    return result

def main():
    print(f"Reading {INPUT_FILE}...")
    html = read_file(INPUT_FILE)
    original_len = len(html)

    # =========================================================================
    # PATCH 1: Add GAME_MODE global variable and T42 layout after session init
    # =========================================================================
    print("\n=== PATCH 1: Game mode global + T42 layout ===")

    old_session = "let session = new SessionV6_4g(6, 7, 6, 7);"
    new_session = """let GAME_MODE = 'TN51'; // 'TN51' or 'T42'
let session = new SessionV6_4g(6, 7, 6, 7);

// Texas 42 Layout — 4 players mapped onto TN51 hex positions
// P1 (bottom) = TN51 P1 + 7th tile
// P3 (top/partner) = TN51 P4 + 7th tile
// P2 (left) = TN51 P4 rotated 90° CCW
// P4 (right) = TN51 P4 rotated 90° CW
const LAYOUT_T42 = {
  "sections": [
    {
      "name": "Trick_History",
      "seed": {"xN": 0.106, "yN": 0.2281, "sizeW": 22, "sizeH": 112, "rz": 270, "ry": 180, "scale": 0.393},
      "grid": {"cols": 4, "rows": 7},
      "tile": [6, 1],
      "dominoes": (function(){
        const d = [];
        const yVals = [0.2281, 0.2592, 0.2904, 0.3215];
        const xVals = [0.106, 0.2171, 0.3282, 0.4393, 0.5504, 0.6616, 0.7727];
        let idx = 0;
        for(let r = 0; r < 7; r++){
          for(let c = 0; c < 4; c++){
            d.push({"col": c, "row": r, "index": idx++, "xN": xVals[r], "yN": yVals[c], "scale": 0.393, "rotZ": 270, "rotY": 180});
          }
        }
        return d;
      })()
    },
    {
      "name": "Player_1_Hand",
      "dominoes": (function(){
        const d = [];
        for(let i = 0; i < 7; i++){
          d.push({"col": i, "row": 0, "index": i, "xN": 0.9 - i * 0.13487, "yN": 0.9, "scale": 1.071, "rotZ": 0, "rotY": 180});
        }
        return d;
      })()
    },
    {
      "name": "Player_1_Played_Domino",
      "dominoes": [{"col": 0, "row": 0, "index": 0, "xN": 0.495, "yN": 0.678, "scale": 0.393, "rotZ": 270, "rotY": 180}]
    },
    {
      "name": "Player_2_Hand",
      "dominoes": (function(){
        const d = [];
        const cy = 0.600, sp = 0.0456, x = 0.165;
        for(let i = 0; i < 7; i++){
          d.push({"col": 0, "row": i, "index": i, "xN": x, "yN": (cy - 3*sp) + i*sp, "scale": 0.393, "rotZ": 270, "rotY": 0});
        }
        return d;
      })()
    },
    {
      "name": "Player_2_Played_Domino",
      "dominoes": [{"col": 0, "row": 0, "index": 0, "xN": 0.380, "yN": 0.600, "scale": 0.393, "rotZ": 270, "rotY": 180}]
    },
    {
      "name": "Player_3_Hand",
      "dominoes": (function(){
        const d = [];
        for(let i = 0; i < 7; i++){
          d.push({"col": i, "row": 0, "index": i, "xN": 0.3282 + i * 0.0556, "yN": 0.411, "scale": 0.393, "rotZ": 180, "rotY": 0});
        }
        return d;
      })()
    },
    {
      "name": "Player_3_Played_Domino",
      "dominoes": [{"col": 0, "row": 0, "index": 0, "xN": 0.495, "yN": 0.522, "scale": 0.393, "rotZ": 270, "rotY": 180}]
    },
    {
      "name": "Player_4_Hand",
      "dominoes": (function(){
        const d = [];
        const cy = 0.600, sp = 0.0456, x = 0.835;
        for(let i = 0; i < 7; i++){
          d.push({"col": 0, "row": i, "index": i, "xN": x, "yN": (cy - 3*sp) + i*sp, "scale": 0.393, "rotZ": 90, "rotY": 0});
        }
        return d;
      })()
    },
    {
      "name": "Player_4_Played_Domino",
      "dominoes": [{"col": 0, "row": 0, "index": 0, "xN": 0.610, "yN": 0.600, "scale": 0.393, "rotZ": 270, "rotY": 180}]
    },
    {
      "name": "Lead_Domino",
      "dominoes": [{"col": 0, "row": 0, "index": 0, "xN": 0.495, "yN": 0.600, "scale": 0.393, "rotZ": 0, "rotY": 180}]
    }
  ],
  "totalDominoes": 28
};

// T42 placeholder positions
const PLACEHOLDER_CONFIG_T42 = {
  dominoWidth: 44,
  dominoHeight: 22,
  leadSize: 28,
  players: {
    1: { xN: 0.495, yN: 0.678 },
    2: { xN: 0.380, yN: 0.600 },
    3: { xN: 0.495, yN: 0.522 },
    4: { xN: 0.610, yN: 0.600 }
  },
  lead: { xN: 0.495, yN: 0.600 }
};

// Helper: get current layout based on game mode
function getActiveLayout(){ return GAME_MODE === 'T42' ? LAYOUT_T42 : LAYOUT; }
function getActivePlaceholderConfig(){ return GAME_MODE === 'T42' ? PLACEHOLDER_CONFIG_T42 : PLACEHOLDER_CONFIG; }

function initGameMode(mode){
  GAME_MODE = mode;
  if(mode === 'T42'){
    session = new SessionV6_4g(4, 6, 7, 7);
  } else {
    session = new SessionV6_4g(6, 7, 6, 7);
  }
}"""
    html = patch(html, old_session, new_session, "Game mode global + T42 layout + helpers")

    # =========================================================================
    # PATCH 2: Fix getSection to use active layout
    # =========================================================================
    print("\n=== PATCH 2: getSection uses active layout ===")

    old_get_section = "function getSection(name){\n  return LAYOUT.sections.find(s => s.name === name);\n}"
    new_get_section = "function getSection(name){\n  return getActiveLayout().sections.find(s => s.name === name);\n}"
    html = patch(html, old_get_section, new_get_section, "getSection uses active layout")

    # =========================================================================
    # PATCH 3: Fix dealer rotation (% 6 → % player_count)
    # =========================================================================
    print("\n=== PATCH 3: Dealer rotation ===")

    html = patch(html,
        "this.dealer = (this.dealer + 1) % 6;",
        "this.dealer = (this.dealer + 1) % this.game.player_count;",
        "Dealer rotation modulo")

    # =========================================================================
    # PATCH 4: Fix _check_for_set totalPossible
    # =========================================================================
    print("\n=== PATCH 4: totalPossible in _check_for_set ===")

    html = patch(html,
        "const totalPossible = 51;",
        "const totalPossible = GAME_MODE === 'T42' ? 42 : 51;",
        "totalPossible dynamic")

    # =========================================================================
    # PATCH 5: Fix evaluateHandForBid for T42 thresholds
    # =========================================================================
    print("\n=== PATCH 5: evaluateHandForBid T42 thresholds ===")

    old_eval = """function evaluateHandForBid(hand) {
  const doubles = [];
  const blanks = [];

  for (const tile of hand) {
    const [a, b] = tile;
    if (a === b) doubles.push(tile);
    if (a === 0 || b === 0) blanks.push(tile);
  }

  if (blanks.length >= 4) {
    const has01 = blanks.some(t => (t[0] === 0 && t[1] === 1) || (t[0] === 1 && t[1] === 0));
    let maxSmallPip = 0;
    let maxDoublePip = 0;
    for (const tile of hand) {
      const [a, b] = tile;
      if (a === b) {
        maxDoublePip = Math.max(maxDoublePip, a);
      } else if (a === 0 || b === 0) {
        maxSmallPip = Math.max(maxSmallPip, Math.max(a, b));
      }
    }
    if (has01 && maxSmallPip <= 2 && maxDoublePip <= 1) {
      return { action: "bid", bid: 51, marks: 1 };
    }
  }

  if (doubles.length >= 4) {
    return { action: "bid", bid: 34, marks: 1 };
  }

  for (let trumpPip = 7; trumpPip >= 0; trumpPip--) {
    const trumpTiles = hand.filter(t => t[0] === trumpPip || t[1] === trumpPip);
    const trumpCount = trumpTiles.length;
    const hasDoubleTrump = trumpTiles.some(t => t[0] === trumpPip && t[1] === trumpPip);
    const hasSecondTrump = trumpPip > 0 && trumpTiles.some(t =>
      (t[0] === trumpPip && t[1] === trumpPip - 1) || (t[0] === trumpPip - 1 && t[1] === trumpPip)
    );
    const nonTrumpDoubles = doubles.filter(d => d[0] !== trumpPip);

    if (trumpCount >= 4 && nonTrumpDoubles.length >= 2 && hasDoubleTrump && hasSecondTrump) {
      return { action: "bid", bid: 51, marks: 1 };
    }
    if (trumpCount >= 4 && nonTrumpDoubles.length >= 2 && hasDoubleTrump) {
      return { action: "bid", bid: 39, marks: 1 };
    }
    if (trumpCount >= 3 && hasDoubleTrump && hasSecondTrump && doubles.length >= 1) {
      return { action: "bid", bid: 34, marks: 1 };
    }
  }

  return { action: "pass" };
}"""

    new_eval = """function evaluateHandForBid(hand) {
  const doubles = [];
  const blanks = [];
  const maxBid = GAME_MODE === 'T42' ? 42 : 51;
  const minBid = GAME_MODE === 'T42' ? 30 : 34;
  const midBid = GAME_MODE === 'T42' ? 36 : 39;
  const maxPip = session.game.max_pip;

  for (const tile of hand) {
    const [a, b] = tile;
    if (a === b) doubles.push(tile);
    if (a === 0 || b === 0) blanks.push(tile);
  }

  if (GAME_MODE !== 'T42' && blanks.length >= 4) {
    const has01 = blanks.some(t => (t[0] === 0 && t[1] === 1) || (t[0] === 1 && t[1] === 0));
    let maxSmallPip = 0;
    let maxDoublePip = 0;
    for (const tile of hand) {
      const [a, b] = tile;
      if (a === b) {
        maxDoublePip = Math.max(maxDoublePip, a);
      } else if (a === 0 || b === 0) {
        maxSmallPip = Math.max(maxSmallPip, Math.max(a, b));
      }
    }
    if (has01 && maxSmallPip <= 2 && maxDoublePip <= 1) {
      return { action: "bid", bid: maxBid, marks: 1 };
    }
  }

  if (doubles.length >= 4) {
    return { action: "bid", bid: minBid, marks: 1 };
  }

  for (let trumpPip = maxPip; trumpPip >= 0; trumpPip--) {
    const trumpTiles = hand.filter(t => t[0] === trumpPip || t[1] === trumpPip);
    const trumpCount = trumpTiles.length;
    const hasDoubleTrump = trumpTiles.some(t => t[0] === trumpPip && t[1] === trumpPip);
    const hasSecondTrump = trumpPip > 0 && trumpTiles.some(t =>
      (t[0] === trumpPip && t[1] === trumpPip - 1) || (t[0] === trumpPip - 1 && t[1] === trumpPip)
    );
    const nonTrumpDoubles = doubles.filter(d => d[0] !== trumpPip);

    if (trumpCount >= 4 && nonTrumpDoubles.length >= 2 && hasDoubleTrump && hasSecondTrump) {
      return { action: "bid", bid: maxBid, marks: 1 };
    }
    if (trumpCount >= 4 && nonTrumpDoubles.length >= 2 && hasDoubleTrump) {
      return { action: "bid", bid: midBid, marks: 1 };
    }
    if (trumpCount >= 3 && hasDoubleTrump && hasSecondTrump && doubles.length >= 1) {
      return { action: "bid", bid: minBid, marks: 1 };
    }
  }

  return { action: "pass" };
}"""
    html = patch(html, old_eval, new_eval, "evaluateHandForBid T42 thresholds")

    # =========================================================================
    # PATCH 6: Fix aiChooseTrump — remove nello for T42, fix pip range
    # =========================================================================
    print("\n=== PATCH 6: aiChooseTrump ===")

    old_ai_trump = """  if (bidAmount >= 51 && blanks.length >= 4) {
    const has01 = blanks.some(t => (t[0] === 0 && t[1] === 1) || (t[0] === 1 && t[1] === 0));
    let maxSmallPip = 0, maxDoublePip = 0;
    for (const tile of hand) {
      const [a, b] = tile;
      if (a === b) maxDoublePip = Math.max(maxDoublePip, a);
      else if (a === 0 || b === 0) maxSmallPip = Math.max(maxSmallPip, Math.max(a, b));
    }
    if (has01 && maxSmallPip <= 2 && maxDoublePip <= 1) {
      return "NELLO";
    }
  }"""
    new_ai_trump = """  if (GAME_MODE !== 'T42' && bidAmount >= 51 && blanks.length >= 4) {
    const has01 = blanks.some(t => (t[0] === 0 && t[1] === 1) || (t[0] === 1 && t[1] === 0));
    let maxSmallPip = 0, maxDoublePip = 0;
    for (const tile of hand) {
      const [a, b] = tile;
      if (a === b) maxDoublePip = Math.max(maxDoublePip, a);
      else if (a === 0 || b === 0) maxSmallPip = Math.max(maxSmallPip, Math.max(a, b));
    }
    if (has01 && maxSmallPip <= 2 && maxDoublePip <= 1) {
      return "NELLO";
    }
  }"""
    html = patch(html, old_ai_trump, new_ai_trump, "aiChooseTrump skip nello in T42")

    # =========================================================================
    # PATCH 7: Fix bidding slider range — dynamic min/max
    # =========================================================================
    print("\n=== PATCH 7: Bidding slider min/max ===")

    html = patch(html,
        "const minBid = Math.max(34, (biddingState ? biddingState.highBid + 1 : 34));",
        "const _baseBid = GAME_MODE === 'T42' ? 30 : 34;\n  const minBid = Math.max(_baseBid, (biddingState ? biddingState.highBid + 1 : _baseBid));",
        "Bid slider min")

    html = patch(html,
        "slider.max = 51;",
        "slider.max = GAME_MODE === 'T42' ? 42 : 51;",
        "Bid slider max")

    # =========================================================================
    # PATCH 8: Fix 2x notch threshold (>= 51 → >= maxBid)
    # =========================================================================
    print("\n=== PATCH 8: 2x notch threshold ===")

    html = patch(html,
        "if(biddingState && biddingState.highBid >= 51 && !biddingState.inMultiplierMode) return;",
        "if(biddingState && biddingState.highBid >= (GAME_MODE === 'T42' ? 42 : 51) && !biddingState.inMultiplierMode) return;",
        "2x notch threshold")

    # =========================================================================
    # PATCH 9: Fix trump slider max attribute in HTML
    # =========================================================================
    print("\n=== PATCH 9: Trump slider HTML max ===")

    html = patch(html,
        '<input type="range" class="trumpSlider" id="trumpSlider" min="0" max="7" value="0">',
        '<input type="range" class="trumpSlider" id="trumpSlider" min="0" max="7" value="0" data-tn51-max="7" data-t42-max="6">',
        "Trump slider data attributes")

    # =========================================================================
    # PATCH 10: Fix buildTrumpOptions to adjust slider max and hide nello/doubles for T42
    # =========================================================================
    print("\n=== PATCH 10: buildTrumpOptions T42 adjustments ===")

    old_trump_opts = """  // Show/hide Nel-O button based on bid
  nelloBtn.style.display = showNello ? 'block' : 'none';"""
    new_trump_opts = """  // Show/hide Nel-O button based on bid (never in T42)
  nelloBtn.style.display = (GAME_MODE !== 'T42' && showNello) ? 'block' : 'none';
  // Hide Doubles button in T42 (standard Texas 42 doesn't use doubles trump)
  // doublesBtn.style.display = GAME_MODE === 'T42' ? 'none' : 'block';
  // Adjust slider max for T42 (0-6) vs TN51 (0-7)
  slider.max = GAME_MODE === 'T42' ? 6 : 7;"""
    html = patch(html, old_trump_opts, new_trump_opts, "buildTrumpOptions T42 hide nello + slider max")

    # =========================================================================
    # PATCH 11: Fix Nello in set_trump — skip for T42
    # =========================================================================
    print("\n=== PATCH 11: set_trump nello skip for T42 ===")

    old_set_nello = """      else if(upper==="NELLO" || upper==="NELLO_2"){
        this.contract="NELLO";
        if(upper==="NELLO_2") this.bid_marks=2;
        this.game.set_trump_suit(null);
        this.game.set_active_players([0,1,3,5]);
        this.game.hands[2]=[];
        this.game.hands[4]=[];
        this.phase=PHASE_PLAYING;
        this.status=`Nel-O: Lose all tricks to win.`;
        this._notify();
        return;
      }"""
    new_set_nello = """      else if((upper==="NELLO" || upper==="NELLO_2") && GAME_MODE !== 'T42'){
        this.contract="NELLO";
        if(upper==="NELLO_2") this.bid_marks=2;
        this.game.set_trump_suit(null);
        this.game.set_active_players([0,1,3,5]);
        this.game.hands[2]=[];
        this.game.hands[4]=[];
        this.phase=PHASE_PLAYING;
        this.status=`Nel-O: Lose all tricks to win.`;
        this._notify();
        return;
      }"""
    html = patch(html, old_set_nello, new_set_nello, "set_trump nello guard for T42")

    # =========================================================================
    # PATCH 12: Fix createPlaceholders to use active config
    # =========================================================================
    print("\n=== PATCH 12: createPlaceholders active config ===")

    # Fix the loop that creates 6 placeholders
    old_placeholders_loop = """  for(let p = 1; p <= 6; p++){
    const config = PLACEHOLDER_CONFIG.players[p];"""
    new_placeholders_loop = """  const _phConfig = getActivePlaceholderConfig();
  const _phCount = GAME_MODE === 'T42' ? 4 : 6;
  for(let p = 1; p <= _phCount; p++){
    const config = _phConfig.players[p];"""
    html = patch(html, old_placeholders_loop, new_placeholders_loop, "createPlaceholders use active config")

    # =========================================================================
    # PATCH 13: Fix positionPlayerIndicators for T42
    # =========================================================================
    print("\n=== PATCH 13: positionPlayerIndicators T42 ===")

    old_indicator_positions = """  const indicatorPositions = {
    1: { xN: 0.50, yN: 0.72 },   // P1: close to placeholder (big gap from hand)
    2: { xN: 0.32, yN: 0.68 },   // P2: moved inward towards center
    3: { xN: 0.32, yN: 0.52 },   // P3: moved inward towards center
    4: { xN: 0.50, yN: 0.47 },   // P4: between hand and placeholder (inside)
    5: { xN: 0.68, yN: 0.52 },   // P5: moved inward towards center
    6: { xN: 0.68, yN: 0.68 }    // P6: moved inward towards center
  };

  for(let p = 1; p <= 6; p++){"""
    new_indicator_positions = """  const indicatorPositions_TN51 = {
    1: { xN: 0.50, yN: 0.72 },   // P1: close to placeholder (big gap from hand)
    2: { xN: 0.32, yN: 0.68 },   // P2: moved inward towards center
    3: { xN: 0.32, yN: 0.52 },   // P3: moved inward towards center
    4: { xN: 0.50, yN: 0.47 },   // P4: between hand and placeholder (inside)
    5: { xN: 0.68, yN: 0.52 },   // P5: moved inward towards center
    6: { xN: 0.68, yN: 0.68 }    // P6: moved inward towards center
  };
  const indicatorPositions_T42 = {
    1: { xN: 0.50, yN: 0.72 },
    2: { xN: 0.22, yN: 0.60 },
    3: { xN: 0.50, yN: 0.47 },
    4: { xN: 0.78, yN: 0.60 }
  };
  const indicatorPositions = GAME_MODE === 'T42' ? indicatorPositions_T42 : indicatorPositions_TN51;
  const _indCount = GAME_MODE === 'T42' ? 4 : 6;

  // Hide unused indicators in T42 mode
  for(let h = 5; h <= 6; h++){
    const hel = document.getElementById(`playerIndicator${h}`);
    if(hel) hel.style.display = GAME_MODE === 'T42' ? 'none' : '';
  }

  for(let p = 1; p <= _indCount; p++){"""
    html = patch(html, old_indicator_positions, new_indicator_positions, "positionPlayerIndicators T42")

    # =========================================================================
    # PATCH 14: Fix clearPlaceholderText loop
    # =========================================================================
    print("\n=== PATCH 14: clearPlaceholderText loop ===")

    # Find the clearPlaceholderText function that loops to 6
    old_clear_ph = """  for(let p = 1; p <= 6; p++){
    setPlaceholderText(p, '', '');
  }"""
    new_clear_ph = """  const _clrCount = GAME_MODE === 'T42' ? 4 : 6;
  for(let p = 1; p <= _clrCount; p++){
    setPlaceholderText(p, '', '');
  }"""
    html = patch(html, old_clear_ph, new_clear_ph, "clearPlaceholderText loop")

    # =========================================================================
    # PATCH 15: Fix startNewHand sprite creation loops
    # =========================================================================
    print("\n=== PATCH 15: startNewHand sprite loops ===")

    old_start_loop = """  for(let p = 0; p < 6; p++){
    sprites[p] = [];
    const playerNum = seatToPlayer(p);  // Convert seat to player number for layout
    for(let h = 0; h < 6; h++){
      const tile = hands[p][h];"""
    new_start_loop = """  for(let p = 0; p < session.game.player_count; p++){
    sprites[p] = [];
    const playerNum = seatToPlayer(p);  // Convert seat to player number for layout
    for(let h = 0; h < session.game.hand_size; h++){
      const tile = hands[p][h];"""
    html = patch(html, old_start_loop, new_start_loop, "startNewHand sprite loops")

    # =========================================================================
    # PATCH 16: Fix boneyard2 rendering — dynamic max pip
    # =========================================================================
    print("\n=== PATCH 16: Boneyard2 rendering dynamic pip ===")

    old_by2_grid = """  // Build the grid: same layout as main boneyard
  const rows = [];
  const doublesRow = [];
  for(let pip = 7; pip >= 0; pip--) doublesRow.push([pip, pip]);
  rows.push(doublesRow);
  for(let suit = 7; suit >= 1; suit--){
    const row = [];
    for(let low = suit - 1; low >= 0; low--) row.push([suit, low]);
    rows.push(row);
  }"""
    new_by2_grid = """  // Build the grid: dynamic based on game mode (double-7 for TN51, double-6 for T42)
  const _by2MaxPip = session.game.max_pip;
  const rows = [];
  const doublesRow = [];
  for(let pip = _by2MaxPip; pip >= 0; pip--) doublesRow.push([pip, pip]);
  rows.push(doublesRow);
  for(let suit = _by2MaxPip; suit >= 1; suit--){
    const row = [];
    for(let low = suit - 1; low >= 0; low--) row.push([suit, low]);
    rows.push(row);
  }"""
    html = patch(html, old_by2_grid, new_by2_grid, "Boneyard2 dynamic pip range")

    # Also fix the hardcoded boneyard row/col counts
    html = patch(html,
        "const maxCols = 8;\n  const numRows = 8;",
        "const maxCols = _by2MaxPip + 1;\n  const numRows = _by2MaxPip + 1;",
        "Boneyard2 maxCols/numRows dynamic")

    # =========================================================================
    # PATCH 17: Fix all hardcoded 6-player seat loops in PP and other functions
    # =========================================================================
    print("\n=== PATCH 17: Fix hardcoded seat loops ===")

    # These are the main rendering/rotation loops in Pass & Play
    # We need to be careful — only replace the ones that iterate over game seats
    # Pattern: "for (let seat = 0; seat < 6; seat++)" — these are the game seat loops

    # Fix ppRotateBoard loops (lines ~3808, 3820, 3898, 3959, 4003, 4027)
    # These all iterate over seats for sprite positioning
    html = html.replace(
        "for (let seat = 0; seat < 6; seat++) {",
        "for (let seat = 0; seat < session.game.player_count; seat++) {",
    )
    count_seat_6 = html.count("for (let seat = 0; seat < session.game.player_count; seat++) {")
    print(f"  OK: seat < 6 loops → seat < session.game.player_count ({count_seat_6} replaced)")

    # Fix "for(let s = 0; s < 6; s++)" patterns (note: no space after for)
    html = html.replace(
        "for(let s = 0; s < 6; s++){",
        "for(let s = 0; s < session.game.player_count; s++){",
    )
    count_s_6 = html.count("for(let s = 0; s < session.game.player_count; s++){")
    print(f"  OK: s < 6 loops → s < session.game.player_count ({count_s_6} replaced)")

    # Fix "for (let s = 0; s < 6; s++) {" (with spaces)
    html = html.replace(
        "for (let s = 0; s < 6; s++) {",
        "for (let s = 0; s < session.game.player_count; s++) {",
    )

    # Fix "for(let seat = 0; seat < 6; seat++){" (no spaces)
    html = html.replace(
        "for(let seat = 0; seat < 6; seat++){",
        "for(let seat = 0; seat < session.game.player_count; seat++){",
    )

    # =========================================================================
    # PATCH 18: Fix "for(let p = 1; p <= 6; p++)" in remaining locations
    # =========================================================================
    print("\n=== PATCH 18: Fix p <= 6 loops ===")

    # The createPlaceholders one was already patched (PATCH 12)
    # The clearPlaceholderText one was already patched (PATCH 14)
    # The positionPlayerIndicators one was already patched (PATCH 13)
    # Any remaining ones need to be dynamic
    # Search for remaining instances
    remaining_p6 = html.count("for(let p = 1; p <= 6; p++){")
    if remaining_p6 > 0:
        html = html.replace(
            "for(let p = 1; p <= 6; p++){",
            "for(let p = 1; p <= session.game.player_count; p++){"
        )
        print(f"  OK: p <= 6 loops → p <= session.game.player_count ({remaining_p6} replaced)")
    else:
        print(f"  OK: No remaining p <= 6 loops (all already patched)")

    # =========================================================================
    # PATCH 19: Fix SEAT_TO_PLAYER and PLAYER_TO_SEAT for T42
    # =========================================================================
    print("\n=== PATCH 19: Seat/player mapping ===")

    old_mapping = """const SEAT_TO_PLAYER = [1, 2, 3, 4, 5, 6];
const PLAYER_TO_SEAT = [null, 0, 1, 2, 3, 4, 5];
function seatToPlayer(seat){ return SEAT_TO_PLAYER[seat] || (seat + 1); }"""
    new_mapping = """const SEAT_TO_PLAYER_TN51 = [1, 2, 3, 4, 5, 6];
const SEAT_TO_PLAYER_T42 = [1, 2, 3, 4];
const PLAYER_TO_SEAT_TN51 = [null, 0, 1, 2, 3, 4, 5];
const PLAYER_TO_SEAT_T42 = [null, 0, 1, 2, 3];
function seatToPlayer(seat){
  const map = GAME_MODE === 'T42' ? SEAT_TO_PLAYER_T42 : SEAT_TO_PLAYER_TN51;
  return map[seat] || (seat + 1);
}"""
    html = patch(html, old_mapping, new_mapping, "Seat/player mapping dynamic")

    # =========================================================================
    # PATCH 20: Add game mode selector to Game Settings popup
    # =========================================================================
    print("\n=== PATCH 20: Game Settings popup — game mode selector ===")

    old_settings_body = """    <div class="modalBody" style="padding:16px;">
      <div style="text-align:center;margin-bottom:16px;">
        <div style="font-size:13px;color:rgba(255,255,255,0.8);margin-bottom:10px;font-weight:600;">Marks to Win</div>"""
    new_settings_body = """    <div class="modalBody" style="padding:16px;">
      <div style="text-align:center;margin-bottom:16px;">
        <div style="font-size:13px;color:rgba(255,255,255,0.8);margin-bottom:10px;font-weight:600;">Game Type</div>
        <div style="display:flex;gap:10px;justify-content:center;">
          <button class="glossBtn gsGameTypeBtn gsGameTypeSelected" data-game-type="TN51" style="padding:8px 16px;font-size:13px;font-weight:700;">Tennessee 51</button>
          <button class="glossBtn gsGameTypeBtn" data-game-type="T42" style="padding:8px 16px;font-size:13px;font-weight:700;">Texas 42</button>
        </div>
      </div>
      <div style="text-align:center;margin-bottom:16px;">
        <div style="font-size:13px;color:rgba(255,255,255,0.8);margin-bottom:10px;font-weight:600;">Marks to Win</div>"""
    html = patch(html, old_settings_body, new_settings_body, "Game Settings game type selector")

    # =========================================================================
    # PATCH 21: Add game mode selector JS handler
    # =========================================================================
    print("\n=== PATCH 21: Game mode selector JS ===")

    old_settings_js = """document.getElementById('btnGameSettingsStart').addEventListener('click', () => {
  hideGameSettings();
  clearSavedGame();
  session.marks_to_win = selectedMarksToWin;
  startNewHand();
});"""
    new_settings_js = """// Game type selector
let selectedGameType = 'TN51';
document.querySelectorAll('.gsGameTypeBtn').forEach(btn => {
  btn.addEventListener('click', () => {
    selectedGameType = btn.dataset.gameType;
    document.querySelectorAll('.gsGameTypeBtn').forEach(b => {
      b.style.border = 'none';
      b.classList.remove('gsGameTypeSelected');
    });
    btn.style.border = '2px solid #fff';
    btn.classList.add('gsGameTypeSelected');
  });
});

document.getElementById('btnGameSettingsStart').addEventListener('click', () => {
  hideGameSettings();
  clearSavedGame();
  initGameMode(selectedGameType);
  session.marks_to_win = selectedMarksToWin;
  // Update start screen title
  const titleEl = document.querySelector('.startScreenTitle');
  if(titleEl) titleEl.textContent = GAME_MODE === 'T42' ? 'Texas 42' : 'Tennessee 51';
  startNewHand();
});"""
    html = patch(html, old_settings_js, new_settings_js, "Game Settings JS handler")

    # =========================================================================
    # PATCH 22: Fix boneyard2 hardcoded trick history positions for T42
    # =========================================================================
    print("\n=== PATCH 22: Boneyard2 trick history positions ===")

    old_by2_pos = """  // Trick history normalized positions (from LAYOUT.sections Trick_History):
  // Columns at xN: 0.106, 0.2171, 0.3282, 0.4393, 0.5504, 0.6616, 0.7727, 0.8838
  // Rows at yN: 0.197, 0.2281, 0.2592, 0.2904, 0.3215, 0.3526
  // These are CENTER positions of trick history tiles
  const thColXN = [0.106, 0.2171, 0.3282, 0.4393, 0.5504, 0.6616, 0.7727, 0.8838];
  const thRowYN = [0.197, 0.2281, 0.2592, 0.2904, 0.3215, 0.3526];

  // Calculate column spacing and row spacing from the grid
  const colSpacing = (thColXN[7] - thColXN[0]) / 7 * tableW;  // px between column centers
  const rowSpacing = (thRowYN[5] - thRowYN[0]) / 5 * tableH;  // px between row centers"""
    new_by2_pos = """  // Trick history normalized positions — same for both modes
  const thColXN = [0.106, 0.2171, 0.3282, 0.4393, 0.5504, 0.6616, 0.7727, 0.8838];
  const thRowYN = GAME_MODE === 'T42'
    ? [0.2281, 0.2592, 0.2904, 0.3215]
    : [0.197, 0.2281, 0.2592, 0.2904, 0.3215, 0.3526];

  const colSpacing = (thColXN[thColXN.length-1] - thColXN[0]) / (thColXN.length-1) * tableW;
  const rowSpacing = (thRowYN[thRowYN.length-1] - thRowYN[0]) / Math.max(1, thRowYN.length-1) * tableH;"""
    html = patch(html, old_by2_pos, new_by2_pos, "Boneyard2 trick history positions dynamic")

    # =========================================================================
    # PATCH 23: Fix currentBidSelection default for T42
    # =========================================================================
    print("\n=== PATCH 23: currentBidSelection default ===")

    html = patch(html,
        "currentBidSelection = 34;",
        "currentBidSelection = GAME_MODE === 'T42' ? 30 : 34;",
        "currentBidSelection default")

    # =========================================================================
    # PATCH 24: Fix AI bid hints that reference 34
    # =========================================================================
    print("\n=== PATCH 24: AI bid hint default ===")

    html = patch(html,
        "const hintBid = session.current_bid || 34;",
        "const hintBid = session.current_bid || (GAME_MODE === 'T42' ? 30 : 34);",
        "AI bid hint default")

    # =========================================================================
    # PATCH 24b: Update bid slider labels dynamically
    # =========================================================================
    print("\n=== PATCH 24b: Bid slider labels ===")

    old_slider_value = """  slider.value = minBid;

  // Update display when slider moves"""
    new_slider_value = """  slider.value = minBid;

  // Update bid range labels for game mode
  const _bidLabels = slider.parentElement.querySelector('.bidRangeLabels');
  if(_bidLabels){
    const spans = _bidLabels.querySelectorAll('span');
    if(spans[0]) spans[0].textContent = minBid;
    if(spans[1]) spans[1].textContent = slider.max;
  }

  // Update display when slider moves"""
    html = patch(html, old_slider_value, new_slider_value, "Bid slider label update")

    # =========================================================================
    # PATCH 25a: Hide P5/P6 indicators in startNewHand for T42
    # =========================================================================
    print("\n=== PATCH 25a: Hide P5/P6 in startNewHand ===")

    old_start_trump_display = """  // Hide trump display
  document.getElementById('trumpDisplay').classList.remove('visible');"""
    new_start_trump_display = """  // Hide trump display
  document.getElementById('trumpDisplay').classList.remove('visible');

  // Hide unused player indicators in T42 mode
  if(GAME_MODE === 'T42'){
    for(let h = 5; h <= 6; h++){
      const hel = document.getElementById('playerIndicator' + h);
      if(hel) hel.style.display = 'none';
    }
  } else {
    for(let h = 1; h <= 6; h++){
      const hel = document.getElementById('playerIndicator' + h);
      if(hel) hel.style.display = '';
    }
  }"""
    html = patch(html, old_start_trump_display, new_start_trump_display, "Hide P5/P6 in startNewHand")

    # =========================================================================
    # PATCH 25: Update version number
    # =========================================================================
    print("\n=== PATCH 25: Version number ===")

    html = patch(html,
        "<title>TN51 Sprite Game</title>",
        "<title>TN51 / T42 Domino Game</title>",
        "Title update")

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
