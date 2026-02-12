#!/usr/bin/env python3
"""
V10_31c — Add _noTrump tracking to formatAdvancedLogCurrentHand
"""

INPUT  = '/var/lib/freelancer/projects/40101953/TN51_Dominoes_V10_31.html'
OUTPUT = INPUT  # in-place

with open(INPUT, 'r', encoding='utf-8') as f:
    src = f.read()

# Use the actual em-dash character
old = """function formatAdvancedLogCurrentHand(){
  const entries = getCurrentHandEntries();
  if(entries.length === 0) return 'No current hand data.';
  // Reuse the full advanced formatter but only on current hand entries
  let text = "=== CURRENT HAND \u2014 ADVANCED AI DEBUG ===\\n";
  text += "=== Generated: " + new Date().toISOString() + " ===\\n\\n";
  for(const entry of entries){
    if(entry.type === "HAND_START"){
      text += "\\n" + "=".repeat(70) + "\\n";
      text += " HAND " + (entry.handId + 1) + "\\n";
      text += "=".repeat(70) + "\\n";
      const c = entry.contract || {};
      text += "Contract: " + (c.mode||"NORMAL") + " | Trump: " + (c.trumpDisplay||"?");"""

new = """function formatAdvancedLogCurrentHand(){
  const entries = getCurrentHandEntries();
  if(entries.length === 0) return 'No current hand data.';
  // Reuse the full advanced formatter but only on current hand entries
  let text = "=== CURRENT HAND \u2014 ADVANCED AI DEBUG ===\\n";
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

if old in src:
    src = src.replace(old, new, 1)
    print('OK: Added _noTrump to formatAdvancedLogCurrentHand')
else:
    print('FAILED: old string not found')

with open(OUTPUT, 'w', encoding='utf-8') as f:
    f.write(src)
