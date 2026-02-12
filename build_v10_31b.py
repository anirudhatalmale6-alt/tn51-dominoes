#!/usr/bin/env python3
"""
V10_31b — Suppress trump info in formatAdvancedLogCurrentHand too
"""

INPUT  = '/var/lib/freelancer/projects/40101953/TN51_Dominoes_V10_31.html'
OUTPUT = INPUT  # in-place

with open(INPUT, 'r', encoding='utf-8') as f:
    src = f.read()

patches = []

# The formatAdvancedLogCurrentHand uses Unicode escapes for box chars.
# We need to add _noTrump detection and suppress trump sections.

# ─── P1: Add _noTrump tracking at start of formatAdvancedLogCurrentHand ───
old_start = """function formatAdvancedLogCurrentHand(){
  const entries = getCurrentHandEntries();
  if(entries.length === 0) return 'No current hand data.';
  // Reuse the full advanced formatter but only on current hand entries
  let text = "=== CURRENT HAND \\u2014 ADVANCED AI DEBUG ===\\n";
  text += "=== Generated: " + new Date().toISOString() + " ===\\n\\n";
  for(const entry of entries){
    if(entry.type === "HAND_START"){
      text += "\\n" + "=".repeat(70) + "\\n";
      text += " HAND " + (entry.handId + 1) + "\\n";
      text += "=".repeat(70) + "\\n";
      const c = entry.contract || {};
      text += "Contract: " + (c.mode||"NORMAL") + " | Trump: " + (c.trumpDisplay||"?");"""

new_start = """function formatAdvancedLogCurrentHand(){
  const entries = getCurrentHandEntries();
  if(entries.length === 0) return 'No current hand data.';
  // Reuse the full advanced formatter but only on current hand entries
  let text = "=== CURRENT HAND \\u2014 ADVANCED AI DEBUG ===\\n";
  text += "=== Generated: " + new Date().toISOString() + " ===\\n\\n";
  let _noTrump = false;
  for(const entry of entries){
    if(entry.type === "HAND_START"){
      const c = entry.contract || {};
      _noTrump = (c.mode === "NELLO" || c.mode === "NONE" || c.mode === "NO_TRUMP");
      text += "\\n" + "=".repeat(70) + "\\n";
      text += " HAND " + (entry.handId + 1) + "\\n";
      text += "=".repeat(70) + "\\n";
      text += "Contract: " + (c.mode||"NORMAL") + " | Trump: " + (c.trumpDisplay||"?");"""

patches.append(('P1: Add _noTrump to formatAdvancedLogCurrentHand', old_start, new_start))

# ─── P2: Suppress void trump info in currentHand formatter ───
# Find the void tracking section with Unicode chars
old_void = """        if(d.voidTracking && Object.keys(d.voidTracking).length > 0){
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
        text += " (opps void: " + d.opponentsVoidInTrump + ", partners have trump: " + d.partnersHaveTrump + ")\\n";"""

new_void = """        if(d.voidTracking && Object.keys(d.voidTracking).length > 0){
          text += "    \\u2502\\n";
          text += "    \\u2502 VOID TRACKING:\\n";
          for(const [seat, info] of Object.entries(d.voidTracking)){
            text += "    \\u2502   " + seat + " (" + info.team + "): void in suits [" + info.voidSuits.join(",") + "]";
            if(!_noTrump){
              if(info.trumpVoidConfirmed) text += " | TRUMP VOID (confirmed)";
              else if(info.trumpVoidLikely > 0) text += " | trump void likely (" + Math.round(info.trumpVoidLikely*100) + "%)";
            }
            text += "\\n";
          }
        }
        if(!_noTrump){
          text += "    \\u2502\\n";
          text += "    \\u2502 TRUMP CONTROL: " + (d.weHaveTrumpControl ? "YES" : "NO");
          text += " (opps void: " + d.opponentsVoidInTrump + ", partners have trump: " + d.partnersHaveTrump + ")\\n";
        }"""

patches.append(('P2: Suppress void trump + trump control in currentHand formatter', old_void, new_void))

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

print(f'\nApplied {ok}/{len(patches)} patches.')
