#!/usr/bin/env python3
"""Build V10_19 — Fix sacrifice low trump: verify partner can beat it
Only sacrifice our lowest trump if a partner's remaining trump can actually beat it.
If our lowest trump is higher than all remaining trumps, skip and play a non-trump instead.
"""

import sys, os

SRC = "/var/lib/freelancer/projects/40101953/TN51_Dominoes_V10_18.html"
DST = "/var/lib/freelancer/projects/40101953/TN51_Dominoes_V10_19.html"

with open(SRC, "r", encoding="utf-8") as f:
    html = f.read()

patches = 0

# ============================================================
# PATCH 1: Add rank check to sacrifice strategy
# ============================================================

old_sacrifice = """      // P4: Sacrifice low trump to get partner in the lead
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
      }"""

new_sacrifice = """      // P4: Sacrifice low trump to get partner in the lead
      // When: partners hold remaining trumps, we have no non-trump doubles to guarantee wins,
      // and we have 2+ trumps (can afford to sacrifice one).
      // Lead our LOWEST trump — partner's higher trump beats it, partner gets the lead.
      // CRITICAL: Only do this if a partner's trump can actually BEAT our lowest trump.
      // If our lowest trump outranks all remaining trumps, we'd win our own trick (pointless).
      // Don't do this with only 1 trump (save it as get-back-in card).
      if(partnersHoldRemainingTrumps && nonTrumpDoubles.length === 0 && otherTrumps.length >= 2){
        // Find lowest non-double trump in our hand
        let lowIdx = otherTrumps[0], lowR = Infinity;
        for(const idx of otherTrumps){
          const r = getTrumpRankNum(hand[idx]);
          if(r < lowR){ lowR = r; lowIdx = idx; }
        }
        // Check: can any remaining trump (held by partner) beat our lowest?
        const highestPartnerTrump = trumpTilesRemaining.length > 0
          ? Math.max(...trumpTilesRemaining.map(getTrumpRankNum)) : -1;
        if(highestPartnerTrump > lowR){
          return makeResult(lowIdx, "Lead: low trump sacrifice (giving partner the lead)");
        }
        // Partner can't beat our lowest trump — skip sacrifice, fall through to non-trump leads
      }"""

if old_sacrifice not in html:
    print("ERROR: Could not find sacrifice block")
    sys.exit(1)
html = html.replace(old_sacrifice, new_sacrifice, 1)
patches += 1
print(f"PATCH {patches}: Added rank check to sacrifice strategy")

# ============================================================
# PATCH 2: Update debug info to show the rank comparison
# ============================================================

old_sacrifice_dbg = """        sacrificeLowTrumpEligible: partnersHoldRemainingTrumps && nonTrumpDoubles.length === 0 && otherTrumps.length >= 2"""

new_sacrifice_dbg = """        sacrificeLowTrumpEligible: partnersHoldRemainingTrumps && nonTrumpDoubles.length === 0 && otherTrumps.length >= 2,
        sacrificeRankCheck: (function(){
          if(!partnersHoldRemainingTrumps || nonTrumpDoubles.length > 0 || otherTrumps.length < 2) return null;
          const myLow = Math.min(...otherTrumps.map(i => getTrumpRankNum(hand[i])));
          const partnerHigh = trumpTilesRemaining.length > 0 ? Math.max(...trumpTilesRemaining.map(getTrumpRankNum)) : -1;
          return { myLowestRank: myLow, partnerHighestRank: partnerHigh, partnerCanBeat: partnerHigh > myLow };
        })()"""

if old_sacrifice_dbg not in html:
    print("ERROR: Could not find sacrifice debug block")
    sys.exit(1)
html = html.replace(old_sacrifice_dbg, new_sacrifice_dbg, 1)
patches += 1
print(f"PATCH {patches}: Updated debug with rank comparison info")

# ============================================================
# PATCH 3: Update the advanced log formatter to show rank check
# ============================================================

old_sacrifice_display = """          if(lc.sacrificeLowTrumpEligible) text += "    │   ★ Eligible for low-trump sacrifice (no doubles, 2+ trumps)\\n";"""

new_sacrifice_display = """          if(lc.sacrificeLowTrumpEligible){
            text += "    │   ★ Low-trump sacrifice check (no doubles, 2+ trumps)";
            if(lc.sacrificeRankCheck){
              const rc = lc.sacrificeRankCheck;
              text += ": my lowest=" + rc.myLowestRank + " vs partner highest=" + rc.partnerHighestRank;
              text += rc.partnerCanBeat ? " → SACRIFICE OK" : " → SKIP (partner can't beat)";
            }
            text += "\\n";
          }"""

if old_sacrifice_display not in html:
    print("ERROR: Could not find sacrifice display block")
    sys.exit(1)
html = html.replace(old_sacrifice_display, new_sacrifice_display, 1)
patches += 1
print(f"PATCH {patches}: Updated log display with rank comparison")

# ============================================================
# Verification
# ============================================================
checks = [
    ("highestPartnerTrump > lowR", "Rank check in sacrifice logic"),
    ("partnerCanBeat", "Rank check in debug"),
    ("SACRIFICE OK", "Sacrifice OK display"),
    ("SKIP (partner can't beat)", "Sacrifice skip display"),
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
