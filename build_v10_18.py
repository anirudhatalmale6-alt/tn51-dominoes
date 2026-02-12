#!/usr/bin/env python3
"""Build V10_18 — Sacrifice Low Trump for Partner Lead Strategy
New strategy: When partners hold remaining trumps and we have no doubles,
sacrifice our lowest trump to hand the lead to a partner.
"""

import sys, os

SRC = "/var/lib/freelancer/projects/40101953/TN51_Dominoes_V10_17.html"
DST = "/var/lib/freelancer/projects/40101953/TN51_Dominoes_V10_18.html"

with open(SRC, "r", encoding="utf-8") as f:
    html = f.read()

patches = 0

# ============================================================
# PATCH 1: Insert "Sacrifice Low Trump for Partner Lead" strategy
# Goes after Phase A P3 and before Phase B
# ============================================================

old_between_phases = """      }
    }

    // ── PHASE B: WE HAVE TRUMP CONTROL — play doubles, try partner-in-lead ──
    if(weHaveTrumpControl){"""

# The first "}" closes P3's if block, second "}" closes Phase A's if(!weHaveTrumpControl)
# We insert the new strategy right before Phase B

new_between_phases = """      }

      // P4: Sacrifice low trump to get partner in the lead
      // When: partners hold remaining trumps, we have no non-trump doubles to guarantee wins,
      // and we have 2+ trumps (can afford to sacrifice one).
      // Lead our LOWEST trump — partner's higher trump beats it, partner gets the lead.
      // Don't do this with only 1 trump (save it as get-back-in card).
      if(partnersHoldRemainingTrumps && nonTrumpDoubles.length === 0 && otherTrumps.length >= 2){
        // Find lowest non-double trump
        let lowIdx = otherTrumps[0], lowR = Infinity;
        for(const idx of otherTrumps){
          const r = getTrumpRankNum(hand[idx]);
          if(r < lowR){ lowR = r; lowIdx = idx; }
        }
        return makeResult(lowIdx, "Lead: low trump sacrifice (giving partner the lead)");
      }
    }

    // ── PHASE B: WE HAVE TRUMP CONTROL — play doubles, try partner-in-lead ──
    if(weHaveTrumpControl){"""

if old_between_phases not in html:
    print("ERROR: Could not find Phase A/B boundary")
    sys.exit(1)
html = html.replace(old_between_phases, new_between_phases, 1)
patches += 1
print(f"PATCH {patches}: Added sacrifice low trump for partner lead strategy")

# ============================================================
# PATCH 2: Add the strategy to the lead categories debug
# so it shows up in the advanced log when triggered
# ============================================================

old_lead_dbg = """    if(_dbg.enabled){
      _dbg.leadCategories = {
        trumpDoubles: trumpDoubles.map(i => hand[i][0]+'-'+hand[i][1]),
        otherTrumps: otherTrumps.map(i => hand[i][0]+'-'+hand[i][1]),
        nonTrumpDoubles: nonTrumpDoubles.map(i => hand[i][0]+'-'+hand[i][1]),
        nonTrumpSingles: nonTrumpSingles.map(i => hand[i][0]+'-'+hand[i][1]),
        phase: weHaveTrumpControl ? 'B (trump control)' : 'A/C (no control)'
      };
    }"""

new_lead_dbg = """    if(_dbg.enabled){
      let phaseLabel;
      if(weHaveTrumpControl) phaseLabel = 'B (trump control)';
      else if(partnersHoldRemainingTrumps) phaseLabel = 'A (partners hold trumps)';
      else phaseLabel = 'A/C (no control)';
      _dbg.leadCategories = {
        trumpDoubles: trumpDoubles.map(i => hand[i][0]+'-'+hand[i][1]),
        otherTrumps: otherTrumps.map(i => hand[i][0]+'-'+hand[i][1]),
        nonTrumpDoubles: nonTrumpDoubles.map(i => hand[i][0]+'-'+hand[i][1]),
        nonTrumpSingles: nonTrumpSingles.map(i => hand[i][0]+'-'+hand[i][1]),
        phase: phaseLabel,
        partnersHoldTrumps: partnersHoldRemainingTrumps,
        sacrificeLowTrumpEligible: partnersHoldRemainingTrumps && nonTrumpDoubles.length === 0 && otherTrumps.length >= 2
      };
    }"""

if old_lead_dbg not in html:
    print("ERROR: Could not find lead categories debug block")
    sys.exit(1)
html = html.replace(old_lead_dbg, new_lead_dbg, 1)
patches += 1
print(f"PATCH {patches}: Updated lead categories debug with sacrifice info")

# ============================================================
# PATCH 3: Update the advanced log formatter to show the new fields
# ============================================================

old_lead_display = """        if(d.leadCategories){
          const lc = d.leadCategories;
          text += "    │\\n";
          text += "    │ LEAD PHASE: " + lc.phase + "\\n";
          if(lc.trumpDoubles.length) text += "    │   Trump doubles: [" + lc.trumpDoubles.join(", ") + "]\\n";
          if(lc.otherTrumps.length) text += "    │   Other trumps: [" + lc.otherTrumps.join(", ") + "]\\n";
          if(lc.nonTrumpDoubles.length) text += "    │   Non-trump doubles: [" + lc.nonTrumpDoubles.join(", ") + "]\\n";
          if(lc.nonTrumpSingles.length) text += "    │   Non-trump singles: [" + lc.nonTrumpSingles.join(", ") + "]\\n";
        }"""

new_lead_display = """        if(d.leadCategories){
          const lc = d.leadCategories;
          text += "    │\\n";
          text += "    │ LEAD PHASE: " + lc.phase + "\\n";
          if(lc.partnersHoldTrumps) text += "    │   ★ Partners hold all remaining trumps\\n";
          if(lc.sacrificeLowTrumpEligible) text += "    │   ★ Eligible for low-trump sacrifice (no doubles, 2+ trumps)\\n";
          if(lc.trumpDoubles.length) text += "    │   Trump doubles: [" + lc.trumpDoubles.join(", ") + "]\\n";
          if(lc.otherTrumps.length) text += "    │   Other trumps: [" + lc.otherTrumps.join(", ") + "]\\n";
          if(lc.nonTrumpDoubles.length) text += "    │   Non-trump doubles: [" + lc.nonTrumpDoubles.join(", ") + "]\\n";
          if(lc.nonTrumpSingles.length) text += "    │   Non-trump singles: [" + lc.nonTrumpSingles.join(", ") + "]\\n";
        }"""

if old_lead_display not in html:
    print("ERROR: Could not find lead display in formatter")
    sys.exit(1)
html = html.replace(old_lead_display, new_lead_display, 1)
patches += 1
print(f"PATCH {patches}: Updated lead display with sacrifice indicators")

# ============================================================
# Verification
# ============================================================
checks = [
    ("low trump sacrifice", "Sacrifice strategy"),
    ("sacrificeLowTrumpEligible", "Sacrifice eligibility debug"),
    ("partnersHoldTrumps", "Partners hold trumps in debug"),
    ("Eligible for low-trump sacrifice", "Sacrifice display in log"),
    ("giving partner the lead", "Sacrifice reason text"),
]

all_ok = True
for pattern, desc in checks:
    if pattern not in html:
        print(f"  ✗ Missing: {desc}")
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
print(f"\nPatches applied: {patches}")
print(f"Source: {src_size:,} bytes")
print(f"Output: {dst_size:,} bytes")
print(f"Delta:  {dst_size - src_size:+,} bytes")
print(f"Written to: {DST}")
print("SUCCESS!")
