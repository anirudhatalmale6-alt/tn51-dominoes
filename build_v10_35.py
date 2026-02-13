#!/usr/bin/env python3
"""Build V10_35 from V10_34 — Fix Monte Carlo simulation bugs + add copy button"""

import os

SRC = 'TN51_Dominoes_V10_34.html'
DST = 'TN51_Dominoes_V10_35.html'

with open(SRC, 'r', encoding='utf-8') as f:
    html = f.read()

original_size = len(html)
patches_applied = 0

def patch(old, new, desc):
    global html, patches_applied
    if old not in html:
        print(f"  FAILED: {desc}")
        print(f"  Could not find: {old[:120]}...")
        return False
    count = html.count(old)
    if count > 1:
        print(f"  WARNING: {desc} — found {count} occurrences, replacing first only")
        html = html.replace(old, new, 1)
    else:
        html = html.replace(old, new)
    patches_applied += 1
    print(f"  OK: {desc}")
    return True

# ============================================================
# PATCH 1: Fix the critical bug — clear current_trick after each trick completes
# The game engine's play_tile() does NOT clear current_trick after a trick.
# The UI code does this manually. The simulation must do it too.
# ============================================================
patch(
    '      // Check if trick completed (result[2] === true means trick finished)\n'
    '      if (result && result[2]) {\n'
    '        const winner = result[1];\n'
    '        const winnerTeam = sim.team_of(winner);',

    '      // Check if trick completed (result[2] === true means trick finished)\n'
    '      if (result && result[2]) {\n'
    '        // CRITICAL: Clear current_trick — play_tile does NOT do this.\n'
    '        // Without this, plays accumulate across tricks and scoring breaks.\n'
    '        sim.current_trick = [];\n'
    '        const winner = result[1];\n'
    '        const winnerTeam = sim.team_of(winner);',

    "PATCH 1: Clear current_trick after trick completes in simulation"
)

# ============================================================
# PATCH 2: Cap bidder points at 51 in score display (safety net)
# Even after fix, display should never show > 51
# ============================================================
patch(
    "html += '<span>Avg score when made: ' + avg(r.scoreWhenMade, r.madeCount) + '</span>';",

    "html += '<span>Avg score when made: ' + Math.min(51, parseFloat(avg(r.scoreWhenMade, r.madeCount))).toFixed(1) + '</span>';",

    "PATCH 2: Cap avg score display at 51"
)

# ============================================================
# PATCH 3: Add "Copy Results" button to MC modal
# Add after the Reset Order button area
# ============================================================
patch(
    '        <div id="mcProgress" style="display:none;text-align:center;padding:10px;">',

    '        <div id="mcCopyRow" style="display:none;text-align:center;margin-bottom:12px;">\n'
    '          <button id="mcCopyBtn" style="padding:6px 14px;background:rgba(59,130,246,0.8);border:none;border-radius:8px;color:#fff;font-weight:600;font-size:12px;cursor:pointer;">Copy Results</button>\n'
    '        </div>\n'
    '        <div id="mcProgress" style="display:none;text-align:center;padding:10px;">',

    "PATCH 3: Add Copy Results button HTML"
)

# ============================================================
# PATCH 4: Add copy results event listener and show/hide logic
# After mcRunBtn listener
# ============================================================
patch(
    "  document.getElementById('mcRunBtn').addEventListener('click', () => {\n"
    "    if (mcRunning) return;\n"
    "    mcStartSimulation();\n"
    "  });",

    "  document.getElementById('mcRunBtn').addEventListener('click', () => {\n"
    "    if (mcRunning) return;\n"
    "    mcStartSimulation();\n"
    "  });\n"
    "\n"
    "  document.getElementById('mcCopyBtn').addEventListener('click', () => {\n"
    "    const resultsDiv = document.getElementById('mcResults');\n"
    "    if (!resultsDiv || resultsDiv.style.display === 'none') return;\n"
    "    const text = resultsDiv.innerText;\n"
    "    navigator.clipboard.writeText(text).then(() => {\n"
    "      document.getElementById('mcCopyBtn').textContent = 'Copied!';\n"
    "      setTimeout(() => { document.getElementById('mcCopyBtn').textContent = 'Copy Results'; }, 1500);\n"
    "    }).catch(e => { console.error('Copy failed:', e); });\n"
    "  });",

    "PATCH 4: Add copy button event listener"
)

# ============================================================
# PATCH 5: Show copy button when results are displayed
# In the displayResults function, show the copy row
# ============================================================
patch(
    "    div.innerHTML = html;\n"
    "  }\n"
    "\n"
    "  function mcResultRow",

    "    div.innerHTML = html;\n"
    "    // Show copy button\n"
    "    document.getElementById('mcCopyRow').style.display = 'block';\n"
    "  }\n"
    "\n"
    "  function mcResultRow",

    "PATCH 5: Show copy button when results display"
)

# ============================================================
# PATCH 6: Hide copy button when reset or new sim starts
# In mcStartSimulation, hide copy row
# ============================================================
patch(
    "  function mcStartSimulation() {\n"
    "    if (mcSelectedOrder.length !== mcPlayerHand.length) return;\n"
    "    mcRunning = true;",

    "  function mcStartSimulation() {\n"
    "    if (mcSelectedOrder.length !== mcPlayerHand.length) return;\n"
    "    mcRunning = true;\n"
    "    document.getElementById('mcCopyRow').style.display = 'none';",

    "PATCH 6: Hide copy button when starting new simulation"
)

# ============================================================
# Write output
# ============================================================
with open(DST, 'w', encoding='utf-8') as f:
    f.write(html)

new_size = len(html)
print(f"\nApplied {patches_applied} patches")
print(f"Output: {DST} ({new_size} bytes, delta: {new_size - original_size:+d})")
