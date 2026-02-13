#!/usr/bin/env python3
"""
Build V10_36: Pass & Play Feature
- Setup modal: checkboxes for human players, new/continue, privacy toggle
- Board rotation: visual perspective shift when human player's turn
- Handoff screen: privacy mode hides tiles between turns
- AI plays for non-human seats, human plays for checked seats
"""

import re, sys

SRC = "TN51_Dominoes_V10_35.html"
DST = "TN51_Dominoes_V10_36.html"

def read(f):
    with open(f, encoding="utf-8") as fh:
        return fh.read()

def write(f, s):
    with open(f, "w", encoding="utf-8") as fh:
        fh.write(s)

html = read(SRC)
original_len = len(html)
patches_ok = 0

def patch(label, old, new, count=1):
    global html, patches_ok
    n = html.count(old)
    if n < count:
        print(f"  FAIL: {label} (found {n}, need {count})")
        sys.exit(1)
    if count == 0:
        # Replace all
        html = html.replace(old, new)
        print(f"  OK: {label} (replaced all {n})")
    else:
        for _ in range(count):
            html = html.replace(old, new, 1)
        print(f"  OK: {label}")
    patches_ok += 1


# ============================================================================
# PATCH 1: Add Pass & Play modal HTML (after mcBackdrop modal, before </body>)
# ============================================================================

PP_MODAL_HTML = """
<!-- Pass & Play Setup Modal -->
<div id="ppBackdrop" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.7);z-index:1500;align-items:center;justify-content:center;font-family:system-ui,-apple-system,sans-serif;">
  <div style="background:linear-gradient(135deg,#1a2332 0%,#0f1923 100%);border-radius:16px;padding:24px;max-width:360px;width:90%;color:#fff;box-shadow:0 20px 60px rgba(0,0,0,0.5);border:1px solid rgba(255,255,255,0.1);">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
      <h3 style="margin:0;font-size:18px;color:#60a5fa;">Pass & Play Setup</h3>
      <button id="ppCloseBtn" style="background:none;border:none;color:#aaa;font-size:22px;cursor:pointer;padding:0 4px;">&times;</button>
    </div>

    <div style="margin-bottom:16px;">
      <div style="font-size:13px;color:#9ca3af;margin-bottom:8px;">Select human players:</div>
      <div id="ppPlayerGrid" style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;">
      </div>
    </div>

    <div style="margin-bottom:16px;display:flex;align-items:center;gap:10px;padding:10px;background:rgba(255,255,255,0.05);border-radius:8px;">
      <label style="display:flex;align-items:center;gap:8px;cursor:pointer;font-size:13px;color:#d1d5db;">
        <input type="checkbox" id="ppPrivacy" checked style="width:18px;height:18px;accent-color:#60a5fa;">
        <span><strong>Privacy Mode</strong> — hide tiles between turns<br><span style="font-size:11px;color:#9ca3af;">(For passing device to another person)</span></span>
      </label>
    </div>

    <div style="display:flex;gap:10px;">
      <button id="ppNewGame" style="flex:1;padding:12px;border:none;border-radius:10px;font-size:14px;font-weight:700;cursor:pointer;background:linear-gradient(135deg,#22c55e,#16a34a);color:#fff;">New Game</button>
      <button id="ppContinue" style="flex:1;padding:12px;border:none;border-radius:10px;font-size:14px;font-weight:700;cursor:pointer;background:linear-gradient(135deg,#3b82f6,#2563eb);color:#fff;">Continue Game</button>
    </div>
  </div>
</div>

<!-- Pass & Play Handoff Screen -->
<div id="ppHandoff" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.85);z-index:1400;align-items:center;justify-content:center;flex-direction:column;font-family:system-ui,-apple-system,sans-serif;">
  <div style="text-align:center;">
    <div id="ppHandoffLabel" style="font-size:28px;font-weight:800;color:#60a5fa;margin-bottom:8px;">Player 4's Turn</div>
    <div id="ppHandoffPhase" style="font-size:14px;color:#9ca3af;margin-bottom:24px;">Bidding Phase</div>
    <button id="ppHandoffBtn" style="padding:16px 40px;border:none;border-radius:12px;font-size:16px;font-weight:700;cursor:pointer;background:linear-gradient(135deg,#22c55e,#16a34a);color:#fff;box-shadow:0 8px 24px rgba(34,197,94,0.3);">Show My Hand</button>
  </div>
</div>
"""

patch("PATCH 1: Add PP modal HTML",
      "<!-- Bidding Overlay -->",
      PP_MODAL_HTML + "\n<!-- Bidding Overlay -->")


# ============================================================================
# PATCH 2: Add Pass & Play state variables and rotation system
# Insert after the existing PASS_AND_PLAY_MODE declaration
# ============================================================================

PP_STATE_JS = """
// --- Pass & Play V10_36 ---
let ppHumanSeats = new Set([0]);  // Which seats are human (default: just P1)
let ppPrivacyMode = true;         // Show handoff screen between turns
let ppActiveViewSeat = 0;         // Which seat's perspective is currently shown (visual rotation)
let ppRotationOffset = 0;         // How many positions board is rotated (0=normal, 3=P4 in P1 spot)

// Convert a game seat to visual player number based on current rotation
function ppVisualPlayer(seat) {
  // When ppRotationOffset=0, seat 0 -> Player 1 (normal)
  // When ppRotationOffset=3 (P4 viewing), seat 3 -> Player 1 position, seat 0 -> Player 4 position
  return ((seat - ppRotationOffset + 6) % 6) + 1;
}

// Convert visual player number back to game seat
function ppSeatFromVisual(visualPlayer) {
  return (visualPlayer - 1 + ppRotationOffset) % 6;
}

// Check if a seat is human-controlled
function ppIsHuman(seat) {
  if (!PASS_AND_PLAY_MODE) return seat === 0;
  return ppHumanSeats.has(seat);
}

// Rotate the board to show from a specific seat's perspective
function ppRotateBoard(viewingSeat) {
  ppActiveViewSeat = viewingSeat;
  ppRotationOffset = viewingSeat;  // e.g., seat 3 -> offset 3

  // Update player indicator labels
  for (let seat = 0; seat < 6; seat++) {
    const visualP = ppVisualPlayer(seat);
    const el = document.getElementById('playerIndicator' + visualP);
    if (el) {
      el.textContent = 'P' + (seat + 1);  // Show real player number
      // Update team color
      el.classList.remove('team1', 'team2');
      el.classList.add(seat % 2 === 0 ? 'team1' : 'team2');
    }
  }

  // Reposition all hand sprites to rotated positions
  for (let seat = 0; seat < 6; seat++) {
    const seatSprites = sprites[seat];
    if (!seatSprites) continue;
    const visualP = ppVisualPlayer(seat);
    const isFocusSeat = (seat === viewingSeat);

    seatSprites.forEach((data, h) => {
      if (!data || !data.sprite) return;
      const pos = getHandPosition(visualP, h);
      if (pos) {
        data.sprite.setPose(pos);
        // Face up only for the viewing seat
        if (isFocusSeat) {
          data.sprite.setFaceUp(true);
        } else {
          data.sprite.setFaceUp(false);
        }
      }
    });
  }

  // Reposition played tiles in current trick
  for (const played of playedThisTrick) {
    if (played && played.sprite) {
      const visualP = ppVisualPlayer(played.seat);
      const pos = getPlayedPosition(visualP);
      if (pos) {
        played.sprite.setPose(pos);
      }
    }
  }

  // Reposition player indicators
  ppRepositionIndicators();

  // Reposition placeholders
  ppRepositionPlaceholders();
}

// Reposition player indicators based on rotation
function ppRepositionIndicators() {
  const indicatorPositions = {
    1: { xN: 0.50, yN: 0.72 },
    2: { xN: 0.32, yN: 0.68 },
    3: { xN: 0.32, yN: 0.52 },
    4: { xN: 0.50, yN: 0.47 },
    5: { xN: 0.68, yN: 0.52 },
    6: { xN: 0.68, yN: 0.68 }
  };

  for (let seat = 0; seat < 6; seat++) {
    const visualP = ppVisualPlayer(seat);
    const el = document.getElementById('playerIndicator' + visualP);
    if (el) {
      const pos = indicatorPositions[visualP];
      const px = normToPx(pos.xN, pos.yN);
      el.style.left = (px.x - 14) + 'px';
      el.style.top = (px.y - 14) + 'px';
    }
  }
}

// Reposition placeholders based on rotation
function ppRepositionPlaceholders() {
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
}

// Reset rotation to normal (P1 perspective)
function ppResetRotation() {
  ppRotationOffset = 0;
  ppActiveViewSeat = 0;

  // Reset indicator labels
  for (let p = 1; p <= 6; p++) {
    const el = document.getElementById('playerIndicator' + p);
    if (el) {
      el.textContent = 'P' + p;
      el.classList.remove('team1', 'team2');
      el.classList.add((p - 1) % 2 === 0 ? 'team1' : 'team2');
    }
  }

  positionPlayerIndicators();
}

// Show handoff screen for a seat
function ppShowHandoff(seat, phaseName) {
  document.getElementById('ppHandoffLabel').textContent = 'Player ' + (seat + 1) + "'s Turn";
  document.getElementById('ppHandoffPhase').textContent = phaseName || '';
  document.getElementById('ppHandoff').style.display = 'flex';
}

// Hide handoff screen
function ppHideHandoff() {
  document.getElementById('ppHandoff').style.display = 'none';
}

// Hide all tiles (face down) - for privacy transitions
function ppHideAllTiles() {
  for (let seat = 0; seat < 6; seat++) {
    const seatSprites = sprites[seat];
    if (!seatSprites) continue;
    seatSprites.forEach(data => {
      if (data && data.sprite) {
        data.sprite.setFaceUp(false);
      }
    });
  }
}

// Transition to next human player's turn in pass & play
function ppTransitionToSeat(seat, phaseName) {
  if (!PASS_AND_PLAY_MODE) return;

  if (ppPrivacyMode) {
    ppHideAllTiles();
    ppShowHandoff(seat, phaseName);
    // Handoff button click will call ppCompleteTransition
  } else {
    ppCompleteTransition(seat);
  }
}

// Complete the transition - rotate board and enable play
function ppCompleteTransition(seat) {
  ppHideHandoff();
  ppRotateBoard(seat);

  // Enable click handlers for the active seat
  ppEnableClicksForSeat(seat);
}

// Add click handlers to a specific seat's sprites
function ppEnableClicksForSeat(seat) {
  // First remove ALL click handlers
  for (let s = 0; s < 6; s++) {
    const seatSprites = sprites[s];
    if (!seatSprites) continue;
    seatSprites.forEach(data => {
      if (data && data.sprite) {
        data.sprite.classList.remove('clickable');
      }
    });
  }

  // Add clickable class to the active seat's sprites
  const seatSprites = sprites[seat];
  if (!seatSprites) return;
  seatSprites.forEach(data => {
    if (data && data.sprite) {
      data.sprite.classList.add('clickable');
    }
  });
}

// Update valid states for a specific seat (generalized from P1-only)
function ppUpdateValidStates(seat) {
  if (session.phase !== PHASE_PLAYING) return;
  if (session.game.current_player !== seat) return;

  const hand = session.game.hands[seat] || [];
  const legalIndices = session.game.legal_indices_for_player(seat);
  const legalTiles = legalIndices.map(i => hand[i]);

  const seatSprites = sprites[seat] || [];
  seatSprites.forEach((data, idx) => {
    if (data && data.sprite && data.tile) {
      const isValid = legalTiles.some(lt =>
        lt && ((lt[0] === data.tile[0] && lt[1] === data.tile[1]) ||
               (lt[0] === data.tile[1] && lt[1] === data.tile[0]))
      );
      const isTrump = session.game._is_trump_tile(data.tile);
      data.sprite.setState(isTrump, isValid);
    }
  });
}
"""

patch("PATCH 2: Add PP state variables and rotation system",
      "let PASS_AND_PLAY_MODE = false;",
      "let PASS_AND_PLAY_MODE = false;\n" + PP_STATE_JS)


# ============================================================================
# PATCH 3: Replace the simple Pass & Play menu toggle with setup modal opener
# ============================================================================

patch("PATCH 3: Replace PP menu toggle",
      """document.getElementById('menuPassPlay').addEventListener('click', () => {
  PASS_AND_PLAY_MODE = !PASS_AND_PLAY_MODE;
  document.getElementById('menuPassPlay').textContent = `Pass & Play: ${PASS_AND_PLAY_MODE ? 'ON' : 'OFF'}`;
  document.getElementById('settingsMenu').classList.remove('open');
});""",
      """document.getElementById('menuPassPlay').addEventListener('click', () => {
  document.getElementById('settingsMenu').classList.remove('open');
  ppOpenSetupModal();
});""")


# ============================================================================
# PATCH 4: Add PP setup modal logic (event handlers + open/close)
# Insert before the closing </script> tag (at the end of the main script block)
# We'll insert before the Monte Carlo IIFE
# ============================================================================

PP_SETUP_JS = """
// ============================================================================
// PASS & PLAY SETUP MODAL (V10_36)
// ============================================================================

function ppOpenSetupModal() {
  const grid = document.getElementById('ppPlayerGrid');
  grid.innerHTML = '';

  for (let seat = 0; seat < 6; seat++) {
    const p = seat + 1;
    const team = seat % 2 === 0 ? 1 : 2;
    const teamColor = team === 1 ? '#3b82f6' : '#ef4444';
    const checked = ppHumanSeats.has(seat) ? 'checked' : '';

    const div = document.createElement('div');
    div.style.cssText = 'display:flex;align-items:center;gap:6px;padding:8px 10px;border-radius:8px;background:rgba(255,255,255,0.05);cursor:pointer;';
    div.innerHTML = `
      <input type="checkbox" id="ppSeat${seat}" ${checked} style="width:16px;height:16px;accent-color:${teamColor};">
      <span style="font-size:13px;color:${teamColor};font-weight:700;">P${p}</span>
      <span style="font-size:10px;color:#6b7280;">T${team}</span>
    `;
    div.addEventListener('click', (e) => {
      if (e.target.tagName !== 'INPUT') {
        const cb = div.querySelector('input');
        cb.checked = !cb.checked;
      }
    });
    grid.appendChild(div);
  }

  document.getElementById('ppPrivacy').checked = ppPrivacyMode;
  document.getElementById('ppBackdrop').style.display = 'flex';
}

function ppCloseSetupModal() {
  document.getElementById('ppBackdrop').style.display = 'none';
}

function ppActivateFromModal(startNew) {
  // Read selected human seats
  ppHumanSeats = new Set();
  for (let seat = 0; seat < 6; seat++) {
    const cb = document.getElementById('ppSeat' + seat);
    if (cb && cb.checked) ppHumanSeats.add(seat);
  }

  // Need at least one human
  if (ppHumanSeats.size === 0) {
    ppHumanSeats.add(0);
  }

  ppPrivacyMode = document.getElementById('ppPrivacy').checked;

  // Enable pass and play
  PASS_AND_PLAY_MODE = true;
  document.getElementById('menuPassPlay').textContent = 'Pass & Play: ON';

  ppCloseSetupModal();

  // Hide all tiles immediately
  ppHideAllTiles();

  if (startNew) {
    ppResetRotation();
    startNewHand();
  } else {
    // Continue current game — find whose turn it is and transition
    ppContinueFromCurrentState();
  }
}

function ppContinueFromCurrentState() {
  const seat = session.game.current_player;
  if (ppIsHuman(seat)) {
    const phase = session.phase === PHASE_NEED_BID ? 'Bidding Phase' :
                  session.phase === PHASE_NEED_TRUMP ? 'Choose Trump' :
                  session.phase === PHASE_PLAYING ? 'Play Phase' : '';
    ppTransitionToSeat(seat, phase);
  } else {
    // AI seat — run AI until we hit a human
    ppResetRotation();
    maybeAIKick();
  }
}

// Disable pass and play
function ppDeactivate() {
  PASS_AND_PLAY_MODE = false;
  ppResetRotation();
  ppHideHandoff();
  document.getElementById('menuPassPlay').textContent = 'Pass & Play: OFF';

  // Reposition everything to normal
  for (let seat = 0; seat < 6; seat++) {
    const seatSprites = sprites[seat];
    if (!seatSprites) continue;
    const playerNum = seatToPlayer(seat);
    seatSprites.forEach((data, h) => {
      if (!data || !data.sprite) return;
      const pos = getHandPosition(playerNum, h);
      if (pos) {
        data.sprite.setPose(pos);
        data.sprite.setFaceUp(seat === 0);
      }
    });
  }

  // Re-enable P1 clicks if it's P1's turn
  if (session.phase === PHASE_PLAYING && session.game.current_player === 0) {
    enablePlayer1Clicks();
    updatePlayer1ValidStates();
  }
}

// Event listeners for PP modal
document.getElementById('ppCloseBtn').addEventListener('click', ppCloseSetupModal);
document.getElementById('ppNewGame').addEventListener('click', () => ppActivateFromModal(true));
document.getElementById('ppContinue').addEventListener('click', () => ppActivateFromModal(false));

document.getElementById('ppHandoffBtn').addEventListener('click', () => {
  const seat = ppActiveViewSeat;
  // Find whose turn it actually is
  const currentSeat = session.game.current_player;
  // For bidding, use biddingState.currentBidder
  const activeSeat = session.phase === PHASE_NEED_BID && typeof biddingState !== 'undefined' && biddingState
    ? biddingState.currentBidder : currentSeat;
  ppCompleteTransition(activeSeat);

  // Resume the appropriate game flow
  if (session.phase === PHASE_NEED_BID) {
    showBidOverlay(true);
  } else if (session.phase === PHASE_NEED_TRUMP) {
    // Trump selection - enable domino clicks
    ppUpdateValidStates(activeSeat);
  } else if (session.phase === PHASE_PLAYING) {
    ppUpdateValidStates(activeSeat);
  }
});

"""

patch("PATCH 4: Add PP setup modal logic",
      "// ============================================================================\n// MONTE CARLO SIMULATION ENGINE (V10_33)",
      PP_SETUP_JS + "\n// ============================================================================\n// MONTE CARLO SIMULATION ENGINE (V10_33)")


# ============================================================================
# PATCH 5: Modify maybeAIKick to handle mixed human/AI in pass & play
# The current code returns immediately if PASS_AND_PLAY_MODE is true.
# We need it to check if current player is human, and if not, run AI.
# ============================================================================

patch("PATCH 5: Modify maybeAIKick for mixed human/AI",
      """function maybeAIKick(){
  if(session.phase !== PHASE_PLAYING) return;
  if(session.game.current_player === 0) return;
  if(PASS_AND_PLAY_MODE) return;

  // Schedule AI to play
  setTimeout(() => aiPlayTurn(), 500);
}""",
      """function maybeAIKick(){
  if(session.phase !== PHASE_PLAYING) return;
  const seat = session.game.current_player;

  if(PASS_AND_PLAY_MODE) {
    if(ppIsHuman(seat)) {
      // It's a human player's turn - transition to them
      ppTransitionToSeat(seat, 'Play Phase');
      return;
    }
    // AI seat in pass & play - let AI play
    setTimeout(() => ppAIPlayLoop(), 300);
    return;
  }

  // Normal mode
  if(seat === 0) return;
  setTimeout(() => aiPlayTurn(), 500);
}""")


# ============================================================================
# PATCH 6: Add ppAIPlayLoop - runs AI for non-human seats, stops at human seats
# Insert after maybeAIKick
# ============================================================================

PP_AI_LOOP = """

// Pass & Play AI loop - plays AI seats until a human seat is reached
async function ppAIPlayLoop() {
  if (isAnimating) return;
  isAnimating = true;

  try {
    while (session.phase === PHASE_PLAYING) {
      const seat = session.game.current_player;

      // If this seat is human, stop and transition to them
      if (ppIsHuman(seat)) {
        break;
      }

      // AI plays
      const hand = session.game.hands[seat] || [];
      const aiRec = choose_tile_ai(session.game, seat, session.contract, true, session.current_bid);
      const gameHandIdx = aiRec.index;

      if (gameHandIdx < 0) break;

      const tileToPlay = aiRec.tile || hand[gameHandIdx];
      setStatus('P' + (seat + 1) + ' plays...');

      const variedDelay = ANIM.OPPONENT_PLAY_DELAY * (1 + (Math.random() * 2 - 1) * 0.15);
      await new Promise(r => setTimeout(r, variedDelay));

      // Find sprite
      const seatSprites = sprites[seat] || [];
      let spriteIdx = -1;
      for (let i = 0; i < seatSprites.length; i++) {
        const sd = seatSprites[i];
        if (sd && sd.tile) {
          if ((sd.tile[0] === tileToPlay[0] && sd.tile[1] === tileToPlay[1]) ||
              (sd.tile[0] === tileToPlay[1] && sd.tile[1] === tileToPlay[0])) {
            spriteIdx = i;
            break;
          }
        }
      }

      if (spriteIdx < 0) break;

      const isLead = session.game.current_trick.length === 0;
      const legalIndices = session.game.legal_indices_for_player(seat);
      const legalTiles = legalIndices.map(i => hand[i]).filter(t => t);
      let currentWinner = null;
      const trick = session.game.current_trick || [];
      if (trick.length > 0) {
        const ws = session.game._determine_trick_winner();
        currentWinner = { seat: ws, team: ws % 2 === 0 ? 1 : 2 };
      }

      try {
        session.play(seat, gameHandIdx);
      } catch(e) {
        console.log("PP AI play error:", e);
        break;
      }

      await playDomino(seat, spriteIdx, isLead, aiRec, { legalTiles, currentWinner });

      // Check trick complete
      if (session.game._sanitized_trick().length >= session.game.active_players.length) {
        await new Promise(r => setTimeout(r, 800));
        await collectToHistory();
        session.game.current_trick = [];

        if (session.maybe_finish_hand()) {
          setStatus(session.status);
          team1Score = session.game.team_points[0];
          team2Score = session.game.team_points[1];
          team1Marks = session.team_marks[0];
          team2Marks = session.team_marks[1];
          updateScoreDisplay();
          logEvent('HAND_END', { status: session.status });
          autoSave();
          setTimeout(() => showHandEndPopup(), 800);
          return;
        }
      }
    }

    // After loop: if current player is human, transition to them
    if (session.phase === PHASE_PLAYING && ppIsHuman(session.game.current_player)) {
      ppTransitionToSeat(session.game.current_player, 'Play Phase');
    }
  } finally {
    isAnimating = false;
  }
}
"""

patch("PATCH 6: Add ppAIPlayLoop",
      """function maybeAIKick(){
  if(session.phase !== PHASE_PLAYING) return;
  const seat = session.game.current_player;""",
      PP_AI_LOOP + """
function maybeAIKick(){
  if(session.phase !== PHASE_PLAYING) return;
  const seat = session.game.current_player;""")


# ============================================================================
# PATCH 7: Modify handlePlayer1Click to handle any human seat in PP mode
# Currently it only allows seat 0 to play. We need it to allow the active PP seat.
# The key guard is: if(session.game.current_player !== 0) return;
# ============================================================================

patch("PATCH 7a: Allow any human seat to click in PP mode (guard check)",
      """  if(session.phase !== PHASE_PLAYING){
    console.log("Click ignored - not in playing phase");
    return;
  }

  const spriteData = sprites[0][spriteSlotIndex];""",
      """  if(session.phase !== PHASE_PLAYING){
    console.log("Click ignored - not in playing phase");
    return;
  }

  // In PP mode, find which seat this sprite belongs to
  const ppClickSeat = PASS_AND_PLAY_MODE ? ppActiveViewSeat : 0;
  const spriteData = sprites[ppClickSeat][spriteSlotIndex];""")

# Fix the hand lookup to use ppClickSeat instead of hardcoded 0
patch("PATCH 7b: Use ppClickSeat for hand lookup",
      """  // Find this tile's index in the current game hand
  const hand = session.game.hands[0] || [];""",
      """  // Find this tile's index in the current game hand
  const hand = session.game.hands[ppClickSeat] || [];""")

# Fix the legal check to use ppClickSeat
patch("PATCH 7c: Use ppClickSeat for legal check",
      """  const legal = session.game.legal_indices_for_player(0);""",
      """  const legal = session.game.legal_indices_for_player(ppClickSeat);""")

# Fix the session.play call to use ppClickSeat
patch("PATCH 7d: Use ppClickSeat for play call",
      """  setStatus('You play...');

  // Capture context BEFORE playing (for accurate logging)
  const aiRec = choose_tile_ai(session.game, 0, session.contract, true, session.current_bid);
  const legalIndices = session.game.legal_indices_for_player(0);""",
      """  setStatus(PASS_AND_PLAY_MODE ? 'P' + (ppClickSeat + 1) + ' plays...' : 'You play...');

  // Capture context BEFORE playing (for accurate logging)
  const aiRec = choose_tile_ai(session.game, ppClickSeat, session.contract, true, session.current_bid);
  const legalIndices = session.game.legal_indices_for_player(ppClickSeat);""")

# Fix the session.play(0, ...) call
patch("PATCH 7e: Use ppClickSeat for session.play",
      """  const isLead = session.game.current_trick.length === 0;
  try {
    session.play(0, gameHandIndex);""",
      """  const isLead = session.game.current_trick.length === 0;
  try {
    session.play(ppClickSeat, gameHandIndex);""")

# Fix the playDomino call
patch("PATCH 7f: Use ppClickSeat for playDomino",
      """  await playDomino(0, spriteSlotIndex, isLead, aiRec, prePlayContext);

  // Check if trick is complete""",
      """  await playDomino(ppClickSeat, spriteSlotIndex, isLead, aiRec, prePlayContext);

  // Check if trick is complete""")


# ============================================================================
# PATCH 8: Fix sprite click registration in startNewHand
# Currently only seat 0 gets click handlers. In PP mode, all human seats need them.
# We'll make ALL sprites clickable (the guard in handlePlayer1Click filters by seat).
# ============================================================================

patch("PATCH 8: Make all sprites clickable in PP mode",
      """        if(p === 0){
          // Pass sprite element directly so click handler finds current position after sorting
          sprite.addEventListener('click', () => handlePlayer1Click(sprite));
          // Mobile touch support - use touchstart for immediate response
          sprite.addEventListener('touchstart', (e) => {
            e.preventDefault();
            e.stopPropagation();
            handlePlayer1Click(sprite);
          }, { passive: false });
        }""",
      """        if(p === 0 || (PASS_AND_PLAY_MODE && ppIsHuman(p))){
          // Pass sprite element directly so click handler finds current position after sorting
          sprite.addEventListener('click', () => handlePlayer1Click(sprite));
          // Mobile touch support - use touchstart for immediate response
          sprite.addEventListener('touchstart', (e) => {
            e.preventDefault();
            e.stopPropagation();
            handlePlayer1Click(sprite);
          }, { passive: false });
        }""")


# ============================================================================
# PATCH 9: Modify findSpriteSlotIndex to search all human seats in PP mode
# Currently it only searches sprites[0]. We need it to search the active seat.
# ============================================================================

# Find the findSpriteSlotIndex function
patch("PATCH 9: Fix findSpriteSlotIndex for PP mode",
      """function findSpriteSlotIndex(spriteElement){
  const p1Sprites = sprites[0] || [];
  for(let i = 0; i < p1Sprites.length; i++){
    const data = p1Sprites[i];
    if(!data) continue;
    // Handle both cases: data.sprite is the element directly (makeSprite)
    // or data.sprite has .el property (createDominoSprite)
    const spriteEl = data.sprite.el ? data.sprite.el : data.sprite;
    if(spriteEl === spriteElement){
      return i;
    }
  }
  return -1;
}""",
      """function findSpriteSlotIndex(spriteElement){
  // In PP mode, search the active viewing seat
  const searchSeat = PASS_AND_PLAY_MODE ? ppActiveViewSeat : 0;
  const searchSprites = sprites[searchSeat] || [];
  for(let i = 0; i < searchSprites.length; i++){
    const data = searchSprites[i];
    if(!data) continue;
    const spriteEl = data.sprite.el ? data.sprite.el : data.sprite;
    if(spriteEl === spriteElement){
      return i;
    }
  }
  // Fallback: search all seats
  for(let s = 0; s < 6; s++){
    const ss = sprites[s] || [];
    for(let i = 0; i < ss.length; i++){
      const data = ss[i];
      if(!data) continue;
      const spriteEl = data.sprite.el ? data.sprite.el : data.sprite;
      if(spriteEl === spriteElement) return i;
    }
  }
  return -1;
}""")


# ============================================================================
# PATCH 10: Modify bidding to use PP transition for human seats
# The runBiddingStep function needs to transition to human seats via PP
# ============================================================================

patch("PATCH 10: PP transition during bidding",
      """  if (isHumanControlled) {
    session.phase = PHASE_NEED_BID;
    const playerLabel = PASS_AND_PLAY_MODE ? `P${seatToPlayer(currentBidder)}'s` : "Your";""",
      """  if (isHumanControlled) {
    session.phase = PHASE_NEED_BID;
    // In PP mode, transition to this player's perspective
    if (PASS_AND_PLAY_MODE && currentBidder !== ppActiveViewSeat) {
      ppTransitionToSeat(currentBidder, 'Bidding Phase');
      // The handoff button click will re-trigger bid display
      return;
    }
    const playerLabel = PASS_AND_PLAY_MODE ? `P${seatToPlayer(currentBidder)}'s` : "Your";""")


# ============================================================================
# PATCH 11: Modify trump selection to handle PP human seats
# When bid winner is human in PP mode, transition to them for trump pick
# ============================================================================

patch("PATCH 11: PP transition for trump selection",
      """const isHumanControlled = PASS_AND_PLAY_MODE || winnerSeat === 0;""",
      """const isHumanControlled = ppIsHuman(winnerSeat);""")


# ============================================================================
# PATCH 12: After human plays in PP mode, use ppAIPlayLoop instead of aiPlayTurn
# ============================================================================

patch("PATCH 12: Use PP AI loop after human play",
      """  // AI players take their turns
  // Reset isAnimating before calling aiPlayTurn so it doesn't get blocked
  isAnimating = false;
  await aiPlayTurn();
}""",
      """  // AI/Human players take their turns
  isAnimating = false;
  if (PASS_AND_PLAY_MODE) {
    maybeAIKick();
  } else {
    await aiPlayTurn();
  }
}""")


# ============================================================================
# PATCH 13: getHandPosition and getPlayedPosition need to use rotation
# The playDomino function converts seat -> playerNum via seatToPlayer.
# We need it to use ppVisualPlayer when in PP mode.
# ============================================================================

patch("PATCH 13: Rotate played domino position in playDomino",
      """  // Convert seat to player number for layout lookups
  const playerNum = seatToPlayer(seat);
  const targetPose = getPlayedPosition(playerNum);""",
      """  // Convert seat to player number for layout lookups
  const playerNum = PASS_AND_PLAY_MODE ? ppVisualPlayer(seat) : seatToPlayer(seat);
  const targetPose = getPlayedPosition(playerNum);""")


# ============================================================================
# PATCH 14: Rotate recenterHand to use correct visual position
# ============================================================================

patch("PATCH 14: Rotate recenterHand positions",
      """  // Convert seat to player number for layout lookups
  const playerNum = seatToPlayer(seat);
  const section = getSection(`Player_${playerNum}_Hand`);""",
      """  // Convert seat to player number for layout lookups
  const playerNum = PASS_AND_PLAY_MODE ? ppVisualPlayer(seat) : seatToPlayer(seat);
  const section = getSection(`Player_${playerNum}_Hand`);""")


# ============================================================================
# PATCH 15: Add setFaceUp method to sprites if not present
# The makeSprite function needs a setFaceUp method for PP rotation
# ============================================================================

patch("PATCH 15: Add setFaceUp method to sprites",
      """  el.setRotY=(deg)=>{""",
      """  el.setFaceUp=(faceUp)=>{
    el.setRotY(faceUp ? 180 : 0);
  };

  el.setRotY=(deg)=>{""")


# ============================================================================
# PATCH 16: When PP mode is on and a new hand starts, handle rotation properly
# After startNewHand creates sprites, we need to set up PP rotation
# ============================================================================

patch("PATCH 16: Handle PP mode in startNewHand",
      """  initBiddingRound();
  startBiddingRound();
}""",
      """  initBiddingRound();

  // In Pass & Play mode, set up rotation for first bidder
  if (PASS_AND_PLAY_MODE) {
    const firstBidder = biddingState ? biddingState.currentBidder : 0;
    if (ppIsHuman(firstBidder)) {
      ppTransitionToSeat(firstBidder, 'Bidding Phase');
    } else {
      // First bidder is AI - rotate to first human or just run bidding
      ppResetRotation();
      startBiddingRound();
    }
  } else {
    startBiddingRound();
  }
}""")


# ============================================================================
# PATCH 17: Fix AI bidding in PP mode - processAIBid needs to work for AI seats
# The runBiddingStep already checks isHumanControlled. But we need to make sure
# non-human seats get processed as AI even in PP mode.
# ============================================================================

# The existing code already handles this via:
# const isHumanControlled = PASS_AND_PLAY_MODE || currentBidder === 0;
# We changed the trump one but need to fix the bidding one too.
# Actually the bidding isHumanControlled check is correct because with PASS_AND_PLAY_MODE
# on, ALL seats show as human. We need to change it to use ppIsHuman.

patch("PATCH 17: Fix bidding human check for mixed seats",
      """  const isHumanControlled = PASS_AND_PLAY_MODE || currentBidder === 0;

  if (isHumanControlled) {
    session.phase = PHASE_NEED_BID;""",
      """  const isHumanControlled = ppIsHuman(currentBidder);

  if (isHumanControlled) {
    session.phase = PHASE_NEED_BID;""")


# ============================================================================
# PATCH 18: Fix humanBid/humanPass guards for PP mode
# They check: if (!PASS_AND_PLAY_MODE && currentBidder !== 0)
# Need to allow any human seat in PP mode
# ============================================================================

patch("PATCH 18a: Fix humanBid guard",
      """  if (!PASS_AND_PLAY_MODE && currentBidder !== 0) return false;""",
      """  if (!ppIsHuman(currentBidder)) return false;""")

patch("PATCH 18b: Fix humanPass guard",
      """  if (!PASS_AND_PLAY_MODE && currentBidder !== 0) return false;""",
      """  if (!ppIsHuman(currentBidder)) return false;""")


# ============================================================================
# PATCH 19: Fix renderAll bid overlay visibility for PP mode
# ============================================================================

patch("PATCH 19: Fix bid overlay visibility",
      "    (PASS_AND_PLAY_MODE || biddingState.currentBidder === 0);",
      "    ppIsHuman(biddingState.currentBidder);")


# ============================================================================
# PATCH 20: Add placeholder data-player attribute for rotation
# The createPlaceholders function needs to tag each placeholder with its player
# ============================================================================

patch("PATCH 20: Tag placeholders with player number",
      "    el.className = 'placeholder player-placeholder';",
      "    el.className = 'placeholder player-placeholder';\n    el.dataset.ppPlayer = String(p);")


# ============================================================================
# DONE
# ============================================================================

write(DST, html)
delta = len(html) - original_len
print(f"\nApplied {patches_ok} patches")
print(f"Output: {DST} ({len(html)} bytes, delta: {'+' if delta >= 0 else ''}{delta})")
