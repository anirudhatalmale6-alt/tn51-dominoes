#!/usr/bin/env python3
"""
V10_31 Build Script — Suppress trump info in logs for Nello/No Trump modes
"""

INPUT  = '/var/lib/freelancer/projects/40101953/TN51_Dominoes_V10_30.html'
OUTPUT = '/var/lib/freelancer/projects/40101953/TN51_Dominoes_V10_31.html'

with open(INPUT, 'r', encoding='utf-8') as f:
    src = f.read()

patches = []

# ─── P1: Add contract mode tracking in formatAdvancedLog ───
# Add a variable to track if current hand is nello/no-trump, right before the loop
old_adv_loop = """  for(const entry of gameLog){
    if(entry.type === "HAND_START"){
      text += "\\n" + "=".repeat(70) + "\\n";
      text += " HAND " + (entry.handId + 1) + "\\n";
      text += "=".repeat(70) + "\\n";
      const c = entry.contract || {};
      text += "Contract: " + (c.mode||"NORMAL") + " | Trump: " + (c.trumpDisplay||"?");
      text += " | Bid: " + (c.bid||"?") + " by P" + seatToPlayer(c.bidderSeat||0);
      text += " (Team " + (c.bidderTeam||"?") + ")\\n";"""

new_adv_loop = """  let _noTrump = false;  // Track if current hand has no trumps (Nello or No Trump)
  for(const entry of gameLog){
    if(entry.type === "HAND_START"){
      const c = entry.contract || {};
      _noTrump = (c.mode === "NELLO" || c.mode === "NONE" || c.mode === "NO_TRUMP");
      text += "\\n" + "=".repeat(70) + "\\n";
      text += " HAND " + (entry.handId + 1) + "\\n";
      text += "=".repeat(70) + "\\n";
      text += "Contract: " + (c.mode||"NORMAL") + " | Trump: " + (c.trumpDisplay||"?");
      text += " | Bid: " + (c.bid||"?") + " by P" + seatToPlayer(c.bidderSeat||0);
      text += " (Team " + (c.bidderTeam||"?") + ")\\n";"""

patches.append(('P1: Add _noTrump tracking in formatAdvancedLog', old_adv_loop, new_adv_loop))

# ─── P2: Suppress TRUMP section in PLAY entries ───
# The trump info block already has a check for d.trumpMode !== "NONE", which is good.
# But we need to suppress VOID TRACKING trump-related info and TRUMP CONTROL line when _noTrump
old_void_section = """        // Void tracking
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
        text += " (opps void: " + d.opponentsVoidInTrump + ", partners have trump: " + d.partnersHaveTrump;
        if(d.partnersHoldRemainingTrumps) text += ", PARTNERS HOLD ALL REMAINING TRUMPS";
        text += ")\\n";"""

new_void_section = """        // Void tracking (suppress trump void info in Nello/No Trump)
        if(d.voidTracking && Object.keys(d.voidTracking).length > 0){
          text += "    │\\n";
          text += "    │ VOID TRACKING:\\n";
          for(const [seat, info] of Object.entries(d.voidTracking)){
            text += "    │   " + seat + " (" + info.team + "): void in suits [" + info.voidSuits.join(",") + "]";
            if(!_noTrump){
              if(info.trumpVoidConfirmed) text += " | TRUMP VOID (confirmed)";
              else if(info.trumpVoidLikely > 0) text += " | trump void likely (" + Math.round(info.trumpVoidLikely*100) + "%)";
            }
            text += "\\n";
          }
        }

        // Trump control (skip entirely in Nello/No Trump)
        if(!_noTrump){
          text += "    │\\n";
          text += "    │ TRUMP CONTROL: " + (d.weHaveTrumpControl ? "YES ✓" : "NO");
          text += " (opps void: " + d.opponentsVoidInTrump + ", partners have trump: " + d.partnersHaveTrump;
          if(d.partnersHoldRemainingTrumps) text += ", PARTNERS HOLD ALL REMAINING TRUMPS";
          text += ")\\n";
        }"""

patches.append(('P2: Suppress void trump info + trump control in Nello/No Trump', old_void_section, new_void_section))

# ─── P3: Suppress Last Trump section ───
old_last_trump = """        // Last trump
        if(d.lastTrump){
          text += "    │ LAST TRUMP: " + (d.lastTrump.isLastTrump ? "YES, only 1 left" : "No");
          if(d.lastTrump.isLastTrump) text += " → " + (d.lastTrump.shouldSaveLastTrump ? "SAVING IT" : "will use if needed");
          text += "\\n";
        }"""

new_last_trump = """        // Last trump (skip in Nello/No Trump)
        if(d.lastTrump && !_noTrump){
          text += "    │ LAST TRUMP: " + (d.lastTrump.isLastTrump ? "YES, only 1 left" : "No");
          if(d.lastTrump.isLastTrump) text += " → " + (d.lastTrump.shouldSaveLastTrump ? "SAVING IT" : "will use if needed");
          text += "\\n";
        }"""

patches.append(('P3: Suppress last trump in Nello/No Trump', old_last_trump, new_last_trump))

# ─── P4: Suppress trump-related lead categories ───
old_lead_cats = """          if(lc.trumpDoubles.length) text += "    │   Trump doubles: [" + lc.trumpDoubles.join(", ") + "]\\n";
          if(lc.otherTrumps.length) text += "    │   Other trumps: [" + lc.otherTrumps.join(", ") + "]\\n";"""

new_lead_cats = """          if(!_noTrump && lc.trumpDoubles.length) text += "    │   Trump doubles: [" + lc.trumpDoubles.join(", ") + "]\\n";
          if(!_noTrump && lc.otherTrumps.length) text += "    │   Other trumps: [" + lc.otherTrumps.join(", ") + "]\\n";"""

patches.append(('P4: Suppress trump lead categories in Nello/No Trump', old_lead_cats, new_lead_cats))

# ─── P5: Suppress trump-in section ───
old_trump_in = """        // Trump-in debug
        if(d.trumpIn){"""

new_trump_in = """        // Trump-in debug (skip in Nello/No Trump)
        if(d.trumpIn && !_noTrump){"""

patches.append(('P5: Suppress trump-in in Nello/No Trump', old_trump_in, new_trump_in))

# ─── P6: Suppress trump info in END OF TRICK STATE ───
old_trick_end_trump = """        if(ts.trumpsInHand && ts.trumpsInHand.length > 0){
          text += "  │ P1 trumps: [" + ts.trumpsInHand.join(", ") + "]\\n";
        }
        if(ts.trumpsRemaining && ts.trumpsRemaining.length > 0){
          text += "  │ Trumps still out: [" + ts.trumpsRemaining.join(", ") + "]\\n";
        } else {
          text += "  │ Trumps still out: none (all accounted for)\\n";
        }

        text += "  │ Trump control: " + (ts.trumpControl ? "YES" : "NO");
        text += " (opps void: " + ts.opponentsVoidInTrump;
        if(ts.partnersHaveTrump !== undefined) text += ", partners trump: " + ts.partnersHaveTrump;
        text += ")\\n";

        const vt = ts.voidTracking;
        if(vt && Object.keys(vt).length > 0){
          text += "  │ KNOWN VOIDS:\\n";
          for(const [seat, info] of Object.entries(vt)){
            text += "  │   " + seat + " (" + info.team + "):";
            if(info.voidSuits && info.voidSuits.length > 0) text += " void in suits [" + info.voidSuits.join(",") + "]";
            if(info.trumpVoidConfirmed) text += " | TRUMP VOID";
            else if(info.trumpVoidLikely > 0) text += " | trump void " + Math.round(info.trumpVoidLikely*100) + "%";
            text += "\\n";
          }
        } else {
          text += "  │ KNOWN VOIDS: none detected yet\\n";
        }"""

new_trick_end_trump = """        if(!_noTrump){
          if(ts.trumpsInHand && ts.trumpsInHand.length > 0){
            text += "  │ P1 trumps: [" + ts.trumpsInHand.join(", ") + "]\\n";
          }
          if(ts.trumpsRemaining && ts.trumpsRemaining.length > 0){
            text += "  │ Trumps still out: [" + ts.trumpsRemaining.join(", ") + "]\\n";
          } else {
            text += "  │ Trumps still out: none (all accounted for)\\n";
          }

          text += "  │ Trump control: " + (ts.trumpControl ? "YES" : "NO");
          text += " (opps void: " + ts.opponentsVoidInTrump;
          if(ts.partnersHaveTrump !== undefined) text += ", partners trump: " + ts.partnersHaveTrump;
          text += ")\\n";
        }

        const vt = ts.voidTracking;
        if(vt && Object.keys(vt).length > 0){
          text += "  │ KNOWN VOIDS:\\n";
          for(const [seat, info] of Object.entries(vt)){
            text += "  │   " + seat + " (" + info.team + "):";
            if(info.voidSuits && info.voidSuits.length > 0) text += " void in suits [" + info.voidSuits.join(",") + "]";
            if(!_noTrump){
              if(info.trumpVoidConfirmed) text += " | TRUMP VOID";
              else if(info.trumpVoidLikely > 0) text += " | trump void " + Math.round(info.trumpVoidLikely*100) + "%";
            }
            text += "\\n";
          }
        } else {
          text += "  │ KNOWN VOIDS: none detected yet\\n";
        }"""

patches.append(('P6: Suppress trump info in END OF TRICK STATE for Nello/No Trump', old_trick_end_trump, new_trick_end_trump))

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
