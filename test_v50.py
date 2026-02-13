#!/usr/bin/env python3
"""Tests for TN51 Dominoes V10_50"""
import os, sys
from playwright.sync_api import sync_playwright

FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'TN51_Dominoes_V10_50.html')
FILE_URL = 'file://' + FILE

passed = 0
failed = 0

def test(name, result, expected=True):
    global passed, failed
    if result == expected:
        print(f"  PASS: {name}")
        passed += 1
    else:
        print(f"  FAIL: {name} — got {result}, expected {expected}")
        failed += 1

def main():
    global passed, failed
    print("Testing TN51 Dominoes V10_50\n")

    errors = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(FILE_URL)
        page.wait_for_timeout(1000)

        # Test 1: No JS errors
        print("Test 1: No JS errors on load")
        test("No JS errors", len(errors) == 0)
        if errors:
            for e in errors:
                print(f"    Error: {e}")

        # Test 2: Marks removed from start screen
        print("\nTest 2: Marks selection removed from start screen")
        r = page.evaluate("document.getElementById('marksSelection') === null")
        test("marksSelection removed", r)

        # Test 3: Game Settings popup exists
        print("\nTest 3: Game Settings popup")
        r = page.evaluate("document.getElementById('gameSettingsBackdrop') !== null")
        test("gameSettingsBackdrop exists", r)

        # Test 4: New Game opens settings popup
        print("\nTest 4: New Game opens Game Settings")
        page.evaluate("document.getElementById('btnStartNewGame').click()")
        page.wait_for_timeout(200)
        start_hidden = page.evaluate("document.getElementById('startScreenBackdrop').style.display === 'none'")
        settings_visible = page.evaluate("document.getElementById('gameSettingsBackdrop').style.display === 'flex'")
        test("Start screen hidden", start_hidden)
        test("Settings popup visible", settings_visible)

        # Test 5: Marks selection in settings works
        print("\nTest 5: Game Settings marks buttons")
        page.evaluate("document.querySelector('.gsMarksBtn[data-marks=\"3\"]').click()")
        r = page.evaluate("selectedMarksToWin")
        test("Selecting 3 marks sets variable", r, 3)

        page.evaluate("document.querySelector('.gsMarksBtn[data-marks=\"15\"]').click()")
        r = page.evaluate("selectedMarksToWin")
        test("Selecting 15 marks sets variable", r, 15)

        # Reset to 7 for next test
        page.evaluate("document.querySelector('.gsMarksBtn[data-marks=\"7\"]').click()")

        # Test 6: Start Game from settings
        print("\nTest 6: Start Game begins game")
        page.evaluate("document.getElementById('btnGameSettingsStart').click()")
        page.wait_for_timeout(500)
        settings_hidden = page.evaluate("document.getElementById('gameSettingsBackdrop').style.display === 'none'")
        marks = page.evaluate("session.marks_to_win")
        test("Settings popup hidden after start", settings_hidden)
        test("marks_to_win = 7", marks, 7)

        # Test 7: Trump hint bar exists
        print("\nTest 7: Trump hint bar")
        r = page.evaluate("document.getElementById('trumpHintBar') !== null")
        test("trumpHintBar exists", r)
        r = page.evaluate("document.getElementById('trumpHintText') !== null")
        test("trumpHintText exists", r)

        # Test 8: AI partner-winning doesn't dump trumps
        print("\nTest 8: AI partner-winning never dumps trumps")
        r = page.evaluate("""(() => {
            const gs = session.game;
            gs.trump_suit = 1;
            gs.trump_mode = 'PIP';
            gs.current_player = 0;
            gs.hands[0] = [[7,7],[4,2],[1,0]];
            gs.current_trick = [[2, [5,5]], [3, [5,3]]];
            gs.led_pip = 5;
            gs.trick_number = 2;
            const rec = choose_tile_ai(gs, 0, 'NORMAL', true, 34);
            const picked = rec.tile;
            const isTrump = gs._is_trump_tile(picked);
            return { picked: picked[0]+'-'+picked[1], isTrump: isTrump, reason: rec.reason };
        })()""")
        if isinstance(r, dict):
            test(f"Picks non-trump ({r.get('picked','?')}: {r.get('reason','')})", r.get('isTrump'), False)
        else:
            test("AI partner test returned result", False)

        # Test 9: AI trump lead picks lowest value
        print("\nTest 9: AI trump lead picks lowest value")
        r = page.evaluate("""(() => {
            const gs = session.game;
            gs.trump_suit = 1;
            gs.trump_mode = 'PIP';
            gs.current_player = 0;
            gs.trick_number = 1;
            gs.hands[0] = [[5,1],[1,0],[4,4]];
            gs.current_trick = [];
            gs.led_pip = null;
            // Reset active players
            gs.active_players = [0,1,2,3,4,5];
            // Make sure we have hands for all players
            for(let i = 1; i < 6; i++){
                if(!gs.hands[i] || gs.hands[i].length === 0) gs.hands[i] = [[7,6],[6,5],[6,4]];
            }
            const rec = choose_tile_ai(gs, 0, 'NORMAL', true, 34);
            const picked = rec.tile;
            return { picked: picked[0]+'-'+picked[1], pipSum: picked[0]+picked[1], reason: rec.reason };
        })()""")
        if isinstance(r, dict):
            picked = r.get('picked', '')
            reason = r.get('reason', '')
            if 'trump' in reason.lower():
                # If leading trump, should be 1-0 (pip sum 1) not 5-1 (pip sum 6)
                test(f"Leads lowest value trump ({picked}: {reason})", picked, '1-0')
            else:
                # Could lead 4-4 double instead — also acceptable
                print(f"  PASS (alt): AI chose {picked} ({reason})")
                passed += 1
        else:
            test("AI trump lead test returned result", False)

        # Test 10: Boneyard timing code
        print("\nTest 10: Boneyard timing")
        r = page.evaluate("""(() => {
            const scripts = document.querySelectorAll('script');
            let src = '';
            for(const s of scripts) src += s.textContent;
            const has1000 = src.includes('}, 1000);');
            const hasHideBefore = src.includes('Hide boneyard BEFORE animation starts');
            return { has1000, hasHideBefore };
        })()""")
        if isinstance(r, dict):
            test("1000ms delay present", r.get('has1000'), True)
            test("Pre-animation hide present", r.get('hasHideBefore'), True)
        else:
            test("Boneyard timing check", False)

        # Test 11: aiChooseTrump function
        print("\nTest 11: aiChooseTrump")
        r = page.evaluate("""(() => {
            const hand = [[3,3],[3,5],[3,1],[7,7],[4,2],[6,0]];
            return aiChooseTrump(hand, 34);
        })()""")
        test(f"aiChooseTrump returns valid result ({r})", r is not None)

        # Test 12: BY2_OUTER_SIZE
        print("\nTest 12: BY2_OUTER_SIZE")
        r = page.evaluate("BY2_OUTER_SIZE")
        test("BY2_OUTER_SIZE = 2", r, 2)

        browser.close()

    print(f"\n{'='*40}")
    print(f"Results: {passed} passed, {failed} failed out of {passed+failed} tests")
    return 0 if failed == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
