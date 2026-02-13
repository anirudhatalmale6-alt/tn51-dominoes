#!/usr/bin/env python3
"""Build V10_47 from V10_46:
1. Fix BY2_OUTER_SIZE to 2
2. Persistent boneyard — temporarily hide during trick collection, reappear after
3. Auto-close boneyard when hand ends + disable BONES button when empty
4. End of game — show final scores, keep marks on board until new game
5. Marks to win selection (3/7/15) at game start
6. Overflow marks — support >15 marks in drawTallyMarks
7. Save/restore fix — save full state including dealer, bid_winner_seat, leader
8. Hand replay system — save named hands, reload to replay same deal
"""
import re, sys

INPUT = 'TN51_Dominoes_V10_46.html'
OUTPUT = 'TN51_Dominoes_V10_47.html'

with open(INPUT, 'r', encoding='utf-8') as f:
    html = f.read()

patches_applied = 0

# ============================================================
# PATCH 1: Fix BY2_OUTER_SIZE from 6 to 2
# ============================================================
old_outer = "const BY2_OUTER_SIZE = 6;"
new_outer = "const BY2_OUTER_SIZE = 2;"

if old_outer in html:
    html = html.replace(old_outer, new_outer, 1)
    patches_applied += 1
    print("PATCH 1 applied: BY2_OUTER_SIZE = 2")
else:
    # Client may have already fixed this manually
    if "const BY2_OUTER_SIZE = 2;" in html:
        print("PATCH 1 skipped: BY2_OUTER_SIZE already 2")
    else:
        print("ERROR: Could not find BY2_OUTER_SIZE")
        sys.exit(1)

# ============================================================
# PATCH 2: Persistent boneyard — hide during trick collection, reappear after
# Modify collectToHistory to temporarily hide boneyard2, then restore after delay
# ============================================================
old_collect_end = """  // Refresh boneyard 2 if visible
  if(boneyard2Visible) renderBoneyard2();

  playedThisTrick = [];
  currentTrick++;
}"""

new_collect_end = """  // Refresh boneyard 2 if visible — show trick history temporarily during collection,
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
  }

  playedThisTrick = [];
  currentTrick++;
}"""

if old_collect_end in html:
    html = html.replace(old_collect_end, new_collect_end, 1)
    patches_applied += 1
    print("PATCH 2 applied: Persistent boneyard with temporary hide during collection")
else:
    print("ERROR: Could not find collectToHistory end block")
    sys.exit(1)

# ============================================================
# PATCH 3: Auto-close boneyard when hand ends + disable BONES button when empty
# Modify showHandEndPopup to close boneyard and disable toggle
# ============================================================
old_show_popup = """function showHandEndPopup(){
  // Flip remaining opponent dominoes face-up so player can see what they had
  flipRemainingDominoes();

  const status = session.status;
  const btnNextHand = document.getElementById('btnNextHand');"""

new_show_popup = """function showHandEndPopup(){
  // Auto-close boneyard 2 at end of hand
  if(boneyard2Visible){
    boneyard2Visible = false;
    const by2c = document.getElementById('boneyard2Container');
    const thBg = document.getElementById('trickHistoryBg');
    const toggleBtn = document.getElementById('boneyard2Toggle');
    if(by2c) by2c.style.display = 'none';
    if(thBg) thBg.style.display = '';
    showTrickHistorySprites();
    if(toggleBtn) toggleBtn.classList.remove('active');
  }
  // Disable BONES button (no tiles left to show)
  const bonesBtn = document.getElementById('boneyard2Toggle');
  if(bonesBtn){
    bonesBtn.style.pointerEvents = 'none';
    bonesBtn.style.opacity = '0.15';
  }

  // Flip remaining opponent dominoes face-up so player can see what they had
  flipRemainingDominoes();

  const status = session.status;
  const btnNextHand = document.getElementById('btnNextHand');"""

if old_show_popup in html:
    html = html.replace(old_show_popup, new_show_popup, 1)
    patches_applied += 1
    print("PATCH 3a applied: Auto-close boneyard at hand end + disable button")
else:
    print("ERROR: Could not find showHandEndPopup")
    sys.exit(1)

# Re-enable BONES button in startNewHand
old_start_new_hand_bones = """  // Hide boneyard 2 overlay when new hand starts
  if(boneyard2Visible){
    boneyard2Visible = false;
    const by2c = document.getElementById('boneyard2Container');
    const thBg = document.getElementById('trickHistoryBg');
    const toggleBtn = document.getElementById('boneyard2Toggle');
    if(by2c) by2c.style.display = 'none';
    if(thBg) thBg.style.display = '';
    if(toggleBtn) toggleBtn.classList.remove('active');
  }"""

new_start_new_hand_bones = """  // Hide boneyard 2 overlay when new hand starts
  if(boneyard2Visible){
    boneyard2Visible = false;
    const by2c = document.getElementById('boneyard2Container');
    const thBg = document.getElementById('trickHistoryBg');
    const toggleBtn = document.getElementById('boneyard2Toggle');
    if(by2c) by2c.style.display = 'none';
    if(thBg) thBg.style.display = '';
    if(toggleBtn) toggleBtn.classList.remove('active');
  }
  // Re-enable BONES button for new hand
  const bonesToggle = document.getElementById('boneyard2Toggle');
  if(bonesToggle){
    bonesToggle.style.pointerEvents = 'auto';
    bonesToggle.style.opacity = '';
  }"""

if old_start_new_hand_bones in html:
    html = html.replace(old_start_new_hand_bones, new_start_new_hand_bones, 1)
    patches_applied += 1
    print("PATCH 3b applied: Re-enable BONES button on new hand")
else:
    print("ERROR: Could not find startNewHand boneyard block")
    sys.exit(1)

# ============================================================
# PATCH 4: End of game — keep marks on board, show final scores
# Remove the marks reset from maybe_finish_hand
# ============================================================
old_game_win = """    if(Math.max(this.team_marks[0], this.team_marks[1]) >= this.marks_to_win){
      const winner=(this.team_marks[0] > this.team_marks[1]) ? 0 : 1;
      this.status += ` Team ${winner+1} wins the game!`;
      this.team_marks=[0,0];
    }"""

new_game_win = """    if(Math.max(this.team_marks[0], this.team_marks[1]) >= this.marks_to_win){
      const winner=(this.team_marks[0] > this.team_marks[1]) ? 0 : 1;
      this.status += ` Team ${winner+1} wins the game!`;
      // Marks stay on board until player starts a new game
    }"""

if old_game_win in html:
    html = html.replace(old_game_win, new_game_win, 1)
    patches_applied += 1
    print("PATCH 4a applied: Marks persist after game win")
else:
    print("ERROR: Could not find game win marks reset")
    sys.exit(1)

# When "New Game" button is clicked after a game win, THEN reset marks
# The Next Hand button handler currently just calls startNewHand().
# We need to detect game-win state and call start_new_game instead.
old_next_hand_handler = """// Handle Next Hand button
document.getElementById('btnNextHand').addEventListener('click', () => {
  hideHandEndPopup();
  SFX.resumeBgmAfterResult();
  startNewHand();
});"""

new_next_hand_handler = """// Handle Next Hand button
document.getElementById('btnNextHand').addEventListener('click', () => {
  hideHandEndPopup();
  SFX.resumeBgmAfterResult();
  // If game just ended (button says "New Game"), reset marks first
  const btn = document.getElementById('btnNextHand');
  if(btn && btn.textContent === 'New Game'){
    session.team_marks = [0, 0];
    clearSavedGame();
  }
  startNewHand();
});"""

if old_next_hand_handler in html:
    html = html.replace(old_next_hand_handler, new_next_hand_handler, 1)
    patches_applied += 1
    print("PATCH 4b applied: Reset marks only on explicit New Game click")
else:
    print("ERROR: Could not find Next Hand handler")
    sys.exit(1)

# Improve showHandEndPopup to show final scores for all players
old_popup_win_check = """  // Check for game win - change button text accordingly
  if(status.includes('wins the game')){
    btnNextHand.textContent = 'New Game';
    btnNextHand.style.background = 'linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%)';
    // Game win/lose: fade out BGM, play result song
    if(status.includes('Team 1 wins the game')){
      SFX.playResultSong('win');
    } else {
      SFX.playResultSong('lose');
    }
  } else {
    btnNextHand.textContent = 'Next Round';
    btnNextHand.style.background = 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)';
  }

  // Show the button
  btnNextHand.style.display = 'block';"""

new_popup_win_check = """  // Check for game win - change button text accordingly
  if(status.includes('wins the game')){
    btnNextHand.textContent = 'New Game';
    btnNextHand.style.background = 'linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%)';
    // Game win/lose: fade out BGM, play result song
    if(status.includes('Team 1 wins the game')){
      SFX.playResultSong('win');
    } else {
      SFX.playResultSong('lose');
    }
    // Show final scores summary
    showGameEndSummary();
  } else {
    btnNextHand.textContent = 'Next Round';
    btnNextHand.style.background = 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)';
  }

  // Show the button
  btnNextHand.style.display = 'block';"""

if old_popup_win_check in html:
    html = html.replace(old_popup_win_check, new_popup_win_check, 1)
    patches_applied += 1
    print("PATCH 4c applied: Call showGameEndSummary on game win")
else:
    print("ERROR: Could not find popup win check")
    sys.exit(1)

# Add the showGameEndSummary function and CSS for overlay
# Insert before the toggleBoneyard2 function
old_boneyard2_section = """function toggleBoneyard2(){"""

game_end_summary_code = """function showGameEndSummary(){
  // Create overlay showing final scores
  let overlay = document.getElementById('gameEndOverlay');
  if(!overlay){
    overlay = document.createElement('div');
    overlay.id = 'gameEndOverlay';
    overlay.style.cssText = 'position:absolute;left:0;top:0;width:100%;height:100%;z-index:50;display:flex;align-items:center;justify-content:center;pointer-events:none;';
    document.getElementById('tableMain').appendChild(overlay);
  }
  const t1m = session.team_marks[0];
  const t2m = session.team_marks[1];
  const t1p = session.game.team_points[0];
  const t2p = session.game.team_points[1];
  const winner = t1m > t2m ? 1 : 2;
  overlay.innerHTML = `
    <div style="background:rgba(0,10,0,0.92);border-radius:14px;padding:18px 28px;text-align:center;color:#fff;font-family:inherit;box-shadow:0 6px 24px rgba(0,0,0,0.6);pointer-events:auto;max-width:80%;">
      <div style="font-size:20px;font-weight:bold;margin-bottom:10px;color:${winner===1?'#3b82f6':'#ef4444'};">Team ${winner} Wins!</div>
      <div style="display:flex;gap:24px;justify-content:center;margin-bottom:8px;">
        <div style="text-align:center;">
          <div style="font-size:12px;opacity:0.7;">Team 1</div>
          <div style="font-size:24px;font-weight:bold;color:#3b82f6;">${t1m}</div>
          <div style="font-size:10px;opacity:0.5;">marks</div>
          <div style="font-size:14px;margin-top:4px;">${t1p} pts</div>
        </div>
        <div style="text-align:center;">
          <div style="font-size:12px;opacity:0.7;">Team 2</div>
          <div style="font-size:24px;font-weight:bold;color:#ef4444;">${t2m}</div>
          <div style="font-size:10px;opacity:0.5;">marks</div>
          <div style="font-size:14px;margin-top:4px;">${t2p} pts</div>
        </div>
      </div>
    </div>`;
  overlay.style.display = 'flex';
}

function hideGameEndSummary(){
  const overlay = document.getElementById('gameEndOverlay');
  if(overlay) overlay.style.display = 'none';
}

function toggleBoneyard2(){"""

new_boneyard2_section = game_end_summary_code

if old_boneyard2_section in html:
    html = html.replace(old_boneyard2_section, new_boneyard2_section, 1)
    patches_applied += 1
    print("PATCH 4d applied: Added showGameEndSummary function")
else:
    print("ERROR: Could not find toggleBoneyard2 anchor")
    sys.exit(1)

# Hide the summary when starting new hand
old_start_hand_shadow = """  shadowLayer.innerHTML = '';
  spriteLayer.innerHTML = '';
  sprites.length = 0;
  currentTrick = 0;"""

new_start_hand_shadow = """  hideGameEndSummary();
  shadowLayer.innerHTML = '';
  spriteLayer.innerHTML = '';
  sprites.length = 0;
  currentTrick = 0;"""

if old_start_hand_shadow in html:
    html = html.replace(old_start_hand_shadow, new_start_hand_shadow, 1)
    patches_applied += 1
    print("PATCH 4e applied: Hide game end summary on new hand")
else:
    print("ERROR: Could not find startNewHand shadow block")
    sys.exit(1)

# ============================================================
# PATCH 5: Marks to win selection at game start
# Add 3/7/15 buttons to start screen
# ============================================================
old_start_screen = """<div class="modalBackdrop" id="startScreenBackdrop" style="display:flex; background:transparent;">
  <div class="startScreenPanel">
    <div class="startScreenTitle">Tennessee 51</div>
    <div class="startScreenButtons">
      <button class="glossBtn glossGreen startScreenBtn" id="btnStartNewGame">New Game</button>
      <button class="glossBtn glossBlue startScreenBtn" id="btnStartResumeGame" style="display:none;">Resume Game</button>
    </div>
  </div>
</div>"""

new_start_screen = """<div class="modalBackdrop" id="startScreenBackdrop" style="display:flex; background:transparent;">
  <div class="startScreenPanel">
    <div class="startScreenTitle">Tennessee 51</div>
    <div id="marksSelection" style="text-align:center;margin-bottom:8px;">
      <div style="font-size:12px;color:rgba(255,255,255,0.7);margin-bottom:6px;">Marks to Win</div>
      <div style="display:flex;gap:8px;justify-content:center;">
        <button class="glossBtn marksBtn" data-marks="3" style="padding:6px 14px;font-size:13px;background:linear-gradient(135deg,#6366f1,#4f46e5);border:none;border-radius:8px;color:#fff;cursor:pointer;">3<br><span style="font-size:9px;opacity:0.7;">Short</span></button>
        <button class="glossBtn marksBtn marksSelected" data-marks="7" style="padding:6px 14px;font-size:13px;background:linear-gradient(135deg,#22c55e,#16a34a);border:2px solid #fff;border-radius:8px;color:#fff;cursor:pointer;">7<br><span style="font-size:9px;opacity:0.7;">Standard</span></button>
        <button class="glossBtn marksBtn" data-marks="15" style="padding:6px 14px;font-size:13px;background:linear-gradient(135deg,#f59e0b,#d97706);border:none;border-radius:8px;color:#fff;cursor:pointer;">15<br><span style="font-size:9px;opacity:0.7;">Long</span></button>
      </div>
    </div>
    <div class="startScreenButtons">
      <button class="glossBtn glossGreen startScreenBtn" id="btnStartNewGame">New Game</button>
      <button class="glossBtn glossBlue startScreenBtn" id="btnStartResumeGame" style="display:none;">Resume Game</button>
    </div>
  </div>
</div>"""

if old_start_screen in html:
    html = html.replace(old_start_screen, new_start_screen, 1)
    patches_applied += 1
    print("PATCH 5a applied: Marks to win selection buttons on start screen")
else:
    print("ERROR: Could not find start screen HTML")
    sys.exit(1)

# Add marks selection JS logic before the start screen button handlers
old_start_handlers = """// Start screen button handlers
document.getElementById('btnStartNewGame').addEventListener('click', () => {
  hideStartScreen();
  clearSavedGame();
  startNewHand();
});"""

new_start_handlers = """// Marks to win selection
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

if old_start_handlers in html:
    html = html.replace(old_start_handlers, new_start_handlers, 1)
    patches_applied += 1
    print("PATCH 5b applied: Marks selection JS + set marks_to_win on new game")
else:
    print("ERROR: Could not find start screen handlers")
    sys.exit(1)

# ============================================================
# PATCH 6: Overflow marks — support >15 marks in drawTallyMarks
# Remove the clamp to 15, add second row for overflow
# ============================================================
old_tally_clamp = """  if(count <= 0) return;

  count = Math.min(15, Math.max(0, count));  // Clamp to 0-15"""

new_tally_clamp = """  if(count <= 0) return;

  // No clamp — support overflow marks beyond 15"""

if old_tally_clamp in html:
    html = html.replace(old_tally_clamp, new_tally_clamp, 1)
    patches_applied += 1
    print("PATCH 6a applied: Removed 15-mark clamp")
else:
    print("ERROR: Could not find tally clamp")
    sys.exit(1)

# We also need to handle overflow rendering. If count > 15, draw first 15 normally
# then draw overflow below. Replace the entire draw logic with one that handles rows.
# Actually, let's take a simpler approach: increase the canvas height when count > 15
# and draw a second row. The current logic already draws right-to-left groups of 5.
# We just need it to wrap after 15 marks.

# Replace the marks pill canvas height in HTML to be dynamic
# Actually, the canvas height is fixed at 24. Let's make the tally function
# handle wrapping internally by splitting into rows of up to 15.

old_tally_func_start = """function drawTallyMarks(canvas, count, teamColor){
  const ctx = canvas.getContext('2d');
  const w = canvas.width;
  const h = canvas.height;
  ctx.clearRect(0, 0, w, h);

  if(count <= 0) return;

  // No clamp — support overflow marks beyond 15

  // Tally mark dimensions
  const lineHeight = h * 0.75;
  const lineWidth = 2;
  const gapBetweenLines = 5;  // Gap between vertical lines within a group
  const groupGap = 8;  // Gap between groups of 5"""

new_tally_func_start = """function drawTallyMarks(canvas, count, teamColor){
  const ctx = canvas.getContext('2d');
  const w = canvas.width;
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  if(count <= 0) return;

  // If count > 15, increase canvas height for extra rows
  const rowCapacity = 15;
  const numRows = Math.ceil(count / rowCapacity);
  const rowH = 24;  // height per row
  const totalH = numRows * rowH;
  if(canvas.height !== totalH){
    canvas.height = totalH;
    canvas.style.height = totalH + 'px';
  }
  const h = rowH;  // each row is this tall

  // Draw each row
  for(let row = 0; row < numRows; row++){
    const rowCount = (row < numRows - 1) ? rowCapacity : (count - row * rowCapacity);
    const yOffset = row * rowH;
    _drawTallyRow(ctx, w, h, yOffset, rowCount, teamColor);
  }
}

function _drawTallyRow(ctx, w, h, yOffset, count, teamColor){
  // Tally mark dimensions
  const lineHeight = h * 0.75;
  const lineWidth = 2;
  const gapBetweenLines = 5;  // Gap between vertical lines within a group
  const groupGap = 8;  // Gap between groups of 5"""

if old_tally_func_start in html:
    html = html.replace(old_tally_func_start, new_tally_func_start, 1)
    patches_applied += 1
    print("PATCH 6b applied: Multi-row tally marks for overflow")
else:
    print("ERROR: Could not find tally function start")
    sys.exit(1)

# Now update all the drawing calls in the tally function to use yOffset
# The drawing code uses `h / 2` for vertical centering — we need to replace
# with `yOffset + h / 2`
# Let's replace the moveTo/lineTo calls and ctx.translate calls

# Replace `ctx.translate(x + jitterX, h / 2)` with `ctx.translate(x + jitterX, yOffset + h / 2)`
# This occurs multiple times in the tally function. We can use replace_all but need to be careful
# it only applies within the tally function. Since the pattern is unique enough, let's do it.

# Actually, after the refactor above, the drawing code is now in _drawTallyRow which receives yOffset.
# But the existing code still uses `h / 2` for centering. Since _drawTallyRow has `h` as the row height,
# we need to add yOffset to all y-coordinates.

# The tally mark drawing has these y-references:
# 1. ctx.translate(x + jitterX, h / 2)  — 3 occurrences
# 2. ctx.moveTo(groupStartX - 1, h / 2 + lineHeight / 2 - 2 + jitterY1)
# 3. ctx.lineTo(groupEndX + 1, h / 2 - lineHeight / 2 + 2 + jitterY2)

# We need to replace each `h / 2` with `yOffset + h / 2` inside the tally drawing code.
# Since these patterns are fairly unique (they're within the tally mark rendering),
# let's replace them.

# First occurrence: in remainder drawing loop
old_translate_remainder = """      ctx.save();
      ctx.translate(x + jitterX, h / 2);
      ctx.rotate(jitterAngle);
      ctx.beginPath();
      ctx.moveTo(0, -lineHeight / 2 + jitterY1);
      ctx.lineTo(0, lineHeight / 2 + jitterY2);
      ctx.stroke();
      ctx.restore();

      x -= gapBetweenLines;
    }

    if(completeGroups > 0) x -= groupGap;  // Gap before complete groups
  }

  // Draw complete groups (from right to left - newest to oldest)
  for(let g = 0; g < completeGroups; g++){
    // Draw the group from right to left
    // Position for rightmost (4th) line
    const groupEndX = x;

    // Draw 4 vertical lines from right to left
    for(let line = 3; line >= 0; line--){
      const jitterX = (Math.random() - 0.5) * 1;
      const jitterY1 = (Math.random() - 0.5) * 1.5;
      const jitterY2 = (Math.random() - 0.5) * 1.5;
      const jitterAngle = (Math.random() - 0.5) * 0.08;

      ctx.save();
      ctx.translate(x + jitterX, h / 2);
      ctx.rotate(jitterAngle);
      ctx.beginPath();
      ctx.moveTo(0, -lineHeight / 2 + jitterY1);
      ctx.lineTo(0, lineHeight / 2 + jitterY2);
      ctx.stroke();
      ctx.restore();

      x -= gapBetweenLines;
    }

    const groupStartX = x + gapBetweenLines;  // Left edge of group

    // Draw diagonal slash through the 4 lines (from bottom-left to top-right)
    const jitterY1 = (Math.random() - 0.5) * 1.5;
    const jitterY2 = (Math.random() - 0.5) * 1.5;
    ctx.beginPath();
    ctx.moveTo(groupStartX - 1, h / 2 + lineHeight / 2 - 2 + jitterY1);
    ctx.lineTo(groupEndX + 1, h / 2 - lineHeight / 2 + 2 + jitterY2);
    ctx.stroke();

    if(g < completeGroups - 1) x -= groupGap;  // Gap before next group
  }
}"""

new_translate_remainder = """      ctx.save();
      ctx.translate(x + jitterX, yOffset + h / 2);
      ctx.rotate(jitterAngle);
      ctx.beginPath();
      ctx.moveTo(0, -lineHeight / 2 + jitterY1);
      ctx.lineTo(0, lineHeight / 2 + jitterY2);
      ctx.stroke();
      ctx.restore();

      x -= gapBetweenLines;
    }

    if(completeGroups > 0) x -= groupGap;  // Gap before complete groups
  }

  // Draw complete groups (from right to left - newest to oldest)
  for(let g = 0; g < completeGroups; g++){
    // Draw the group from right to left
    // Position for rightmost (4th) line
    const groupEndX = x;

    // Draw 4 vertical lines from right to left
    for(let line = 3; line >= 0; line--){
      const jitterX = (Math.random() - 0.5) * 1;
      const jitterY1 = (Math.random() - 0.5) * 1.5;
      const jitterY2 = (Math.random() - 0.5) * 1.5;
      const jitterAngle = (Math.random() - 0.5) * 0.08;

      ctx.save();
      ctx.translate(x + jitterX, yOffset + h / 2);
      ctx.rotate(jitterAngle);
      ctx.beginPath();
      ctx.moveTo(0, -lineHeight / 2 + jitterY1);
      ctx.lineTo(0, lineHeight / 2 + jitterY2);
      ctx.stroke();
      ctx.restore();

      x -= gapBetweenLines;
    }

    const groupStartX = x + gapBetweenLines;  // Left edge of group

    // Draw diagonal slash through the 4 lines (from bottom-left to top-right)
    const jitterY1 = (Math.random() - 0.5) * 1.5;
    const jitterY2 = (Math.random() - 0.5) * 1.5;
    ctx.beginPath();
    ctx.moveTo(groupStartX - 1, yOffset + h / 2 + lineHeight / 2 - 2 + jitterY1);
    ctx.lineTo(groupEndX + 1, yOffset + h / 2 - lineHeight / 2 + 2 + jitterY2);
    ctx.stroke();

    if(g < completeGroups - 1) x -= groupGap;  // Gap before next group
  }
}"""

if old_translate_remainder in html:
    html = html.replace(old_translate_remainder, new_translate_remainder, 1)
    patches_applied += 1
    print("PATCH 6c applied: Updated tally draw calls with yOffset")
else:
    print("ERROR: Could not find tally draw calls")
    sys.exit(1)

# ============================================================
# PATCH 7: Save/restore fix — include dealer, bid_winner_seat, leader in snapshot
# ============================================================
old_snapshot = """  snapshot(){
    const g=this.game;
    return {
      hands: g.hands.map(h=>h.map(t=>[t[0],t[1]])),
      current_player:Number(g.current_player),
      current_trick: g.current_trick.map(([p,t])=>[Number(p), [t[0],t[1]]]),
      tricks_team:g.tricks_team,
      team_points:[Number(g.team_points[0]), Number(g.team_points[1])],
      team_marks:[Number(this.team_marks[0]), Number(this.team_marks[1])],
      marks_to_win:Number(this.marks_to_win),
      trump_suit:g.trump_suit,
      trump_mode:g.trump_mode,
      contract:this.contract,
      phase:this.phase,
      status:this.status,
      current_bid:Number(this.current_bid),
      bid_marks:Number(this.bid_marks),
    };
  }"""

new_snapshot = """  snapshot(){
    const g=this.game;
    return {
      hands: g.hands.map(h=>h.map(t=>[t[0],t[1]])),
      current_player:Number(g.current_player),
      current_trick: g.current_trick.map(([p,t])=>[Number(p), [t[0],t[1]]]),
      tricks_team:g.tricks_team,
      team_points:[Number(g.team_points[0]), Number(g.team_points[1])],
      team_marks:[Number(this.team_marks[0]), Number(this.team_marks[1])],
      marks_to_win:Number(this.marks_to_win),
      trump_suit:g.trump_suit,
      trump_mode:g.trump_mode,
      contract:this.contract,
      phase:this.phase,
      status:this.status,
      current_bid:Number(this.current_bid),
      bid_marks:Number(this.bid_marks),
      dealer:Number(this.dealer),
      bid_winner_seat:this.bid_winner_seat !== undefined ? Number(this.bid_winner_seat) : 0,
      leader:g.leader !== undefined ? Number(g.leader) : 0,
      trick_number:g.trick_number !== undefined ? Number(g.trick_number) : 0,
      active_players:g.active_players ? g.active_players.slice() : [0,1,2,3,4,5],
    };
  }"""

if old_snapshot in html:
    html = html.replace(old_snapshot, new_snapshot, 1)
    patches_applied += 1
    print("PATCH 7a applied: Snapshot includes dealer, bid_winner_seat, leader, trick_number, active_players")
else:
    print("ERROR: Could not find snapshot function")
    sys.exit(1)

# Fix both resume handlers to restore dealer and use makeSprite instead of createDominoSprite
# Fix the menu resume handler
old_menu_resume = """// Resume saved game handler
document.getElementById('menuResumeGame').addEventListener('click', () => {
  document.getElementById('settingsMenu').classList.remove('open');
  const saved = loadSavedGame();
  if(saved && saved.session){
    // Restore session state
    try {
      // Reset sprites and UI
      shadowLayer.innerHTML = '';
      spriteLayer.innerHTML = '';
      sprites.length = 0;

      // Restore game state from snapshot
      const snap = saved.session;
      session.game.hands = snap.hands;
      session.game.current_trick = snap.current_trick || [];
      session.game.tricks_team = snap.tricks_team || [[], []];
      session.game.team_points = snap.team_points || [0, 0];
      session.game.trump_suit = snap.trump_suit;
      session.game.trump_mode = snap.trump_mode;
      session.game.trick_number = snap.trick_number || 0;
      session.game.current_player = snap.current_player || 0;
      session.game.leader = snap.leader || 0;
      session.game.active_players = snap.active_players || [0,1,2,3,4,5];

      session.phase = snap.phase || PHASE_PLAYING;
      session.team_marks = [saved.team1Marks || 0, saved.team2Marks || 0];
      session.contract = snap.contract || "NORMAL";
      session.current_bid = snap.current_bid || 34;
      session.bid_marks = snap.bid_marks || 1;
      session.bid_winner_seat = snap.bid_winner_seat || 0;

      team1TricksWon = saved.team1TricksWon || 0;
      team2TricksWon = saved.team2TricksWon || 0;
      currentTrick = saved.currentTrick || 0;
      team1Score = saved.team1Score || 0;
      team2Score = saved.team2Score || 0;

      // Recreate sprites
      createPlaceholders();
      const hands = session.game.hands;
      for(let p = 0; p < 6; p++){
        sprites[p] = [];
        const playerNum = seatToPlayer(p);
        for(let h = 0; h < 6; h++){
          const tile = hands[p] && hands[p][h];
          if(tile){
            const faceUp = (p === 0);
            const sprite = createDominoSprite(tile, faceUp);
            const pos = getHandPosition(playerNum, h);
            if(pos) sprite.setPose(pos);
            sprites[p][h] = { sprite, tile, originalSlot: h };

            if(p === 0){
              sprite.el.classList.add('clickable');
              sprite.el.addEventListener('click', () => handlePlayer1Click(sprite.el));
            }
          } else {
            sprites[p][h] = null;
          }
        }
      }

      updateScoreDisplay();
      updateTrumpDisplay();

      if(session.phase === PHASE_PLAYING && session.game.current_player === 0){
        waitingForPlayer1 = true;
        enablePlayer1Clicks();
        updatePlayer1ValidStates();
        setStatus('Game resumed - Click a domino to play');
      } else if(session.phase === PHASE_PLAYING){
        setStatus('Game resumed');
        setTimeout(() => aiPlayTurn(), 500);
      } else {
        setStatus('Game resumed');
      }

      console.log('Game restored successfully');
    } catch(e) {
      console.error('Failed to restore game:', e);
      setStatus('Failed to restore game');
    }
  }
});"""

new_menu_resume = """// Resume saved game handler
document.getElementById('menuResumeGame').addEventListener('click', () => {
  document.getElementById('settingsMenu').classList.remove('open');
  resumeGameFromSave();
});"""

if old_menu_resume in html:
    html = html.replace(old_menu_resume, new_menu_resume, 1)
    patches_applied += 1
    print("PATCH 7b applied: Menu resume handler simplified")
else:
    print("ERROR: Could not find menu resume handler")
    sys.exit(1)

# Fix the start screen resume handler
old_start_resume = """document.getElementById('btnStartResumeGame').addEventListener('click', () => {
  hideStartScreen();
  const saved = loadSavedGame();
  if(saved && saved.session){
    // Restore session state (same as menuResumeGame handler)
    try {
      shadowLayer.innerHTML = '';
      spriteLayer.innerHTML = '';
      sprites.length = 0;

      const snap = saved.session;
      session.game.hands = snap.hands;
      session.game.current_trick = snap.current_trick || [];
      session.game.tricks_team = snap.tricks_team || [[], []];
      session.game.team_points = snap.team_points || [0, 0];
      session.game.trump_suit = snap.trump_suit;
      session.game.trump_mode = snap.trump_mode;
      session.game.trick_number = snap.trick_number || 0;
      session.game.current_player = snap.current_player || 0;
      session.game.leader = snap.leader || 0;
      session.game.active_players = snap.active_players || [0,1,2,3,4,5];

      session.phase = snap.phase || PHASE_PLAYING;
      session.team_marks = [saved.team1Marks || 0, saved.team2Marks || 0];
      session.contract = snap.contract || "NORMAL";
      session.current_bid = snap.current_bid || 34;
      session.bid_marks = snap.bid_marks || 1;
      session.bid_winner_seat = snap.bid_winner_seat || 0;

      team1TricksWon = saved.team1TricksWon || 0;
      team2TricksWon = saved.team2TricksWon || 0;
      currentTrick = saved.currentTrick || 0;
      team1Score = saved.team1Score || 0;
      team2Score = saved.team2Score || 0;

      createPlaceholders();
      const hands = session.game.hands;
      for(let p = 0; p < 6; p++){
        sprites[p] = [];
        const playerNum = seatToPlayer(p);
        for(let h = 0; h < 6; h++){
          const tile = hands[p] && hands[p][h];
          if(tile){
            const faceUp = (p === 0);
            const sprite = createDominoSprite(tile, faceUp);
            const pos = getHandPosition(playerNum, h);
            if(pos) sprite.setPose(pos);
            sprites[p][h] = { sprite, tile, originalSlot: h };
            if(p === 0){
              sprite.el.style.pointerEvents = 'auto';
              sprite.el.style.cursor = 'pointer';
              sprite.el.addEventListener('click', () => handlePlayer1Click(sprite.el));
            }
          } else {
            sprites[p][h] = null;
          }
        }
      }

      updateScoreDisplay();
      updateTrumpDisplay();
      renderAll();
      setStatus(session.status || "Game resumed");

      if(session.phase === PHASE_PLAYING && session.game.current_player === 0){
        waitingForPlayer1 = true;
        enablePlayer1Clicks();
        updatePlayer1ValidStates();
      } else if(session.phase === PHASE_PLAYING){
        maybeAIKick();
      }
    } catch(e) {
      console.error("Resume failed:", e);
      startNewHand();
    }
  } else {
    startNewHand();
  }
});"""

new_start_resume = """document.getElementById('btnStartResumeGame').addEventListener('click', () => {
  hideStartScreen();
  if(!resumeGameFromSave()){
    startNewHand();
  }
});"""

if old_start_resume in html:
    html = html.replace(old_start_resume, new_start_resume, 1)
    patches_applied += 1
    print("PATCH 7c applied: Start screen resume handler simplified")
else:
    print("ERROR: Could not find start screen resume handler")
    sys.exit(1)

# Add the unified resumeGameFromSave function after saveGameState
old_load_saved = """function loadSavedGame(){
  try {
    const saved = localStorage.getItem(SAVE_KEY);
    if(!saved) return null;
    return JSON.parse(saved);
  } catch(e) {
    console.warn('Failed to load saved game:', e);
    return null;
  }
}"""

new_load_saved = """function loadSavedGame(){
  try {
    const saved = localStorage.getItem(SAVE_KEY);
    if(!saved) return null;
    return JSON.parse(saved);
  } catch(e) {
    console.warn('Failed to load saved game:', e);
    return null;
  }
}

function resumeGameFromSave(){
  const saved = loadSavedGame();
  if(!saved || !saved.session) return false;
  try {
    shadowLayer.innerHTML = '';
    spriteLayer.innerHTML = '';
    sprites.length = 0;

    const snap = saved.session;
    session.game.hands = snap.hands;
    session.game.current_trick = snap.current_trick || [];
    session.game.tricks_team = snap.tricks_team || [[], []];
    session.game.team_points = snap.team_points || [0, 0];
    session.game.trump_suit = snap.trump_suit;
    session.game.trump_mode = snap.trump_mode;
    session.game.trick_number = snap.trick_number || 0;
    session.game.current_player = snap.current_player || 0;
    session.game.leader = snap.leader || 0;
    session.game.active_players = snap.active_players || [0,1,2,3,4,5];

    session.phase = snap.phase || PHASE_PLAYING;
    session.team_marks = snap.team_marks || [saved.team1Marks || 0, saved.team2Marks || 0];
    session.marks_to_win = snap.marks_to_win || 7;
    session.contract = snap.contract || "NORMAL";
    session.current_bid = snap.current_bid || 34;
    session.bid_marks = snap.bid_marks || 1;
    session.bid_winner_seat = snap.bid_winner_seat || 0;
    session.dealer = snap.dealer || 0;

    team1TricksWon = saved.team1TricksWon || 0;
    team2TricksWon = saved.team2TricksWon || 0;
    currentTrick = saved.currentTrick || 0;
    team1Score = saved.team1Score || 0;
    team2Score = saved.team2Score || 0;

    // Recreate sprites using makeSprite (consistent with startNewHand)
    createPlaceholders();
    const hands = session.game.hands;
    for(let p = 0; p < 6; p++){
      sprites[p] = [];
      const playerNum = seatToPlayer(p);
      for(let h = 0; h < 6; h++){
        const tile = hands[p] && hands[p][h];
        if(tile){
          const sprite = makeSprite(tile);
          const pos = getHandPosition(playerNum, h);
          if(pos){
            sprite.setPose(pos);
            if(sprite._shadow) shadowLayer.appendChild(sprite._shadow);
            spriteLayer.appendChild(sprite);
          }
          sprites[p][h] = { sprite, tile, originalSlot: h };
          if(p === 0){
            sprite.addEventListener('click', () => handlePlayer1Click(sprite));
            sprite.addEventListener('touchstart', (e) => {
              e.preventDefault();
              e.stopPropagation();
              handlePlayer1Click(sprite);
            }, { passive: false });
          }
        } else {
          sprites[p][h] = null;
        }
      }
    }

    team1Marks = session.team_marks[0];
    team2Marks = session.team_marks[1];
    updateScoreDisplay();
    updateTrumpDisplay();
    renderAll();

    if(session.phase === PHASE_PLAYING && session.game.current_player === 0){
      waitingForPlayer1 = true;
      enablePlayer1Clicks();
      updatePlayer1ValidStates();
      setStatus('Game resumed - Click a domino to play');
    } else if(session.phase === PHASE_PLAYING){
      setStatus('Game resumed');
      setTimeout(() => aiPlayTurn(), 500);
    } else {
      setStatus(session.status || 'Game resumed');
    }

    console.log('Game restored successfully');
    return true;
  } catch(e) {
    console.error('Failed to restore game:', e);
    setStatus('Failed to restore game');
    return false;
  }
}"""

if old_load_saved in html:
    html = html.replace(old_load_saved, new_load_saved, 1)
    patches_applied += 1
    print("PATCH 7d applied: Unified resumeGameFromSave with makeSprite and full state")
else:
    print("ERROR: Could not find loadSavedGame function")
    sys.exit(1)

# Also save during PHASE_NEED_BID and PHASE_NEED_TRUMP too (was only PHASE_PLAYING/PHASE_HAND_PAUSE)
old_autosave = """function autoSave(){
  if(session.phase === PHASE_PLAYING || session.phase === PHASE_HAND_PAUSE){
    saveGameState();
  }
}"""

new_autosave = """function autoSave(){
  // Save during any active game phase
  if(session.phase === PHASE_PLAYING || session.phase === PHASE_HAND_PAUSE ||
     session.phase === PHASE_NEED_BID || session.phase === PHASE_NEED_TRUMP){
    saveGameState();
  }
}"""

if old_autosave in html:
    html = html.replace(old_autosave, new_autosave, 1)
    patches_applied += 1
    print("PATCH 7e applied: Auto-save during bidding/trump phases too")
else:
    print("ERROR: Could not find autoSave function")
    sys.exit(1)

# ============================================================
# PATCH 8: Hand replay system — save named hands, reload to replay same deal
# Add to settings menu + replay functions
# ============================================================

# First, find the settings menu HTML to add a "Save Hand" option
# Let me search for the existing menu items
old_menu_notes = """document.getElementById('menuNotes').addEventListener('click', () => {
  document.getElementById('settingsMenu').classList.remove('open');
  document.getElementById('notesTextarea').value = loadNotes();
  document.getElementById('notesBackdrop').style.display = 'flex';
});"""

new_menu_notes = """document.getElementById('menuNotes').addEventListener('click', () => {
  document.getElementById('settingsMenu').classList.remove('open');
  document.getElementById('notesTextarea').value = loadNotes();
  document.getElementById('notesBackdrop').style.display = 'flex';
});

// ============================================================
// HAND REPLAY SYSTEM — save/load named hands for testing
// ============================================================
const REPLAY_KEY = 'tn51_saved_hands';

function getSavedHands(){
  try {
    const data = localStorage.getItem(REPLAY_KEY);
    return data ? JSON.parse(data) : [];
  } catch(e){ return []; }
}

function saveHandForReplay(name){
  // Find the most recent HAND_START in the game log
  let handStart = null;
  for(let i = gameLog.length - 1; i >= 0; i--){
    if(gameLog[i].type === 'HAND_START'){
      handStart = gameLog[i];
      break;
    }
  }
  if(!handStart || !handStart.hands) return false;

  const entry = {
    name: name,
    timestamp: Date.now(),
    hands: handStart.hands.map(h => h.tiles),
    dealerSeat: handStart.dealerSeat,
    contract: handStart.contract,
    marks: [session.team_marks[0], session.team_marks[1]],
    marksToWin: session.marks_to_win
  };

  const saved = getSavedHands();
  saved.unshift(entry);
  // Keep max 20 saved hands
  if(saved.length > 20) saved.length = 20;
  localStorage.setItem(REPLAY_KEY, JSON.stringify(saved));
  return true;
}

function replayHand(index){
  const saved = getSavedHands();
  if(index < 0 || index >= saved.length) return false;
  const entry = saved[index];

  // Reconstruct hands as tile arrays
  const hands = entry.hands.map(tiles =>
    tiles.map(tStr => {
      const parts = tStr.split('-');
      return [parseInt(parts[0]), parseInt(parts[1])];
    })
  );

  // Reset game state
  shadowLayer.innerHTML = '';
  spriteLayer.innerHTML = '';
  sprites.length = 0;
  currentTrick = 0;
  playedThisTrick = [];
  team1TricksWon = 0;
  team2TricksWon = 0;
  zIndexCounter = 100;
  isAnimating = false;
  waitingForPlayer1 = false;

  // Hide boneyard2, game end summary
  if(boneyard2Visible){
    boneyard2Visible = false;
    const by2c = document.getElementById('boneyard2Container');
    const thBg = document.getElementById('trickHistoryBg');
    const toggleBtn = document.getElementById('boneyard2Toggle');
    if(by2c) by2c.style.display = 'none';
    if(thBg) thBg.style.display = '';
    if(toggleBtn) toggleBtn.classList.remove('active');
  }
  hideGameEndSummary();

  // Re-enable bones button
  const bonesToggle = document.getElementById('boneyard2Toggle');
  if(bonesToggle){
    bonesToggle.style.pointerEvents = 'auto';
    bonesToggle.style.opacity = '';
  }

  document.getElementById('trumpDisplay').classList.remove('visible');

  // Restore marks if saved
  if(entry.marks){
    session.team_marks = [entry.marks[0], entry.marks[1]];
  }
  if(entry.marksToWin){
    session.marks_to_win = entry.marksToWin;
  }
  if(entry.dealerSeat !== undefined){
    session.dealer = entry.dealerSeat;
  }

  // Set hands directly instead of random shuffle
  session.contract = "NORMAL";
  session.current_bid = 0;
  session.bid_marks = 1;
  session.dealer = (session.dealer + 1) % 6;

  session.game.set_hands(hands, 0);
  session.game.set_trump_suit(null);
  session.game.set_active_players([0,1,2,3,4,5]);
  session.phase = PHASE_NEED_BID;
  session.status = "Starting bidding round... (Replaying saved hand)";

  createPlaceholders();

  for(let p = 0; p < 6; p++){
    sprites[p] = [];
    const playerNum = seatToPlayer(p);
    for(let h = 0; h < 6; h++){
      const tile = hands[p][h];
      if(!tile) continue;
      const sprite = makeSprite(tile);
      const pos = getHandPosition(playerNum, h);
      if(pos){
        sprite.setPose(pos);
        if(sprite._shadow) shadowLayer.appendChild(sprite._shadow);
        spriteLayer.appendChild(sprite);
      }
      const data = { sprite, tile, originalSlot: h };
      sprites[p][h] = data;
      if(p === 0){
        sprite.addEventListener('click', () => handlePlayer1Click(sprite));
        sprite.addEventListener('touchstart', (e) => {
          e.preventDefault();
          e.stopPropagation();
          handlePlayer1Click(sprite);
        }, { passive: false });
      }
    }
  }

  team1Score = session.game.team_points[0];
  team2Score = session.game.team_points[1];
  team1Marks = session.team_marks[0];
  team2Marks = session.team_marks[1];
  updateScoreDisplay();

  initBiddingRound();
  startBiddingRound();
  return true;
}

document.getElementById('menuReplay').addEventListener('click', () => {
  document.getElementById('settingsMenu').classList.remove('open');
  showReplayDialog();
});

function showReplayDialog(){
  const saved = getSavedHands();
  let overlay = document.getElementById('replayOverlay');
  if(!overlay){
    overlay = document.createElement('div');
    overlay.id = 'replayOverlay';
    overlay.style.cssText = 'position:fixed;left:0;top:0;width:100%;height:100%;z-index:200;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,0.7);';
    document.body.appendChild(overlay);
  }

  let html = '<div style="background:rgba(0,20,0,0.95);border-radius:12px;padding:16px 20px;color:#fff;max-width:90%;max-height:80%;overflow-y:auto;min-width:280px;">';
  html += '<div style="font-size:16px;font-weight:bold;margin-bottom:8px;">Saved Hands</div>';

  // Save current hand button
  html += '<div style="margin-bottom:12px;">';
  html += '<input type="text" id="replayNameInput" placeholder="Name this hand..." style="padding:6px 10px;border-radius:6px;border:1px solid #444;background:#1a1a2e;color:#fff;width:60%;font-size:13px;">';
  html += ' <button onclick="saveCurrentHand()" style="padding:6px 12px;border-radius:6px;border:none;background:#22c55e;color:#fff;cursor:pointer;font-size:13px;">Save</button>';
  html += '</div>';

  if(saved.length === 0){
    html += '<div style="opacity:0.5;font-size:13px;">No saved hands yet. Play a hand first, then save it here.</div>';
  } else {
    for(let i = 0; i < saved.length; i++){
      const h = saved[i];
      const date = new Date(h.timestamp).toLocaleDateString();
      const contract = h.contract ? `${h.contract.mode || ''} ${h.contract.trumpDisplay || ''}`.trim() : '';
      html += `<div style="display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.1);">`;
      html += `<div style="flex:1;"><div style="font-size:13px;font-weight:bold;">${h.name || 'Hand ' + (i+1)}</div>`;
      html += `<div style="font-size:10px;opacity:0.5;">${date}${contract ? ' | ' + contract : ''}</div></div>`;
      html += `<button onclick="loadReplayHand(${i})" style="padding:4px 10px;border-radius:6px;border:none;background:#3b82f6;color:#fff;cursor:pointer;font-size:12px;">Replay</button>`;
      html += `<button onclick="deleteReplayHand(${i})" style="padding:4px 8px;border-radius:6px;border:none;background:#ef4444;color:#fff;cursor:pointer;font-size:12px;">X</button>`;
      html += '</div>';
    }
  }

  html += '<div style="text-align:right;margin-top:12px;"><button onclick="closeReplayDialog()" style="padding:6px 14px;border-radius:6px;border:none;background:#555;color:#fff;cursor:pointer;font-size:13px;">Close</button></div>';
  html += '</div>';

  overlay.innerHTML = html;
  overlay.style.display = 'flex';
}

function closeReplayDialog(){
  const el = document.getElementById('replayOverlay');
  if(el) el.style.display = 'none';
}

function saveCurrentHand(){
  const nameInput = document.getElementById('replayNameInput');
  const name = (nameInput && nameInput.value.trim()) || ('Hand ' + new Date().toLocaleTimeString());
  if(saveHandForReplay(name)){
    showReplayDialog();  // Refresh the list
  } else {
    alert('No hand data available. Play at least one hand first.');
  }
}

function loadReplayHand(index){
  document.getElementById('replayOverlay').style.display = 'none';
  replayHand(index);
}

function deleteReplayHand(index){
  const saved = getSavedHands();
  saved.splice(index, 1);
  localStorage.setItem(REPLAY_KEY, JSON.stringify(saved));
  showReplayDialog();  // Refresh
}"""

if old_menu_notes in html:
    html = html.replace(old_menu_notes, new_menu_notes, 1)
    patches_applied += 1
    print("PATCH 8a applied: Hand replay system functions")
else:
    print("ERROR: Could not find menuNotes handler")
    sys.exit(1)

# Add "Replay Hand" button to settings menu HTML
old_menu_html_notes = """<div class="settingsItem" id="menuNotes">Notes</div>"""
new_menu_html_notes = """<div class="settingsItem" id="menuNotes">Notes</div>
  <div class="settingsItem" id="menuReplay">Replay Hand</div>"""

if old_menu_html_notes in html:
    html = html.replace(old_menu_html_notes, new_menu_html_notes, 1)
    patches_applied += 1
    print("PATCH 8b applied: Replay Hand menu item")
else:
    print("WARNING: Could not find menu Notes HTML for replay button")

# ============================================================
# Update version string
# ============================================================
html = html.replace('TN51 Dominoes V10_46', 'TN51 Dominoes V10_47')
html = html.replace("'V10_46'", "'V10_47'")
html = html.replace('"V10_46"', '"V10_47"')
print("Version updated: V10_46 -> V10_47")

# Write output
with open(OUTPUT, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\nTotal patches applied: {patches_applied}")
print(f"Output: {OUTPUT} ({len(html):,} bytes)")
