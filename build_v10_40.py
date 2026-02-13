#!/usr/bin/env python3
"""
Build V10_40: Fix PP hand gaps, toggle off, and splash robustness
- ppRotateBoard: compact non-null sprites before positioning (no gaps)
- ppDeactivate: same compaction fix
- PP menu toggle: check if already ON and deactivate instead of reopening modal
- Splash robustness: also clear saved game when PP starts new game
"""

import re, sys

SRC = "TN51_Dominoes_V10_39.html"
DST = "TN51_Dominoes_V10_40.html"

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
        print(f"FAIL {label}: found {n} occurrences, expected >= {count}")
        print(f"  Looking for: {old[:120]}...")
        sys.exit(1)
    html = html.replace(old, new, count)
    patches_ok += 1
    print(f"  OK {label}")

# =============================================================================
# PATCH 1: Fix ppRotateBoard — compact non-null sprites before positioning
# Instead of using slot index h (which leaves gaps for played tiles),
# filter non-null sprites and use recenterHand-style centering.
# =============================================================================
patch("PATCH 1: Fix ppRotateBoard hand gaps",
    """  // Reposition all hand sprites to rotated positions
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
  }""",
    """  // Reposition all hand sprites to rotated positions (compacted, no gaps)
  for (let seat = 0; seat < 6; seat++) {
    const seatSprites = sprites[seat];
    if (!seatSprites) continue;
    const visualP = ppVisualPlayer(seat);
    const isFocusSeat = (seat === viewingSeat);

    // Filter non-null sprites and position compactly (like recenterHand)
    const remaining = seatSprites.filter(d => d && d.sprite);
    const section = getSection('Player_' + visualP + '_Hand');
    if (section && section.dominoes.length >= 2 && remaining.length > 0) {
      const first = section.dominoes[0];
      const last = section.dominoes[5];
      const centerXN = (first.xN + last.xN) / 2;
      const centerYN = (first.yN + last.yN) / 2;
      const spacingXN = (last.xN - first.xN) / 5;
      const spacingYN = (last.yN - first.yN) / 5;
      const count = remaining.length;

      remaining.forEach((data, i) => {
        const offsetFromCenter = i - (count - 1) / 2;
        const xN = centerXN + offsetFromCenter * spacingXN;
        const yN = centerYN + offsetFromCenter * spacingYN;
        const px = normToPx(xN, yN);
        const targetPose = {
          x: px.x - 28,
          y: px.y - 56,
          s: first.scale,
          rz: first.rotZ,
          ry: isFocusSeat ? 180 : 0
        };
        data.sprite.setPose(targetPose);
      });
    } else {
      // Fallback: use slot-based positioning
      seatSprites.forEach((data, h) => {
        if (!data || !data.sprite) return;
        const pos = getHandPosition(visualP, h);
        if (pos) {
          data.sprite.setPose(pos);
          if (isFocusSeat) {
            data.sprite.setFaceUp(true);
          } else {
            data.sprite.setFaceUp(false);
          }
        }
      });
    }
  }""")

# =============================================================================
# PATCH 2: Fix ppDeactivate — same compaction fix for returning to normal mode
# =============================================================================
patch("PATCH 2: Fix ppDeactivate hand gaps",
    """  // Reposition everything to normal
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
  }""",
    """  // Reposition everything to normal (compacted, no gaps)
  for (let seat = 0; seat < 6; seat++) {
    const seatSprites = sprites[seat];
    if (!seatSprites) continue;
    const playerNum = seatToPlayer(seat);
    const remaining = seatSprites.filter(d => d && d.sprite);
    const section = getSection('Player_' + playerNum + '_Hand');
    if (section && section.dominoes.length >= 2 && remaining.length > 0) {
      const first = section.dominoes[0];
      const last = section.dominoes[5];
      const centerXN = (first.xN + last.xN) / 2;
      const centerYN = (first.yN + last.yN) / 2;
      const spacingXN = (last.xN - first.xN) / 5;
      const spacingYN = (last.yN - first.yN) / 5;
      const count = remaining.length;

      remaining.forEach((data, i) => {
        const offsetFromCenter = i - (count - 1) / 2;
        const xN = centerXN + offsetFromCenter * spacingXN;
        const yN = centerYN + offsetFromCenter * spacingYN;
        const px = normToPx(xN, yN);
        data.sprite.setPose({
          x: px.x - 28,
          y: px.y - 56,
          s: first.scale,
          rz: first.rotZ,
          ry: seat === 0 ? 180 : 0
        });
      });
    } else {
      seatSprites.forEach((data, h) => {
        if (!data || !data.sprite) return;
        const pos = getHandPosition(playerNum, h);
        if (pos) {
          data.sprite.setPose(pos);
          data.sprite.setFaceUp(seat === 0);
        }
      });
    }
  }""")

# =============================================================================
# PATCH 3: Fix PP menu toggle — if PP is already ON, turn it OFF
# =============================================================================
patch("PATCH 3: Fix PP toggle off",
    """document.getElementById('menuPassPlay').addEventListener('click', () => {
  document.getElementById('settingsMenu').classList.remove('open');
  ppOpenSetupModal();
});""",
    """document.getElementById('menuPassPlay').addEventListener('click', () => {
  document.getElementById('settingsMenu').classList.remove('open');
  if (PASS_AND_PLAY_MODE) {
    ppDeactivate();
  } else {
    ppOpenSetupModal();
  }
});""")

# =============================================================================
# PATCH 4: Splash robustness — clear saved game when PP starts new game
# Also make the flow more robust by ensuring splash is hidden before anything else
# =============================================================================
patch("PATCH 4: More robust PP New Game from splash",
    """  if (startNew) {
    ppResetRotation();
    hideStartScreen();
    startNewHand();
  } else {""",
    """  if (startNew) {
    ppResetRotation();
    hideStartScreen();
    clearSavedGame();
    startNewHand();
  } else {""")

print(f"\n{'='*60}")
print(f"Build complete: {patches_ok} patches applied")
print(f"Size: {len(html):,} bytes (was {original_len:,}, delta {len(html)-original_len:+,})")
write(DST, html)
print(f"Output: {DST}")
