#!/usr/bin/env python3
"""
Build script for TN51 Dominoes V10_33
Patches V10_32 to add Monte Carlo Simulation feature.
"""

import sys

INPUT  = "/var/lib/freelancer/projects/40101953/TN51_Dominoes_V10_32.html"
OUTPUT = "/var/lib/freelancer/projects/40101953/TN51_Dominoes_V10_33.html"

def read_file(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()

def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def patch(html, old, new, label=""):
    if old not in html:
        print(f"ERROR: Could not find patch target for: {label}")
        print(f"  Looking for: {repr(old[:120])}")
        sys.exit(1)
    count = html.count(old)
    if count > 1:
        print(f"WARNING: Found {count} occurrences of patch target for: {label}")
        print(f"  Will replace first occurrence only.")
    result = html.replace(old, new, 1)
    print(f"  PATCHED: {label}")
    return result

def main():
    html = read_file(INPUT)
    print(f"Read {len(html)} bytes from {INPUT}")

    # =========================================================================
    # PATCH 1: Add Monte Carlo menu item after "Advanced AI Log"
    # =========================================================================
    old_menu = '  <div class="settingsItem" id="menuAdvancedLog">Advanced AI Log</div>\n  <div class="settingsDivider"></div>'
    new_menu = '  <div class="settingsItem" id="menuAdvancedLog">Advanced AI Log</div>\n  <div class="settingsItem" id="menuMonteCarlo">Monte Carlo</div>\n  <div class="settingsDivider"></div>'
    html = patch(html, old_menu, new_menu, "Add Monte Carlo menu item")

    # =========================================================================
    # PATCH 2: Add Monte Carlo modal HTML after advLogBackdrop closing </div>
    # =========================================================================
    old_modal_anchor = '</div>\n\n<!-- Bidding Overlay -->'
    mc_modal_html = r'''</div>

<!-- Monte Carlo Simulation Modal -->
<div class="modalBackdrop" id="mcBackdrop" style="display:none;">
  <div class="modalPanel" style="max-width:720px;width:95vw;max-height:90vh;">
    <div class="modalHeader">
      <span>Monte Carlo Simulation</span>
      <button class="modalCloseBtn" id="mcCloseBtn">&times;</button>
    </div>
    <div class="modalBody" style="max-height:75vh;overflow-y:auto;padding:12px;">
      <div id="mcNotReady" style="display:none;text-align:center;padding:20px;color:rgba(255,255,255,0.7);font-size:13px;">
        Monte Carlo is available during play phase when you are the bid winner and leading trick 1.
      </div>
      <div id="mcMain">
        <div style="margin-bottom:10px;font-size:12px;color:rgba(255,255,255,0.8);">
          Tap your tiles in the order you want to lead them. The simulation will test how often your bid makes.
        </div>
        <div id="mcTileSelect" style="display:flex;flex-wrap:wrap;gap:8px;justify-content:center;margin-bottom:12px;"></div>
        <div style="display:flex;gap:8px;justify-content:center;margin-bottom:12px;">
          <button id="mcResetBtn" style="padding:6px 14px;background:rgba(239,68,68,0.8);border:none;border-radius:8px;color:#fff;font-weight:600;font-size:12px;cursor:pointer;">Reset Order</button>
        </div>
        <div id="mcControls" style="display:flex;align-items:center;gap:12px;justify-content:center;margin-bottom:12px;">
          <label style="font-size:12px;color:rgba(255,255,255,0.8);">Simulations:</label>
          <select id="mcSimCount" style="padding:4px 8px;border-radius:6px;border:1px solid rgba(255,255,255,0.3);background:rgba(255,255,255,0.15);color:#fff;font-size:12px;">
            <option value="100">100</option>
            <option value="500" selected>500</option>
            <option value="1000">1000</option>
          </select>
          <button id="mcRunBtn" disabled style="padding:8px 20px;background:rgba(34,197,94,0.8);border:none;border-radius:8px;color:#fff;font-weight:700;font-size:13px;cursor:pointer;opacity:0.5;">Run Simulation</button>
        </div>
        <div id="mcProgress" style="display:none;text-align:center;padding:10px;">
          <div style="font-size:12px;color:rgba(255,255,255,0.8);margin-bottom:6px;" id="mcProgressText">Running...</div>
          <div style="width:100%;height:6px;background:rgba(255,255,255,0.15);border-radius:3px;overflow:hidden;">
            <div id="mcProgressBar" style="width:0%;height:100%;background:rgba(34,197,94,0.9);transition:width 0.1s;border-radius:3px;"></div>
          </div>
        </div>
        <div id="mcResults" style="display:none;margin-top:8px;"></div>
      </div>
    </div>
  </div>
</div>

<!-- Bidding Overlay -->'''
    html = patch(html, old_modal_anchor, mc_modal_html, "Add Monte Carlo modal HTML")

    # =========================================================================
    # PATCH 3: Add Monte Carlo event listeners and simulation engine
    #          Insert after advLogClearBtn handler block
    # =========================================================================
    old_listener_anchor = "document.getElementById('advLogClearBtn').addEventListener('click', () => {\n  if(confirm('Clear all log entries? Hand numbering will restart from 1.')){\n    gameLog = [];\n    handNumber = 0;\n    trickNumber = 0;\n    saveGameLog();\n    document.getElementById('advLogContent').textContent = 'Log cleared. Hand numbering will start from 1.';\n  }\n});"

    new_listener_block = old_listener_anchor + r"""

// ============================================================================
// MONTE CARLO SIMULATION ENGINE (V10_33)
// ============================================================================

(function() {
  'use strict';

  let mcSelectedOrder = [];   // indices into P1's hand, in user-selected order
  let mcPlayerHand = [];      // copy of P1's hand tiles at time modal opened
  let mcRunning = false;

  // --- Open Monte Carlo modal ---
  document.getElementById('menuMonteCarlo').addEventListener('click', () => {
    document.getElementById('settingsMenu').classList.remove('open');
    mcOpenModal();
  });

  document.getElementById('mcCloseBtn').addEventListener('click', () => {
    document.getElementById('mcBackdrop').style.display = 'none';
    mcRunning = false;
  });

  document.getElementById('mcResetBtn').addEventListener('click', () => {
    mcSelectedOrder = [];
    mcRenderTiles();
    mcUpdateRunBtn();
  });

  document.getElementById('mcRunBtn').addEventListener('click', () => {
    if (mcRunning) return;
    mcStartSimulation();
  });

  // --- Open the modal and populate tiles ---
  function mcOpenModal() {
    const notReady = document.getElementById('mcNotReady');
    const main = document.getElementById('mcMain');

    // Check if we're in a valid state for Monte Carlo
    if (!session || session.phase !== PHASE_PLAYING) {
      notReady.style.display = 'block';
      notReady.textContent = 'Monte Carlo is available during the play phase. Start a hand first.';
      main.style.display = 'none';
      document.getElementById('mcBackdrop').style.display = 'flex';
      return;
    }

    const g = session.game;
    const hand = g.hands[0];
    if (!hand || hand.length === 0) {
      notReady.style.display = 'block';
      notReady.textContent = 'No tiles in your hand.';
      main.style.display = 'none';
      document.getElementById('mcBackdrop').style.display = 'flex';
      return;
    }

    notReady.style.display = 'none';
    main.style.display = 'block';

    // Copy P1's current hand
    mcPlayerHand = hand.map(t => [t[0], t[1]]);
    mcSelectedOrder = [];

    mcRenderTiles();
    mcUpdateRunBtn();

    // Clear previous results
    document.getElementById('mcResults').style.display = 'none';
    document.getElementById('mcResults').innerHTML = '';
    document.getElementById('mcProgress').style.display = 'none';

    document.getElementById('mcBackdrop').style.display = 'flex';
  }

  // --- Render tile selection UI ---
  function mcRenderTiles() {
    const container = document.getElementById('mcTileSelect');
    container.innerHTML = '';

    mcPlayerHand.forEach((tile, idx) => {
      const orderPos = mcSelectedOrder.indexOf(idx);
      const isSelected = orderPos !== -1;

      const tileDiv = document.createElement('div');
      tileDiv.style.cssText = 'position:relative;width:56px;height:72px;border-radius:8px;cursor:pointer;display:flex;flex-direction:column;align-items:center;justify-content:center;font-weight:700;font-size:16px;color:#fff;user-select:none;transition:transform 0.15s,box-shadow 0.15s;';

      if (isSelected) {
        tileDiv.style.background = 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)';
        tileDiv.style.boxShadow = '0 4px 12px rgba(34,197,94,0.5), inset 0 1px 0 rgba(255,255,255,0.3)';
        tileDiv.style.transform = 'scale(1.05)';
        tileDiv.style.border = '2px solid rgba(255,255,255,0.5)';
      } else {
        tileDiv.style.background = 'linear-gradient(135deg, rgba(255,255,255,0.2) 0%, rgba(255,255,255,0.08) 100%)';
        tileDiv.style.boxShadow = '0 2px 8px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.15)';
        tileDiv.style.border = '2px solid rgba(255,255,255,0.2)';
      }

      // Tile pips display
      const topPip = document.createElement('div');
      topPip.textContent = tile[0];
      topPip.style.cssText = 'font-size:18px;line-height:1;';
      const divider = document.createElement('div');
      divider.style.cssText = 'width:70%;height:2px;background:rgba(255,255,255,0.4);margin:3px 0;';
      const botPip = document.createElement('div');
      botPip.textContent = tile[1];
      botPip.style.cssText = 'font-size:18px;line-height:1;';

      tileDiv.appendChild(topPip);
      tileDiv.appendChild(divider);
      tileDiv.appendChild(botPip);

      // Order badge
      if (isSelected) {
        const badge = document.createElement('div');
        badge.textContent = String(orderPos + 1);
        badge.style.cssText = 'position:absolute;top:-6px;right:-6px;width:20px;height:20px;border-radius:50%;background:#fbbf24;color:#000;font-size:11px;font-weight:900;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 4px rgba(0,0,0,0.3);';
        tileDiv.appendChild(badge);
      }

      tileDiv.addEventListener('click', () => {
        if (mcRunning) return;
        const existingPos = mcSelectedOrder.indexOf(idx);
        if (existingPos !== -1) {
          // Deselect: remove this and all after it
          mcSelectedOrder.splice(existingPos);
        } else if (mcSelectedOrder.length < mcPlayerHand.length) {
          mcSelectedOrder.push(idx);
        }
        mcRenderTiles();
        mcUpdateRunBtn();
      });

      container.appendChild(tileDiv);
    });
  }

  // --- Update Run button state ---
  function mcUpdateRunBtn() {
    const btn = document.getElementById('mcRunBtn');
    const allSelected = mcSelectedOrder.length === mcPlayerHand.length;
    btn.disabled = !allSelected;
    btn.style.opacity = allSelected ? '1' : '0.5';
  }

  // --- Start simulation ---
  function mcStartSimulation() {
    if (mcSelectedOrder.length !== mcPlayerHand.length) return;
    mcRunning = true;

    const numSims = parseInt(document.getElementById('mcSimCount').value) || 500;
    const progressDiv = document.getElementById('mcProgress');
    const progressText = document.getElementById('mcProgressText');
    const progressBar = document.getElementById('mcProgressBar');
    const resultsDiv = document.getElementById('mcResults');

    progressDiv.style.display = 'block';
    resultsDiv.style.display = 'none';
    resultsDiv.innerHTML = '';
    progressBar.style.width = '0%';
    progressText.textContent = 'Preparing simulation...';

    // Disable controls during run
    document.getElementById('mcRunBtn').disabled = true;
    document.getElementById('mcRunBtn').style.opacity = '0.5';

    // Gather game state
    const g = session.game;
    const trumpSuit = g.trump_suit;
    const trumpMode = g.trump_mode;
    const contract = session.contract || "NORMAL";
    const bid = session.current_bid || 34;
    const activePlayers = g.active_players.slice();
    const bidWinnerSeat = session.bid_winner_seat !== undefined ? session.bid_winner_seat : 0;

    // Build remaining tile pool (all tiles minus P1's hand)
    const allTiles = allDominoesForSet(g.max_pip);
    const handSet = new Set(mcPlayerHand.map(t => t[0] + ',' + t[1]));
    const remainingPool = allTiles.filter(t => !handSet.has(t[0] + ',' + t[1]));

    // Results accumulators
    const results = {
      total: numSims,
      keptControl: 0, keptControlBidMade: 0,
      lostToPartner: 0, lostToPartnerBidMade: 0,
      lostToOpponent: 0, lostToOpponentBidMade: 0,
      totalBidMade: 0,
      scoreWhenMade: 0, scoreWhenFailed: 0,
      madeCount: 0, failedCount: 0,
      setCount: 0,
      nelloWon: 0, nelloLost: 0,
      trickControlLost: new Array(7).fill(0)
    };

    let simsDone = 0;
    const BATCH_SIZE = 25;

    function runBatch() {
      const batchEnd = Math.min(simsDone + BATCH_SIZE, numSims);

      for (let sim = simsDone; sim < batchEnd; sim++) {
        runOneSim(results, mcPlayerHand, mcSelectedOrder, remainingPool,
                  trumpSuit, trumpMode, contract, bid, activePlayers, bidWinnerSeat);
      }

      simsDone = batchEnd;
      const pct = Math.round((simsDone / numSims) * 100);
      progressBar.style.width = pct + '%';
      progressText.textContent = 'Running simulation ' + simsDone + '/' + numSims + '...';

      if (simsDone < numSims) {
        setTimeout(runBatch, 0);
      } else {
        // Done
        mcRunning = false;
        progressDiv.style.display = 'none';
        mcDisplayResults(results, contract);
        mcUpdateRunBtn();
      }
    }

    setTimeout(runBatch, 10);
  }

  // --- Run one simulation ---
  function runOneSim(results, playerHand, playOrder, remainingPool,
                     trumpSuit, trumpMode, contract, bid, activePlayers, bidWinnerSeat) {
    // Shuffle remaining tiles and distribute
    const pool = remainingPool.slice();
    shuffleInPlace(pool);

    const hands = new Array(6);
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
    const sim = new GameStateV6_4g(6, 7, 6);
    sim.set_hands(hands, bidWinnerSeat);
    if (trumpMode === "NONE") {
      sim.set_trump_suit(null);
    } else if (trumpMode === "DOUBLES") {
      sim.set_trump_suit("DOUBLES");
    } else {
      sim.set_trump_suit(trumpSuit);
    }
    sim.set_active_players(activePlayers);

    // Track control
    let inControl = true;
    let controlLostTo = null;  // 'partner' or 'opponent'
    let controlLostTrick = -1;
    let leadOrderIdx = 0;  // Next tile in P1's preferred order to lead

    // Play up to 6 tricks
    let safety = 0;
    while (!sim.hand_is_over() && safety < 100) {
      safety++;
      const currentSeat = sim.current_player;
      const isLeading = sim.current_trick.length === 0;
      let tileIdx = -1;

      if (currentSeat === 0 && inControl && isLeading && leadOrderIdx < playOrder.length) {
        // P1 leads in preferred order
        const preferredTile = playerHand[playOrder[leadOrderIdx]];
        const hand = sim.hands[0];
        tileIdx = hand.findIndex(t => t[0] === preferredTile[0] && t[1] === preferredTile[1]);
        if (tileIdx === -1) {
          // Tile not found (already played?), fallback to AI
          try { tileIdx = choose_tile_ai(sim, 0, contract, false, bid); } catch(_) { tileIdx = 0; }
        }
        leadOrderIdx++;
      } else {
        // AI plays for everyone else, or for P1 when not in control / following
        try {
          tileIdx = choose_tile_ai(sim, currentSeat, contract, false, bid);
        } catch(_) {
          const legal = sim.legal_indices_for_player(currentSeat);
          tileIdx = legal.length > 0 ? legal[0] : 0;
        }
      }

      // Validate tileIdx
      const legal = sim.legal_indices_for_player(currentSeat);
      if (legal.length === 0) break;
      if (!legal.includes(tileIdx)) {
        tileIdx = legal[0];
      }

      let result;
      try {
        result = sim.play_tile(currentSeat, tileIdx);
      } catch(e) {
        break;
      }

      // Check if trick completed (result[2] === true means trick finished)
      if (result && result[2]) {
        const winner = result[1];
        const winnerTeam = sim.team_of(winner);
        const p1Team = 0;  // seat 0 is team 0

        if (inControl && winner !== 0) {
          // P1 lost control
          inControl = false;
          if (winnerTeam === p1Team) {
            controlLostTo = 'partner';
          } else {
            controlLostTo = 'opponent';
          }
          controlLostTrick = sim.trick_number;  // trick_number was already incremented
          if (controlLostTrick >= 1 && controlLostTrick <= 6) {
            results.trickControlLost[controlLostTrick]++;
          }
        }

        // Check for early set
        const bidderTeamIndex = (bidWinnerSeat % 2 === 0) ? 0 : 1;
        const bidderPoints = sim.team_points[bidderTeamIndex];
        const totalAwarded = sim.team_points[0] + sim.team_points[1];
        const pointsRemaining = 51 - totalAwarded;
        if (contract !== "NELLO" && bidderPoints + pointsRemaining < bid) {
          break;  // Set - no need to continue
        }
        // Check if bid already made (early exit)
        if (contract !== "NELLO" && bidderPoints >= bid) {
          break;
        }
      }
    }

    // Evaluate final result
    const bidderTeamIndex = (bidWinnerSeat % 2 === 0) ? 0 : 1;
    const bidderPoints = sim.team_points[bidderTeamIndex];

    let bidMade = false;
    if (contract === "NELLO") {
      // Nello: bidder's team must win 0 tricks
      bidMade = sim.tricks_team[bidderTeamIndex].length === 0;
      if (bidMade) results.nelloWon++;
      else results.nelloLost++;
    } else {
      bidMade = bidderPoints >= bid;
    }

    // Classify control outcome
    if (inControl) {
      results.keptControl++;
      if (bidMade) results.keptControlBidMade++;
    } else if (controlLostTo === 'partner') {
      results.lostToPartner++;
      if (bidMade) results.lostToPartnerBidMade++;
    } else {
      results.lostToOpponent++;
      if (bidMade) results.lostToOpponentBidMade++;
    }

    if (bidMade) {
      results.totalBidMade++;
      results.scoreWhenMade += bidderPoints;
      results.madeCount++;
    } else {
      results.scoreWhenFailed += bidderPoints;
      results.failedCount++;
      if (contract !== "NELLO") {
        const totalAwarded = sim.team_points[0] + sim.team_points[1];
        const pointsRemaining = 51 - totalAwarded;
        if (bidderPoints + pointsRemaining < bid) {
          results.setCount++;
        }
      }
    }
  }

  // --- Display results ---
  function mcDisplayResults(r, contract) {
    const div = document.getElementById('mcResults');
    div.style.display = 'block';

    // Build play order string
    const orderStr = mcSelectedOrder.map(idx => {
      const t = mcPlayerHand[idx];
      return t[0] + '-' + t[1];
    }).join(', ');

    // Trump info
    const g = session.game;
    let trumpStr = 'NT';
    if (g.trump_mode === 'PIP') trumpStr = g.trump_suit + 's';
    else if (g.trump_mode === 'DOUBLES') trumpStr = 'Doubles';

    const bid = session.current_bid || 0;
    const pct = (n, d) => d > 0 ? (n / d * 100).toFixed(1) + '%' : '0%';
    const avg = (s, c) => c > 0 ? (s / c).toFixed(1) : '--';

    let html = '';

    // Header
    html += '<div style="background:rgba(0,0,0,0.2);border-radius:10px;padding:10px;margin-bottom:8px;">';
    html += '<div style="font-size:13px;font-weight:700;color:#fbbf24;margin-bottom:6px;">MONTE CARLO RESULTS (' + r.total + ' simulations)</div>';
    html += '<div style="font-size:11px;color:rgba(255,255,255,0.7);margin-bottom:3px;">Play order: ' + orderStr + '</div>';
    html += '<div style="font-size:11px;color:rgba(255,255,255,0.7);">Trump: ' + trumpStr + ' | Bid: ' + bid + (contract === 'NELLO' ? ' | Nel-O' : '') + '</div>';
    html += '</div>';

    if (contract === 'NELLO') {
      // Nello results
      html += '<div style="background:rgba(0,0,0,0.15);border-radius:10px;padding:10px;margin-bottom:8px;">';
      html += '<div style="font-size:12px;font-weight:700;color:#60a5fa;margin-bottom:8px;">NEL-O RESULTS</div>';
      html += mcResultRow('Won (0 tricks taken)', r.nelloWon, r.total, '#4ade80');
      html += mcResultRow('Lost (caught a trick)', r.nelloLost, r.total, '#f87171');
      html += '</div>';
    } else {
      // Control analysis
      html += '<div style="background:rgba(0,0,0,0.15);border-radius:10px;padding:10px;margin-bottom:8px;">';
      html += '<div style="font-size:12px;font-weight:700;color:#60a5fa;margin-bottom:8px;">CONTROL ANALYSIS</div>';

      // Kept full control
      html += mcResultRow('Kept full control', r.keptControl, r.total, '#4ade80');
      if (r.keptControl > 0) {
        html += mcSubRow('Bid made', r.keptControlBidMade, r.keptControl);
      }

      // Lost to partner
      html += mcResultRow('Lost control to PARTNER', r.lostToPartner, r.total, '#fbbf24');
      if (r.lostToPartner > 0) {
        html += mcSubRow('Bid made', r.lostToPartnerBidMade, r.lostToPartner);
      }

      // Lost to opponent
      html += mcResultRow('Lost control to OPPONENT', r.lostToOpponent, r.total, '#f87171');
      if (r.lostToOpponent > 0) {
        html += mcSubRow('Bid made', r.lostToOpponentBidMade, r.lostToOpponent);
      }
      html += '</div>';

      // Overall
      html += '<div style="background:rgba(0,0,0,0.15);border-radius:10px;padding:10px;margin-bottom:8px;">';
      html += '<div style="font-size:12px;font-weight:700;color:#60a5fa;margin-bottom:8px;">OVERALL</div>';
      html += mcResultRow('Bid made', r.totalBidMade, r.total, '#4ade80');
      html += mcResultRow('Set (early loss)', r.setCount, r.total, '#f87171');
      html += '<div style="display:flex;justify-content:space-between;font-size:11px;color:rgba(255,255,255,0.7);margin-top:6px;padding-top:6px;border-top:1px solid rgba(255,255,255,0.1);">';
      html += '<span>Avg score when made: ' + avg(r.scoreWhenMade, r.madeCount) + '</span>';
      html += '<span>Avg score when failed: ' + avg(r.scoreWhenFailed, r.failedCount) + '</span>';
      html += '</div>';
      html += '</div>';

      // Trick where control was lost
      let hasLostData = false;
      for (let i = 1; i <= 6; i++) {
        if (r.trickControlLost[i] > 0) { hasLostData = true; break; }
      }
      if (hasLostData) {
        html += '<div style="background:rgba(0,0,0,0.15);border-radius:10px;padding:10px;">';
        html += '<div style="font-size:12px;font-weight:700;color:#60a5fa;margin-bottom:8px;">CONTROL LOST ON TRICK</div>';
        for (let i = 1; i <= 6; i++) {
          if (r.trickControlLost[i] > 0) {
            const totalLost = r.lostToPartner + r.lostToOpponent;
            html += mcResultRow('Trick ' + i, r.trickControlLost[i], totalLost, '#a78bfa');
          }
        }
        html += '</div>';
      }
    }

    div.innerHTML = html;
  }

  function mcResultRow(label, count, total, color) {
    const pct = total > 0 ? (count / total * 100).toFixed(1) : '0.0';
    return '<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">' +
      '<div style="flex:1;font-size:11px;color:rgba(255,255,255,0.9);">' + label + '</div>' +
      '<div style="font-size:11px;font-weight:700;color:' + color + ';">' + count + '/' + total + ' (' + pct + '%)</div>' +
      '</div>';
  }

  function mcSubRow(label, count, total) {
    const pct = total > 0 ? (count / total * 100).toFixed(1) : '0.0';
    return '<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;padding-left:16px;">' +
      '<div style="flex:1;font-size:10px;color:rgba(255,255,255,0.6);">' + label + '</div>' +
      '<div style="font-size:10px;color:rgba(255,255,255,0.6);">' + count + '/' + total + ' (' + pct + '%)</div>' +
      '</div>';
  }

})();"""

    html = patch(html, old_listener_anchor, new_listener_block, "Add Monte Carlo JS engine and event listeners")

    # =========================================================================
    # DONE — Write output
    # =========================================================================
    write_file(OUTPUT, html)
    print(f"\nWrote {len(html)} bytes to {OUTPUT}")
    print("Build V10_33 complete.")

if __name__ == "__main__":
    main()
