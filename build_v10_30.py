#!/usr/bin/env python3
"""
V10_30 Build Script — Fix advanced log background + current hand log with copy
"""

INPUT  = '/var/lib/freelancer/projects/40101953/TN51_Dominoes_V10_29.html'
OUTPUT = '/var/lib/freelancer/projects/40101953/TN51_Dominoes_V10_30.html'

with open(INPUT, 'r', encoding='utf-8') as f:
    src = f.read()

patches = []

# ─── P1: Fix advanced log modal — wrap with modalPanel, add proper structure ───
old_advlog_html = """<div class="modalBackdrop" id="advLogBackdrop" style="display:none;">
  <div class="modalBody" style="max-width:720px;width:95vw;">
    <div class="modalInner">
      <button class="modalCloseBtn" id="advLogCloseBtn">&times;</button>
      <h3 style="color:#fff;margin-bottom:10px;">Advanced AI Debug Log</h3>
      <p style="font-size:11px;color:rgba(255,255,255,0.6);margin-bottom:10px;">Full AI reasoning for every play. Copy and share for analysis.</p>
      <pre id="advLogContent" style="font-size:10px;white-space:pre-wrap;word-break:break-word;color:rgba(255,255,255,0.9);max-height:60vh;overflow-y:auto;"></pre>
      <div style="display:flex;gap:8px;margin-top:10px;">
        <button id="advLogCopyBtn" style="flex:1;padding:10px;background:rgba(59,130,246,0.8);border:none;border-radius:8px;color:#fff;font-weight:600;cursor:pointer;">Copy to Clipboard</button>
        <button id="advLogDownloadBtn" style="flex:1;padding:10px;background:rgba(34,197,94,0.8);border:none;border-radius:8px;color:#fff;font-weight:600;cursor:pointer;">Download .txt</button>
        <button id="advLogClearBtn" style="flex:0 0 auto;padding:10px 16px;background:rgba(239,68,68,0.8);border:none;border-radius:8px;color:#fff;font-weight:600;cursor:pointer;">Clear</button>
      </div>
    </div>
  </div>
</div>"""

new_advlog_html = """<div class="modalBackdrop" id="advLogBackdrop" style="display:none;">
  <div class="modalPanel" style="max-width:720px;width:95vw;max-height:85vh;">
    <div class="modalHeader">
      <span>Advanced AI Log</span>
      <button class="modalCloseBtn" id="advLogCloseBtn">&times;</button>
    </div>
    <div style="display:flex;gap:0;border-bottom:1px solid rgba(255,255,255,0.15);">
      <button id="advLogTabFull" style="flex:1;padding:8px;background:rgba(255,255,255,0.15);border:none;color:#fff;font-weight:600;font-size:12px;cursor:pointer;">Full Log</button>
      <button id="advLogTabHand" style="flex:1;padding:8px;background:transparent;border:none;color:rgba(255,255,255,0.5);font-weight:600;font-size:12px;cursor:pointer;">Current Hand</button>
    </div>
    <div class="modalBody" style="max-height:60vh;overflow-y:auto;">
      <pre id="advLogContent" style="font-size:10px;white-space:pre-wrap;word-break:break-word;color:rgba(255,255,255,0.9);"></pre>
    </div>
    <div style="padding:10px;border-top:1px solid rgba(255,255,255,0.1);">
      <div style="display:flex;gap:8px;">
        <button id="advLogCopyBtn" style="flex:1;padding:10px;background:rgba(59,130,246,0.8);border:none;border-radius:8px;color:#fff;font-weight:600;cursor:pointer;">Copy to Clipboard</button>
        <button id="advLogDownloadBtn" style="flex:1;padding:10px;background:rgba(34,197,94,0.8);border:none;border-radius:8px;color:#fff;font-weight:600;cursor:pointer;">Download .txt</button>
        <button id="advLogClearBtn" style="flex:0 0 auto;padding:10px 16px;background:rgba(239,68,68,0.8);border:none;border-radius:8px;color:#fff;font-weight:600;cursor:pointer;">Clear</button>
      </div>
    </div>
  </div>
</div>"""

patches.append(('P1: Fix advanced log modal with proper modalPanel + tabs', old_advlog_html, new_advlog_html))

# ─── P2: Add tabs to game log modal HTML ───
old_gamelog_header = """    <div class="modalHeader">
      <span>Game Log</span>
      <button class="modalCloseBtn" id="gameLogCloseBtn">&times;</button>
    </div>
    <div class="modalBody" style="max-height:60vh;overflow-y:auto;">
      <pre id="gameLogContent" style="font-size:11px;white-space:pre-wrap;word-break:break-word;color:rgba(255,255,255,0.9);"></pre>
    </div>
    <div style="padding:10px;border-top:1px solid rgba(255,255,255,0.1);">
      <div style="display:flex;gap:8px;">
        <button id="gameLogCopyBtn" style="flex:1;padding:10px;background:rgba(59,130,246,0.8);border:none;border-radius:8px;color:#fff;font-weight:600;cursor:pointer;">Copy Log to Clipboard</button>
        <button id="gameLogClearBtn" style="flex:0 0 auto;padding:10px 16px;background:rgba(239,68,68,0.8);border:none;border-radius:8px;color:#fff;font-weight:600;cursor:pointer;">Clear Log</button>
      </div>
    </div>"""

new_gamelog_header = """    <div class="modalHeader">
      <span>Game Log</span>
      <button class="modalCloseBtn" id="gameLogCloseBtn">&times;</button>
    </div>
    <div style="display:flex;gap:0;border-bottom:1px solid rgba(255,255,255,0.15);">
      <button id="gameLogTabFull" style="flex:1;padding:8px;background:rgba(255,255,255,0.15);border:none;color:#fff;font-weight:600;font-size:12px;cursor:pointer;">Full Log</button>
      <button id="gameLogTabHand" style="flex:1;padding:8px;background:transparent;border:none;color:rgba(255,255,255,0.5);font-weight:600;font-size:12px;cursor:pointer;">Current Hand</button>
    </div>
    <div class="modalBody" style="max-height:60vh;overflow-y:auto;">
      <pre id="gameLogContent" style="font-size:11px;white-space:pre-wrap;word-break:break-word;color:rgba(255,255,255,0.9);"></pre>
    </div>
    <div style="padding:10px;border-top:1px solid rgba(255,255,255,0.1);">
      <div style="display:flex;gap:8px;">
        <button id="gameLogCopyBtn" style="flex:1;padding:10px;background:rgba(59,130,246,0.8);border:none;border-radius:8px;color:#fff;font-weight:600;cursor:pointer;">Copy Log to Clipboard</button>
        <button id="gameLogClearBtn" style="flex:0 0 auto;padding:10px 16px;background:rgba(239,68,68,0.8);border:none;border-radius:8px;color:#fff;font-weight:600;cursor:pointer;">Clear Log</button>
      </div>
    </div>"""

patches.append(('P2: Add tabs to game log modal', old_gamelog_header, new_gamelog_header))

# ─── P3: Add current-hand formatter functions and tab logic ───
# Insert after formatAdvancedLog function ends. Find the menu handler.
old_menu_handler = """// Advanced AI Log handlers
document.getElementById('menuAdvancedLog').addEventListener('click', () => {
  document.getElementById('settingsMenu').classList.remove('open');
  document.getElementById('advLogContent').textContent = formatAdvancedLog() || 'No log entries yet.';
  document.getElementById('advLogBackdrop').style.display = 'flex';
});"""

new_menu_handler = """// ─── Current-hand log helpers ───
// Extract only entries from the most recent hand
function getCurrentHandEntries(){
  // Find the last HAND_START
  let lastHandIdx = -1;
  for(let i = gameLog.length - 1; i >= 0; i--){
    if(gameLog[i].type === 'HAND_START'){ lastHandIdx = i; break; }
  }
  if(lastHandIdx === -1) return [];
  return gameLog.slice(lastHandIdx);
}

function formatGameLogCurrentHand(){
  const entries = getCurrentHandEntries();
  if(entries.length === 0) return 'No current hand data.';
  let text = "=== CURRENT HAND LOG ===\\n\\n";
  for(const entry of entries){
    if(entry.type === "HAND_START"){
      text += `========== HAND ${entry.handId + 1} ==========\\n`;
      const c = entry.contract || {};
      text += `  Dealer: P${seatToPlayer(entry.dealerSeat||0)} | Leader: P${seatToPlayer(entry.leaderSeat||0)}\\n`;
      text += `  Contract: ${c.mode || "NORMAL"} | Trump: ${c.trumpDisplay || "?"} | Bid: ${c.bid || "?"}\\n`;
      text += `  Bidder: P${seatToPlayer(c.bidderSeat||0)} (Team ${c.bidderTeam || "?"})\\n`;
      const scores = entry.scoresBeforeHand || {};
      text += `  Scores Before: Team1=${scores.team1||0} Team2=${scores.team2||0}\\n`;
      if(entry.hands){
        text += `  Starting Hands:\\n`;
        for(const h of entry.hands){
          if(h.tiles && h.tiles.length > 0){
            text += `    P${seatToPlayer(h.seat)} (T${h.team}): ${h.tiles.join(", ")}\\n`;
          }
        }
      }
    } else if(entry.type === "TRICK_START"){
      text += `\\n  --- Trick ${entry.trickId + 1} ---\\n`;
      text += `    Leader: P${seatToPlayer(entry.leaderSeat)} (Team ${entry.leaderTeam}) | Led pip: ${entry.ledPip !== null ? entry.ledPip : "?"}\\n`;
    } else if(entry.type === "PLAY"){
      const actor = entry.isAISeat ? "[AI]" : "[Human]";
      text += `    P${seatToPlayer(entry.seat)} ${actor}: ${entry.tilePlayed}`;
      if(entry.aiReason) text += ` (${entry.aiReason})`;
      if(entry.wasOverride) text += ` [OVERRIDE! AI wanted: ${entry.aiSuggestedTile}]`;
      else if(!entry.isAISeat && entry.aiSuggestedTile) text += ` [AI agreed]`;
      if(entry.partnerCurrentlyWinning) text += ` [partner winning]`;
      text += "\\n";
      if(entry.legalMoves && entry.legalMoves.length > 1) text += `      Legal: ${entry.legalMoves.join(", ")}\\n`;
    } else if(entry.type === "TRICK_END"){
      text += `    >> Winner: P${seatToPlayer(entry.winnerSeat)} (Team ${entry.winnerTeam}) +${entry.pointsInTrick} pts\\n`;
      text += `    >> Plays: ${entry.playsString}\\n`;
    } else if(entry.type === "HAND_END"){
      const scores = entry.finalScores || {};
      text += `\\n  ====== HAND ${entry.handId + 1} RESULT ======\\n`;
      text += `  Final: Team1=${scores.team1||0} Team2=${scores.team2||0}\\n`;
      text += `  ${entry.winner || ""}\\n`;
      text += `  Bid made: ${entry.bidMade ? "Yes" : "No"}\\n`;
    }
  }
  return text;
}

function formatAdvancedLogCurrentHand(){
  const entries = getCurrentHandEntries();
  if(entries.length === 0) return 'No current hand data.';
  // Reuse the full advanced formatter but only on current hand entries
  let text = "=== CURRENT HAND — ADVANCED AI DEBUG ===\\n";
  text += "=== Generated: " + new Date().toISOString() + " ===\\n\\n";
  for(const entry of entries){
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
          if(h.tiles && h.tiles.length > 0) text += "  P" + seatToPlayer(h.seat) + " (T" + h.team + "): " + h.tiles.join(", ") + "\\n";
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
      if(entry.legalMoves && entry.legalMoves.length > 1) text += "    Legal moves: " + entry.legalMoves.join(", ") + "\\n";
      const d = entry.aiDebug;
      if(d){
        text += "    \\u250c\\u2500\\u2500\\u2500 AI REASONING \\u2500\\u2500\\u2500\\n";
        text += "    \\u2502 Seat: " + d.seat + " | Team: " + d.myTeam + " | Trick: " + d.trickNum;
        text += " | " + (d.isLead ? "LEADING" : "FOLLOWING (led pip: " + d.ledPip + ")") + "\\n";
        text += "    \\u2502 Hand: [" + (d.handTiles||[]).join(", ") + "]\\n";
        text += "    \\u2502 Legal: [" + (d.legalTiles||[]).join(", ") + "]\\n";
        text += "    \\u2502 Played tiles tracked: " + d.playedCount + "\\n";
        if(d.trumpMode && d.trumpMode !== "NONE"){
          text += "    \\u2502\\n";
          text += "    \\u2502 TRUMP: mode=" + d.trumpMode + " suit=" + d.trumpSuit + "\\n";
          text += "    \\u2502   In hand: [" + (d.trumpsInHand||[]).join(", ") + "]\\n";
          text += "    \\u2502   Remaining (not in hand): [" + (d.trumpsRemaining||[]).join(", ") + "]\\n";
          text += "    \\u2502   I have highest trump: " + d.iHaveHighestTrump;
          text += " (my rank: " + d.myHighestTrumpRank + " vs remaining: " + d.highestRemainingTrumpRank + ")\\n";
        }
        if(d.voidTracking && Object.keys(d.voidTracking).length > 0){
          text += "    \\u2502\\n";
          text += "    \\u2502 VOID TRACKING:\\n";
          for(const [seat, info] of Object.entries(d.voidTracking)){
            text += "    \\u2502   " + seat + " (" + info.team + "): void in suits [" + info.voidSuits.join(",") + "]";
            if(info.trumpVoidConfirmed) text += " | TRUMP VOID (confirmed)";
            else if(info.trumpVoidLikely > 0) text += " | trump void likely (" + Math.round(info.trumpVoidLikely*100) + "%)";
            text += "\\n";
          }
        }
        text += "    \\u2502\\n";
        text += "    \\u2502 TRUMP CONTROL: " + (d.weHaveTrumpControl ? "YES" : "NO");
        text += " (opps void: " + d.opponentsVoidInTrump + ", partners have trump: " + d.partnersHaveTrump + ")\\n";
        if(d.bidSafety){
          const b = d.bidSafety;
          text += "    \\u2502 BID: " + b.currentBid + " | Our score: " + b.ourScore;
          text += " | Need: " + b.pointsNeeded + " | ";
          text += b.bidIsSafe ? "SAFE" : (b.bidIsClose ? "CLOSE!" : "still working");
          text += " | Tricks left: " + b.tricksLeft + "\\n";
        }
        text += "    \\u2502\\n";
        text += "    \\u2502 DECISION: " + (d.decision || d.chosenTile || "?") + "\\n";
        text += "    \\u2514\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\n";
      }
    }
    else if(entry.type === "TRICK_END"){
      text += "  >> Winner: P" + seatToPlayer(entry.winnerSeat) + " (Team " + entry.winnerTeam + ") +" + entry.pointsInTrick + " pts\\n";
    }
    else if(entry.type === "HAND_END"){
      const scores = entry.finalScores || {};
      text += "\\n" + "=".repeat(70) + "\\n";
      text += "HAND " + (entry.handId+1) + " RESULT: Team1=" + (scores.team1||0) + " Team2=" + (scores.team2||0);
      text += " | " + (entry.winner||"") + " | Bid made: " + (entry.bidMade ? "Yes" : "No") + "\\n";
      text += "=".repeat(70) + "\\n";
    }
  }
  return text;
}

// Track which tab is active for each log
let _gameLogTab = 'full';
let _advLogTab = 'full';

function refreshGameLogContent(){
  const content = _gameLogTab === 'hand' ? formatGameLogCurrentHand() : (formatGameLog() || 'No log entries yet.');
  document.getElementById('gameLogContent').textContent = content;
  // Tab styling
  document.getElementById('gameLogTabFull').style.background = _gameLogTab === 'full' ? 'rgba(255,255,255,0.15)' : 'transparent';
  document.getElementById('gameLogTabFull').style.color = _gameLogTab === 'full' ? '#fff' : 'rgba(255,255,255,0.5)';
  document.getElementById('gameLogTabHand').style.background = _gameLogTab === 'hand' ? 'rgba(255,255,255,0.15)' : 'transparent';
  document.getElementById('gameLogTabHand').style.color = _gameLogTab === 'hand' ? '#fff' : 'rgba(255,255,255,0.5)';
}

function refreshAdvLogContent(){
  const content = _advLogTab === 'hand' ? formatAdvancedLogCurrentHand() : (formatAdvancedLog() || 'No log entries yet.');
  document.getElementById('advLogContent').textContent = content;
  document.getElementById('advLogTabFull').style.background = _advLogTab === 'full' ? 'rgba(255,255,255,0.15)' : 'transparent';
  document.getElementById('advLogTabFull').style.color = _advLogTab === 'full' ? '#fff' : 'rgba(255,255,255,0.5)';
  document.getElementById('advLogTabHand').style.background = _advLogTab === 'hand' ? 'rgba(255,255,255,0.15)' : 'transparent';
  document.getElementById('advLogTabHand').style.color = _advLogTab === 'hand' ? '#fff' : 'rgba(255,255,255,0.5)';
}

// Tab click handlers
document.getElementById('gameLogTabFull').addEventListener('click', () => { _gameLogTab = 'full'; refreshGameLogContent(); });
document.getElementById('gameLogTabHand').addEventListener('click', () => { _gameLogTab = 'hand'; refreshGameLogContent(); });
document.getElementById('advLogTabFull').addEventListener('click', () => { _advLogTab = 'full'; refreshAdvLogContent(); });
document.getElementById('advLogTabHand').addEventListener('click', () => { _advLogTab = 'hand'; refreshAdvLogContent(); });

// Advanced AI Log handlers
document.getElementById('menuAdvancedLog').addEventListener('click', () => {
  document.getElementById('settingsMenu').classList.remove('open');
  refreshAdvLogContent();
  document.getElementById('advLogBackdrop').style.display = 'flex';
});"""

patches.append(('P3: Add current-hand formatters + tab logic', old_menu_handler, new_menu_handler))

# ─── P4: Update game log menu handler to use refresh function ───
old_gamelog_menu = """document.getElementById('menuGameLog').addEventListener('click', () => {
  document.getElementById('settingsMenu').classList.remove('open');
  document.getElementById('gameLogContent').textContent = formatGameLog() || 'No log entries yet.';
  document.getElementById('gameLogBackdrop').style.display = 'flex';
});"""

new_gamelog_menu = """document.getElementById('menuGameLog').addEventListener('click', () => {
  document.getElementById('settingsMenu').classList.remove('open');
  refreshGameLogContent();
  document.getElementById('gameLogBackdrop').style.display = 'flex';
});"""

patches.append(('P4: Update game log menu to use refreshGameLogContent', old_gamelog_menu, new_gamelog_menu))

# ─── P5: Update game log copy button to copy whichever tab is active ───
old_gamelog_copy = """document.getElementById('gameLogCopyBtn').addEventListener('click', () => {
  const text = formatGameLog();
  navigator.clipboard.writeText(text).then(() => {
    document.getElementById('gameLogCopyBtn').textContent = 'Copied!';
    setTimeout(() => {
      document.getElementById('gameLogCopyBtn').textContent = 'Copy Log to Clipboard';
    }, 1500);"""

new_gamelog_copy = """document.getElementById('gameLogCopyBtn').addEventListener('click', () => {
  const text = _gameLogTab === 'hand' ? formatGameLogCurrentHand() : formatGameLog();
  navigator.clipboard.writeText(text).then(() => {
    document.getElementById('gameLogCopyBtn').textContent = 'Copied!';
    setTimeout(() => {
      document.getElementById('gameLogCopyBtn').textContent = 'Copy Log to Clipboard';
    }, 1500);"""

patches.append(('P5: Game log copy uses active tab content', old_gamelog_copy, new_gamelog_copy))

# ─── P6: Update advanced log copy to use active tab ───
old_advlog_copy = """document.getElementById('advLogCopyBtn').addEventListener('click', () => {
  const text = formatAdvancedLog();
  navigator.clipboard.writeText(text).then(() => {"""

new_advlog_copy = """document.getElementById('advLogCopyBtn').addEventListener('click', () => {
  const text = _advLogTab === 'hand' ? formatAdvancedLogCurrentHand() : formatAdvancedLog();
  navigator.clipboard.writeText(text).then(() => {"""

patches.append(('P6: Advanced log copy uses active tab content', old_advlog_copy, new_advlog_copy))

# ─── P7: Update advanced log download to use active tab ───
old_advlog_dl = """document.getElementById('advLogDownloadBtn').addEventListener('click', () => {
  const text = formatAdvancedLog();"""

new_advlog_dl = """document.getElementById('advLogDownloadBtn').addEventListener('click', () => {
  const text = _advLogTab === 'hand' ? formatAdvancedLogCurrentHand() : formatAdvancedLog();"""

patches.append(('P7: Advanced log download uses active tab content', old_advlog_dl, new_advlog_dl))

# ─── Apply patches ───
ok = 0
for name, old, new in patches:
    if old in src:
        src = src.replace(old, new, 1)
        print(f'OK: {name}')
        ok += 1
    else:
        print(f'FAILED: {name} — old string not found')

with open(OUTPUT, 'w', encoding='utf-8') as f:
    f.write(src)

print(f'\nApplied {ok}/{len(patches)} patches → {OUTPUT}')
