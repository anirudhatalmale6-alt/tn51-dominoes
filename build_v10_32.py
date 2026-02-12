#!/usr/bin/env python3
"""
Build script for TN51 Dominoes V10_32

Patches V10_31 with:
  PATCH 1: Add END OF TRICK STATE to current hand formatter's TRICK_END display
  PATCH 2: Show ALL opponents' void status in debug output (not just confirmed/likely)
           - 2a: Update choose_tile_ai() debug to always include all non-self players
           - 2b: Update full log formatter void display to handle empty voids
           - 2c: Update current hand formatter void display to handle empty voids

Note: The full log formatter uses literal UTF-8 box-drawing characters,
while the current hand formatter uses \\u2502-style JS escape sequences.
"""

import os
import sys

SRC = "/var/lib/freelancer/projects/40101953/TN51_Dominoes_V10_31.html"
DST = "/var/lib/freelancer/projects/40101953/TN51_Dominoes_V10_32.html"

def patch(html, old, new, label):
    if old not in html:
        print(f"ERROR: Could not find patch target for {label}")
        print(f"  Looking for: {repr(old[:200])}...")
        sys.exit(1)
    count = html.count(old)
    if count != 1:
        print(f"ERROR: Found {count} occurrences of patch target for {label} (expected 1)")
        sys.exit(1)
    html = html.replace(old, new)
    print(f"  OK: {label}")
    return html


def main():
    print(f"Reading {SRC}...")
    with open(SRC, "r", encoding="utf-8") as f:
        html = f.read()
    print(f"  Size: {len(html):,} bytes")

    # =========================================================================
    # PATCH 1: Add END OF TRICK STATE to current hand formatter
    # The current hand formatter TRICK_END section uses literal UTF-8 chars
    # for the box drawing (same as full log). We match the exact text.
    # =========================================================================
    print("\nPATCH 1: Add END OF TRICK STATE to current hand TRICK_END formatter")

    old_1 = (
        '    else if(entry.type === "TRICK_END"){\n'
        '      text += "  >> Winner: P" + seatToPlayer(entry.winnerSeat) + " (Team " + entry.winnerTeam + ") +" + entry.pointsInTrick + " pts\\n";\n'
        '    }\n'
        '    else if(entry.type === "HAND_END"){\n'
        '      const scores = entry.finalScores || {};\n'
        '      text += "\\n" + "=".repeat(70) + "\\n";\n'
        '      text += "HAND " + (entry.handId+1) + " RESULT: Team1=" + (scores.team1||0) + " Team2=" + (scores.team2||0);\n'
        '      text += " | " + (entry.winner||"") + " | Bid made: " + (entry.bidMade ? "Yes" : "No") + "\\n";\n'
        '      text += "=".repeat(70) + "\\n";\n'
        '    }'
    )

    new_1 = (
        '    else if(entry.type === "TRICK_END"){\n'
        '      text += "  >> Winner: P" + seatToPlayer(entry.winnerSeat) + " (Team " + entry.winnerTeam + ") +" + entry.pointsInTrick + " pts\\n";\n'
        '\n'
        '      // End-of-trick state summary\n'
        '      const ts = entry.trickEndState;\n'
        '      if(ts){\n'
        '        text += "  \u250c\u2500\u2500\u2500 END OF TRICK STATE \u2500\u2500\u2500\\n";\n'
        '        text += "  \u2502 Scores: Team1=" + ts.teamScores[0] + " Team2=" + ts.teamScores[1] + "\\n";\n'
        '\n'
        '        if(ts.bidSafety){\n'
        '          const b = ts.bidSafety;\n'
        '          text += "  \u2502 Bid: " + b.currentBid + " | Need: " + b.pointsNeeded + " | ";\n'
        '          if(b.bidIsSafe) text += "SAFE";\n'
        '          else if(b.bidIsClose) text += "CLOSE!";\n'
        '          else text += "still working";\n'
        '          text += " | Tricks left: " + b.tricksLeft + "\\n";\n'
        '        }\n'
        '\n'
        '        if(!_noTrump){\n'
        '          if(ts.trumpsInHand && ts.trumpsInHand.length > 0){\n'
        '            text += "  \u2502 P1 trumps: [" + ts.trumpsInHand.join(", ") + "]\\n";\n'
        '          }\n'
        '          if(ts.trumpsRemaining && ts.trumpsRemaining.length > 0){\n'
        '            text += "  \u2502 Trumps still out: [" + ts.trumpsRemaining.join(", ") + "]\\n";\n'
        '          } else {\n'
        '            text += "  \u2502 Trumps still out: none (all accounted for)\\n";\n'
        '          }\n'
        '\n'
        '          text += "  \u2502 Trump control: " + (ts.trumpControl ? "YES" : "NO");\n'
        '          text += " (opps void: " + ts.opponentsVoidInTrump;\n'
        '          if(ts.partnersHaveTrump !== undefined) text += ", partners trump: " + ts.partnersHaveTrump;\n'
        '          text += ")\\n";\n'
        '        }\n'
        '\n'
        '        const vt = ts.voidTracking;\n'
        '        if(vt && Object.keys(vt).length > 0){\n'
        '          text += "  \u2502 KNOWN VOIDS:\\n";\n'
        '          for(const [seat, info] of Object.entries(vt)){\n'
        '            if(info.voidSuits && info.voidSuits.length === 0 && !info.trumpVoidConfirmed && !(info.trumpVoidLikely > 0)){\n'
        '              text += "  \u2502   " + seat + " (" + info.team + "): no voids detected\\n";\n'
        '            } else {\n'
        '              text += "  \u2502   " + seat + " (" + info.team + "):";\n'
        '              if(info.voidSuits && info.voidSuits.length > 0) text += " void in suits [" + info.voidSuits.join(",") + "]";\n'
        '              if(!_noTrump){\n'
        '                if(info.trumpVoidConfirmed) text += " | TRUMP VOID";\n'
        '                else if(info.trumpVoidLikely > 0) text += " | trump void " + Math.round(info.trumpVoidLikely*100) + "%";\n'
        '              }\n'
        '              text += "\\n";\n'
        '            }\n'
        '          }\n'
        '        } else {\n'
        '          text += "  \u2502 KNOWN VOIDS: none detected yet\\n";\n'
        '        }\n'
        '        text += "  \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\\n";\n'
        '      }\n'
        '    }\n'
        '    else if(entry.type === "HAND_END"){\n'
        '      const scores = entry.finalScores || {};\n'
        '      text += "\\n" + "=".repeat(70) + "\\n";\n'
        '      text += "HAND " + (entry.handId+1) + " RESULT: Team1=" + (scores.team1||0) + " Team2=" + (scores.team2||0);\n'
        '      text += " | " + (entry.winner||"") + " | Bid made: " + (entry.bidMade ? "Yes" : "No") + "\\n";\n'
        '      text += "=".repeat(70) + "\\n";\n'
        '    }'
    )

    html = patch(html, old_1, new_1, "PATCH 1: Current hand TRICK_END -> add END OF TRICK STATE")

    # =========================================================================
    # PATCH 2a: Update choose_tile_ai() debug to always include all non-self players
    # =========================================================================
    print("\nPATCH 2a: Update choose_tile_ai() debug void tracking to include all players")

    old_2a = (
        "  // Debug: void tracking + trump control\n"
        "  if(_dbg.enabled){\n"
        "    _dbg.voidTracking = {};\n"
        "    for(let s = 0; s < gameState.player_count; s++){\n"
        "      if(s === p) continue;\n"
        "      const voids = Array.from(voidIn[s]);\n"
        "      if(voids.length > 0 || trumpVoidConfirmed[s] || trumpVoidLikely[s] > 0){\n"
        "        const pLabel = (typeof seatToPlayer === 'function') ? ('P'+seatToPlayer(s)) : ('P'+(s+1));\n"
        "        _dbg.voidTracking[pLabel] = {\n"
        "          team: s % 2 === myTeam ? 'ours' : 'opp',\n"
        "          voidSuits: voids,\n"
        "          trumpVoidConfirmed: trumpVoidConfirmed[s],\n"
        "          trumpVoidLikely: trumpVoidLikely[s]\n"
        "        };\n"
        "      }\n"
        "    }"
    )

    new_2a = (
        "  // Debug: void tracking + trump control\n"
        "  if(_dbg.enabled){\n"
        "    _dbg.voidTracking = {};\n"
        "    for(let s = 0; s < gameState.player_count; s++){\n"
        "      if(s === p) continue;\n"
        "      const voids = Array.from(voidIn[s]);\n"
        "      const pLabel = (typeof seatToPlayer === 'function') ? ('P'+seatToPlayer(s)) : ('P'+(s+1));\n"
        "      _dbg.voidTracking[pLabel] = {\n"
        "        team: s % 2 === myTeam ? 'ours' : 'opp',\n"
        "        voidSuits: voids,\n"
        "        trumpVoidConfirmed: trumpVoidConfirmed[s],\n"
        "        trumpVoidLikely: trumpVoidLikely[s]\n"
        "      };\n"
        "    }"
    )

    html = patch(html, old_2a, new_2a, "PATCH 2a: Debug void tracking -> include all players")

    # =========================================================================
    # PATCH 2b: Update full log formatter void display to handle empty voids
    # The full log formatter uses LITERAL UTF-8 box-drawing characters
    # =========================================================================
    print("\nPATCH 2b: Update full log formatter void display for empty voids")

    # Use literal Unicode box-drawing chars (│ = U+2502)
    BOX_V = "\u2502"  # │

    old_2b = (
        '        // Void tracking (suppress trump void info in Nello/No Trump)\n'
        '        if(d.voidTracking && Object.keys(d.voidTracking).length > 0){\n'
        f'          text += "    {BOX_V}\\n";\n'
        f'          text += "    {BOX_V} VOID TRACKING:\\n";\n'
        '          for(const [seat, info] of Object.entries(d.voidTracking)){\n'
        f'            text += "    {BOX_V}   " + seat + " (" + info.team + "): void in suits [" + info.voidSuits.join(",") + "]";\n'
        '            if(!_noTrump){\n'
        '              if(info.trumpVoidConfirmed) text += " | TRUMP VOID (confirmed)";\n'
        '              else if(info.trumpVoidLikely > 0) text += " | trump void likely (" + Math.round(info.trumpVoidLikely*100) + "%)";\n'
        '            }\n'
        '            text += "\\n";\n'
        '          }\n'
        '        }'
    )

    new_2b = (
        '        // Void tracking (suppress trump void info in Nello/No Trump)\n'
        '        if(d.voidTracking && Object.keys(d.voidTracking).length > 0){\n'
        f'          text += "    {BOX_V}\\n";\n'
        f'          text += "    {BOX_V} VOID TRACKING:\\n";\n'
        '          for(const [seat, info] of Object.entries(d.voidTracking)){\n'
        '            if(info.voidSuits && info.voidSuits.length === 0 && !info.trumpVoidConfirmed && !(info.trumpVoidLikely > 0)){\n'
        f'              text += "    {BOX_V}   " + seat + " (" + info.team + "): no voids detected\\n";\n'
        '            } else {\n'
        f'              text += "    {BOX_V}   " + seat + " (" + info.team + "): void in suits [" + info.voidSuits.join(",") + "]";\n'
        '              if(!_noTrump){\n'
        '                if(info.trumpVoidConfirmed) text += " | TRUMP VOID (confirmed)";\n'
        '                else if(info.trumpVoidLikely > 0) text += " | trump void likely (" + Math.round(info.trumpVoidLikely*100) + "%)";\n'
        '              }\n'
        '              text += "\\n";\n'
        '            }\n'
        '          }\n'
        '        }'
    )

    html = patch(html, old_2b, new_2b, "PATCH 2b: Full log void display -> handle empty voids")

    # =========================================================================
    # PATCH 2c: Update current hand formatter void display to handle empty voids
    # The current hand formatter uses JS ESCAPE SEQUENCES: \\u2502
    # So in the file the literal text is \u2502, which in Python is \\u2502
    # =========================================================================
    print("\nPATCH 2c: Update current hand formatter void display for empty voids")

    # The file literally contains the six characters: \u2502
    # In Python string, that's: \\u2502
    ESC_V = "\\u2502"  # literal \u2502 in the file

    old_2c = (
        '        if(d.voidTracking && Object.keys(d.voidTracking).length > 0){\n'
        f'          text += "    {ESC_V}\\n";\n'
        f'          text += "    {ESC_V} VOID TRACKING:\\n";\n'
        '          for(const [seat, info] of Object.entries(d.voidTracking)){\n'
        f'            text += "    {ESC_V}   " + seat + " (" + info.team + "): void in suits [" + info.voidSuits.join(",") + "]";\n'
        '            if(!_noTrump){\n'
        '              if(info.trumpVoidConfirmed) text += " | TRUMP VOID (confirmed)";\n'
        '              else if(info.trumpVoidLikely > 0) text += " | trump void likely (" + Math.round(info.trumpVoidLikely*100) + "%)";\n'
        '            }\n'
        '            text += "\\n";\n'
        '          }\n'
        '        }\n'
        '        if(!_noTrump){\n'
        f'          text += "    {ESC_V}\\n";\n'
        f'          text += "    {ESC_V} TRUMP CONTROL: " + (d.weHaveTrumpControl ? "YES" : "NO");'
    )

    new_2c = (
        '        if(d.voidTracking && Object.keys(d.voidTracking).length > 0){\n'
        f'          text += "    {ESC_V}\\n";\n'
        f'          text += "    {ESC_V} VOID TRACKING:\\n";\n'
        '          for(const [seat, info] of Object.entries(d.voidTracking)){\n'
        '            if(info.voidSuits && info.voidSuits.length === 0 && !info.trumpVoidConfirmed && !(info.trumpVoidLikely > 0)){\n'
        f'              text += "    {ESC_V}   " + seat + " (" + info.team + "): no voids detected\\n";\n'
        '            } else {\n'
        f'              text += "    {ESC_V}   " + seat + " (" + info.team + "): void in suits [" + info.voidSuits.join(",") + "]";\n'
        '              if(!_noTrump){\n'
        '                if(info.trumpVoidConfirmed) text += " | TRUMP VOID (confirmed)";\n'
        '                else if(info.trumpVoidLikely > 0) text += " | trump void likely (" + Math.round(info.trumpVoidLikely*100) + "%)";\n'
        '              }\n'
        '              text += "\\n";\n'
        '            }\n'
        '          }\n'
        '        }\n'
        '        if(!_noTrump){\n'
        f'          text += "    {ESC_V}\\n";\n'
        f'          text += "    {ESC_V} TRUMP CONTROL: " + (d.weHaveTrumpControl ? "YES" : "NO");'
    )

    html = patch(html, old_2c, new_2c, "PATCH 2c: Current hand void display -> handle empty voids")

    # =========================================================================
    # Write output
    # =========================================================================
    print(f"\nWriting {DST}...")
    with open(DST, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  Size: {len(html):,} bytes")
    print("\nDone! V10_32 built successfully.")


if __name__ == "__main__":
    main()
