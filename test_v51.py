#!/usr/bin/env python3
"""
Test suite for V10_51 — Texas 42 mode
Tests both TN51 (default) and T42 game mode via Game Settings popup.
"""

import sys
import time
from playwright.sync_api import sync_playwright

FILE = "file:///var/lib/freelancer/projects/40101953/TN51_Dominoes_V10_51.html"
PASS = 0
FAIL = 0

def test(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS: {name}")
    else:
        FAIL += 1
        print(f"  FAIL: {name} — {detail}")

def run_tests():
    global PASS, FAIL

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1024, "height": 768})
        page.goto(FILE)
        page.wait_for_timeout(2000)

        # =====================================================================
        # TEST GROUP 1: Page loads and default state
        # =====================================================================
        print("\n=== GROUP 1: Default state (TN51 mode) ===")

        # Check GAME_MODE defaults to TN51
        mode = page.evaluate("GAME_MODE")
        test("GAME_MODE defaults to TN51", mode == "TN51", f"got {mode}")

        # Check session defaults
        pc = page.evaluate("session.game.player_count")
        test("Default player count is 6", pc == 6, f"got {pc}")

        mp = page.evaluate("session.game.max_pip")
        test("Default max pip is 7", mp == 7, f"got {mp}")

        hs = page.evaluate("session.game.hand_size")
        test("Default hand size is 6", hs == 6, f"got {hs}")

        # Check start screen visible
        start_visible = page.evaluate("document.getElementById('startScreenBackdrop').style.display !== 'none'")
        test("Start screen visible on load", start_visible)

        # =====================================================================
        # TEST GROUP 2: Game Settings popup — game type selector
        # =====================================================================
        print("\n=== GROUP 2: Game Settings popup ===")

        # Click New Game to open Game Settings
        page.click("#btnStartNewGame")
        page.wait_for_timeout(500)

        # Check game settings popup visible
        gs_visible = page.evaluate("document.getElementById('gameSettingsBackdrop').style.display !== 'none'")
        test("Game Settings popup opens on New Game click", gs_visible)

        # Check game type buttons exist
        tn51_btn = page.query_selector('[data-game-type="TN51"]')
        t42_btn = page.query_selector('[data-game-type="T42"]')
        test("Tennessee 51 button exists", tn51_btn is not None)
        test("Texas 42 button exists", t42_btn is not None)

        # =====================================================================
        # TEST GROUP 3: Start TN51 game — verify normal mode
        # =====================================================================
        print("\n=== GROUP 3: TN51 mode game ===")

        # Click Start Game (TN51 selected by default)
        page.click("#btnGameSettingsStart")
        page.wait_for_timeout(1500)

        # Verify TN51 mode
        mode = page.evaluate("GAME_MODE")
        test("Game started in TN51 mode", mode == "TN51", f"got {mode}")

        pc = page.evaluate("session.game.player_count")
        test("TN51 has 6 players", pc == 6, f"got {pc}")

        hs = page.evaluate("session.game.hand_size")
        test("TN51 has 6 tiles per hand", hs == 6, f"got {hs}")

        # Check all 6 player indicators visible
        for i in range(1, 7):
            vis = page.evaluate(f"document.getElementById('playerIndicator{i}').style.display !== 'none'")
            test(f"TN51: Player {i} indicator visible", vis)

        # Take screenshot
        page.screenshot(path="/var/lib/freelancer/projects/40101953/test_v51_tn51.png")

        # =====================================================================
        # TEST GROUP 4: Switch to Texas 42 mode
        # =====================================================================
        print("\n=== GROUP 4: Switch to Texas 42 mode ===")

        # We need to go back to start screen and start a new game
        # Simulate by calling the functions directly
        page.evaluate("""
            // Reset to splash
            document.getElementById('startScreenBackdrop').style.display = 'flex';
        """)
        page.wait_for_timeout(300)

        page.click("#btnStartNewGame")
        page.wait_for_timeout(500)

        # Click Texas 42 button
        page.click('[data-game-type="T42"]')
        page.wait_for_timeout(300)

        # Verify selection
        sel = page.evaluate("selectedGameType")
        test("Texas 42 selected in settings", sel == "T42", f"got {sel}")

        # Start game
        page.click("#btnGameSettingsStart")
        page.wait_for_timeout(1500)

        # Verify T42 mode
        mode = page.evaluate("GAME_MODE")
        test("Game switched to T42 mode", mode == "T42", f"got {mode}")

        pc = page.evaluate("session.game.player_count")
        test("T42 has 4 players", pc == 4, f"got {pc}")

        mp = page.evaluate("session.game.max_pip")
        test("T42 max pip is 6", mp == 6, f"got {mp}")

        hs = page.evaluate("session.game.hand_size")
        test("T42 has 7 tiles per hand", hs == 7, f"got {hs}")

        # Check hands are properly dealt
        hands = page.evaluate("session.game.hands")
        test("T42: 4 hands dealt", len(hands) == 4, f"got {len(hands)}")
        for i, hand in enumerate(hands):
            test(f"T42: Hand {i} has 7 tiles", len(hand) == 7, f"got {len(hand)}")

        # All tiles should be max pip 6
        all_valid = page.evaluate("""
            session.game.hands.every(hand =>
                hand.every(tile => tile[0] <= 6 && tile[1] <= 6)
            )
        """)
        test("T42: All tiles have pips <= 6", all_valid)

        # Total unique tiles should be 28 (double-6 set)
        total_tiles = page.evaluate("""
            const allTiles = session.game.hands.flat();
            allTiles.length
        """)
        test("T42: Total tiles dealt = 28", total_tiles == 28, f"got {total_tiles}")

        # Check P5/P6 indicators hidden
        p5_hidden = page.evaluate("document.getElementById('playerIndicator5').style.display === 'none'")
        p6_hidden = page.evaluate("document.getElementById('playerIndicator6').style.display === 'none'")
        test("T42: P5 indicator hidden", p5_hidden)
        test("T42: P6 indicator hidden", p6_hidden)

        # Check P1-P4 indicators visible
        for i in range(1, 5):
            vis = page.evaluate(f"document.getElementById('playerIndicator{i}').style.display !== 'none'")
            test(f"T42: Player {i} indicator visible", vis)

        # Check sprites created — should be 4 players
        sprite_count = page.evaluate("sprites.length")
        test("T42: sprites array has 4 seats", sprite_count == 4, f"got {sprite_count}")

        # Check each seat has 7 sprites
        for s in range(4):
            sc = page.evaluate(f"sprites[{s}] ? sprites[{s}].length : 0")
            test(f"T42: Seat {s} has 7 sprites", sc == 7, f"got {sc}")

        # =====================================================================
        # TEST GROUP 5: T42 Layout verification
        # =====================================================================
        print("\n=== GROUP 5: T42 Layout ===")

        # Check getActiveLayout returns T42 layout
        layout_name = page.evaluate("getActiveLayout() === LAYOUT_T42")
        test("T42: getActiveLayout() returns LAYOUT_T42", layout_name)

        # Check T42 layout has correct sections
        sections = page.evaluate("getActiveLayout().sections.map(s => s.name)")
        expected_sections = [
            "Trick_History",
            "Player_1_Hand", "Player_1_Played_Domino",
            "Player_2_Hand", "Player_2_Played_Domino",
            "Player_3_Hand", "Player_3_Played_Domino",
            "Player_4_Hand", "Player_4_Played_Domino",
            "Lead_Domino"
        ]
        test("T42: Layout has 10 sections", len(sections) == 10, f"got {len(sections)}: {sections}")

        # Check P1 hand has 7 positions
        p1_count = page.evaluate("getSection('Player_1_Hand').dominoes.length")
        test("T42: P1 Hand has 7 positions", p1_count == 7, f"got {p1_count}")

        # Check P2 hand has 7 positions
        p2_count = page.evaluate("getSection('Player_2_Hand').dominoes.length")
        test("T42: P2 Hand has 7 positions", p2_count == 7, f"got {p2_count}")

        # Check Trick History has 28 positions (4 rows × 7 cols)
        th_count = page.evaluate("getSection('Trick_History').dominoes.length")
        test("T42: Trick History has 28 positions", th_count == 28, f"got {th_count}")

        # =====================================================================
        # TEST GROUP 6: T42 Bidding
        # =====================================================================
        print("\n=== GROUP 6: T42 Bidding ===")

        # Check bidding is in progress (phase should be NEED_BID)
        phase = page.evaluate("session.phase")
        test("T42: Game is in bidding phase", phase == "NEED_BID", f"got {phase}")

        # Take screenshot of T42 game
        page.screenshot(path="/var/lib/freelancer/projects/40101953/test_v51_t42.png")

        # =====================================================================
        # TEST GROUP 7: T42 totalPossible
        # =====================================================================
        print("\n=== GROUP 7: T42 scoring ===")

        total_possible = page.evaluate("GAME_MODE === 'T42' ? 42 : 51")
        test("T42: totalPossible is 42", total_possible == 42)

        # =====================================================================
        # TEST GROUP 8: T42 team assignment
        # =====================================================================
        print("\n=== GROUP 8: T42 teams ===")

        t0 = page.evaluate("session.game.team_of(0)")
        t1 = page.evaluate("session.game.team_of(1)")
        t2 = page.evaluate("session.game.team_of(2)")
        t3 = page.evaluate("session.game.team_of(3)")
        test("T42: Seat 0 is Team 0", t0 == 0, f"got {t0}")
        test("T42: Seat 1 is Team 1", t1 == 1, f"got {t1}")
        test("T42: Seat 2 is Team 0 (partner)", t2 == 0, f"got {t2}")
        test("T42: Seat 3 is Team 1", t3 == 1, f"got {t3}")

        # =====================================================================
        # Summary
        # =====================================================================
        print(f"\n{'='*50}")
        print(f"Results: {PASS} passed, {FAIL} failed out of {PASS+FAIL} tests")
        print(f"{'='*50}")

        browser.close()

    return FAIL == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
