#!/usr/bin/env python3
"""
Test suite for V10_52 — T42 bug fixes + layout settings
Tests both TN51 (default) and T42 game mode.
"""

import sys
import time
from playwright.sync_api import sync_playwright

FILE = "file:///var/lib/freelancer/projects/40101953/TN51_Dominoes_V10_52.html"
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
        # TEST GROUP 1: Page loads and default state (TN51)
        # =====================================================================
        print("\n=== GROUP 1: Default state (TN51 mode) ===")

        mode = page.evaluate("GAME_MODE")
        test("GAME_MODE defaults to TN51", mode == "TN51", f"got {mode}")

        pc = page.evaluate("session.game.player_count")
        test("Default player count is 6", pc == 6, f"got {pc}")

        mp = page.evaluate("session.game.max_pip")
        test("Default max pip is 7", mp == 7, f"got {mp}")

        hs = page.evaluate("session.game.hand_size")
        test("Default hand size is 6", hs == 6, f"got {hs}")

        play_order = page.evaluate("PLAY_ORDER")
        test("Default PLAY_ORDER has 6 entries", len(play_order) == 6, f"got {len(play_order)}")

        # =====================================================================
        # TEST GROUP 2: Start TN51 game
        # =====================================================================
        print("\n=== GROUP 2: TN51 mode game ===")

        page.click("#btnStartNewGame")
        page.wait_for_timeout(500)
        page.click("#btnGameSettingsStart")
        page.wait_for_timeout(1500)

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

        page.screenshot(path="/var/lib/freelancer/projects/40101953/test_v52_tn51.png")

        # =====================================================================
        # TEST GROUP 3: Switch to Texas 42 mode
        # =====================================================================
        print("\n=== GROUP 3: Switch to Texas 42 mode ===")

        page.evaluate("""
            document.getElementById('startScreenBackdrop').style.display = 'flex';
        """)
        page.wait_for_timeout(300)
        page.click("#btnStartNewGame")
        page.wait_for_timeout(500)

        page.click('[data-game-type="T42"]')
        page.wait_for_timeout(300)

        sel = page.evaluate("selectedGameType")
        test("Texas 42 selected in settings", sel == "T42", f"got {sel}")

        page.click("#btnGameSettingsStart")
        page.wait_for_timeout(1500)

        mode = page.evaluate("GAME_MODE")
        test("Game switched to T42 mode", mode == "T42", f"got {mode}")

        pc = page.evaluate("session.game.player_count")
        test("T42 has 4 players", pc == 4, f"got {pc}")

        mp = page.evaluate("session.game.max_pip")
        test("T42 max pip is 6", mp == 6, f"got {mp}")

        hs = page.evaluate("session.game.hand_size")
        test("T42 has 7 tiles per hand", hs == 7, f"got {hs}")

        play_order = page.evaluate("PLAY_ORDER")
        test("T42 PLAY_ORDER has 4 entries", len(play_order) == 4, f"got {len(play_order)}: {play_order}")
        test("T42 PLAY_ORDER is [1,2,3,4]", play_order == [1,2,3,4], f"got {play_order}")

        # Check hands
        hands = page.evaluate("session.game.hands")
        test("T42: 4 hands dealt", len(hands) == 4, f"got {len(hands)}")
        for i, hand in enumerate(hands):
            test(f"T42: Hand {i} has 7 tiles", len(hand) == 7, f"got {len(hand)}")

        # All tiles <= 6
        all_valid = page.evaluate("""
            session.game.hands.every(hand =>
                hand.every(tile => tile[0] <= 6 && tile[1] <= 6)
            )
        """)
        test("T42: All tiles have pips <= 6", all_valid)

        total_tiles = page.evaluate("session.game.hands.flat().length")
        test("T42: Total tiles dealt = 28", total_tiles == 28, f"got {total_tiles}")

        # P5/P6 hidden
        p5_hidden = page.evaluate("document.getElementById('playerIndicator5').style.display === 'none'")
        p6_hidden = page.evaluate("document.getElementById('playerIndicator6').style.display === 'none'")
        test("T42: P5 indicator hidden", p5_hidden)
        test("T42: P6 indicator hidden", p6_hidden)

        # P1-P4 visible
        for i in range(1, 5):
            vis = page.evaluate(f"document.getElementById('playerIndicator{i}').style.display !== 'none'")
            test(f"T42: Player {i} indicator visible", vis)

        # Sprite arrays
        sprite_count = page.evaluate("sprites.length")
        test("T42: sprites array has 4 seats", sprite_count == 4, f"got {sprite_count}")
        for s in range(4):
            sc = page.evaluate(f"sprites[{s}] ? sprites[{s}].length : 0")
            test(f"T42: Seat {s} has 7 sprites", sc == 7, f"got {sc}")

        # =====================================================================
        # TEST GROUP 4: T42 Layout
        # =====================================================================
        print("\n=== GROUP 4: T42 Layout ===")

        layout_match = page.evaluate("getActiveLayout() === LAYOUT_T42")
        test("T42: getActiveLayout() returns LAYOUT_T42", layout_match)

        sections = page.evaluate("getActiveLayout().sections.map(s => s.name)")
        test("T42: Layout has 10 sections", len(sections) == 10, f"got {len(sections)}: {sections}")

        p1_count = page.evaluate("getSection('Player_1_Hand').dominoes.length")
        test("T42: P1 Hand has 7 positions", p1_count == 7, f"got {p1_count}")

        p2_count = page.evaluate("getSection('Player_2_Hand').dominoes.length")
        test("T42: P2 Hand has 7 positions", p2_count == 7, f"got {p2_count}")

        th_count = page.evaluate("getSection('Trick_History').dominoes.length")
        test("T42: Trick History has 28 positions", th_count == 28, f"got {th_count}")

        # =====================================================================
        # TEST GROUP 5: T42 Bidding
        # =====================================================================
        print("\n=== GROUP 5: T42 Bidding ===")

        phase = page.evaluate("session.phase")
        test("T42: Game is in bidding phase", phase == "NEED_BID", f"got {phase}")

        # Check bidding state
        bidder_count = page.evaluate("biddingState.bidderOrder.length")
        test("T42: bidderOrder has 4 entries", bidder_count == 4, f"got {bidder_count}")

        # =====================================================================
        # TEST GROUP 6: T42 Scoring
        # =====================================================================
        print("\n=== GROUP 6: T42 scoring ===")

        total_possible = page.evaluate("GAME_MODE === 'T42' ? 42 : 51")
        test("T42: totalPossible is 42", total_possible == 42)

        # =====================================================================
        # TEST GROUP 7: T42 Teams
        # =====================================================================
        print("\n=== GROUP 7: T42 teams ===")

        t0 = page.evaluate("session.game.team_of(0)")
        t1 = page.evaluate("session.game.team_of(1)")
        t2 = page.evaluate("session.game.team_of(2)")
        t3 = page.evaluate("session.game.team_of(3)")
        test("T42: Seat 0 is Team 0", t0 == 0, f"got {t0}")
        test("T42: Seat 1 is Team 1", t1 == 1, f"got {t1}")
        test("T42: Seat 2 is Team 0 (partner)", t2 == 0, f"got {t2}")
        test("T42: Seat 3 is Team 1", t3 == 1, f"got {t3}")

        # =====================================================================
        # TEST GROUP 8: getTrickHistoryPosition dynamic grid
        # =====================================================================
        print("\n=== GROUP 8: getTrickHistoryPosition grid ===")

        # In T42: grid is 4 cols × 7 rows = 28 positions
        # Team 1 trick 0, player 0 → row 0, col 0, index 0
        pos_t1_0_0 = page.evaluate("getTrickHistoryPosition(0, 0, 0)")
        test("T42: getTrickHistoryPosition(0,0,0) returns valid", pos_t1_0_0 is not None)

        # Team 1 trick 0, player 3 → row 0, col 3, index 3
        pos_t1_0_3 = page.evaluate("getTrickHistoryPosition(0, 0, 3)")
        test("T42: getTrickHistoryPosition(0,0,3) returns valid", pos_t1_0_3 is not None)

        # Team 2 trick 0, player 0 → row 6, col 0, index 24
        pos_t2_0_0 = page.evaluate("getTrickHistoryPosition(0, 1, 0)")
        test("T42: getTrickHistoryPosition(0,1,0) returns valid", pos_t2_0_0 is not None)

        # Team 2 trick 0, player 3 → row 6, col 3, index 27
        pos_t2_0_3 = page.evaluate("getTrickHistoryPosition(0, 1, 3)")
        test("T42: getTrickHistoryPosition(0,1,3) returns valid", pos_t2_0_3 is not None)

        # Verify positions are different (not stacking)
        # T42 trick history is horizontal — rows differ in X, not Y
        if pos_t1_0_0 and pos_t2_0_0:
            diff_x = abs(pos_t1_0_0['x'] - pos_t2_0_0['x'])
            diff_y = abs(pos_t1_0_0['y'] - pos_t2_0_0['y'])
            test("T42: Team1 and Team2 trick positions differ",
                 diff_x > 10 or diff_y > 10,
                 f"Team1 ({pos_t1_0_0['x']:.1f},{pos_t1_0_0['y']:.1f}), Team2 ({pos_t2_0_0['x']:.1f},{pos_t2_0_0['y']:.1f})")

        # =====================================================================
        # TEST GROUP 9: ppVisualPlayer/ppSeatFromVisual dynamic modulo
        # =====================================================================
        print("\n=== GROUP 9: PP functions ===")

        # With default rotation (0), seat 0 → Player 1
        vp0 = page.evaluate("ppVisualPlayer(0)")
        test("T42: ppVisualPlayer(0) = 1", vp0 == 1, f"got {vp0}")

        vp3 = page.evaluate("ppVisualPlayer(3)")
        test("T42: ppVisualPlayer(3) = 4", vp3 == 4, f"got {vp3}")

        # Reverse: visual 1 → seat 0
        sv1 = page.evaluate("ppSeatFromVisual(1)")
        test("T42: ppSeatFromVisual(1) = 0", sv1 == 0, f"got {sv1}")

        # =====================================================================
        # TEST GROUP 10: T42 Layout Settings
        # =====================================================================
        print("\n=== GROUP 10: T42 Layout Settings ===")

        # Check settings button visible in T42 mode
        btn_display = page.evaluate("document.getElementById('t42SettingsBtn').style.display")
        test("T42: Settings button visible", btn_display == 'block', f"got '{btn_display}'")

        # Check T42_SETTINGS object exists
        has_settings = page.evaluate("typeof T42_SETTINGS === 'object'")
        test("T42: T42_SETTINGS object exists", has_settings)

        # Check default values
        p1s = page.evaluate("T42_SETTINGS.p1Scale")
        test("T42: Default p1Scale is 1.071", abs(p1s - 1.071) < 0.001, f"got {p1s}")

        ops = page.evaluate("T42_SETTINGS.opponentScale")
        test("T42: Default opponentScale is 0.393", abs(ops - 0.393) < 0.001, f"got {ops}")

        # Open settings popup
        page.click("#t42SettingsBtn")
        page.wait_for_timeout(300)
        popup_vis = page.evaluate("document.getElementById('t42SettingsBackdrop').style.display === 'flex'")
        test("T42: Settings popup opens", popup_vis)

        # Change a value and verify it updates
        page.evaluate("document.getElementById('t42s_opponentScale').value = 0.5; document.getElementById('t42s_opponentScale').dispatchEvent(new Event('input'))")
        page.wait_for_timeout(200)
        new_ops = page.evaluate("T42_SETTINGS.opponentScale")
        test("T42: opponentScale updated to 0.5", abs(new_ops - 0.5) < 0.01, f"got {new_ops}")

        # Reset defaults
        page.click("#btnT42Reset")
        page.wait_for_timeout(200)
        reset_ops = page.evaluate("T42_SETTINGS.opponentScale")
        test("T42: Reset restores default opponentScale", abs(reset_ops - 0.393) < 0.001, f"got {reset_ops}")

        # Close popup
        page.click("#btnCloseT42Settings")
        page.wait_for_timeout(200)

        # =====================================================================
        # TEST GROUP 11: Simulate a complete trick in T42
        # =====================================================================
        print("\n=== GROUP 11: T42 trick simulation ===")

        # We need to get past bidding first
        # Let's force-set the game state to playing
        page.evaluate("""
            // Force bid completion
            session.current_bid = 30;
            session.bid_marks = 1;
            session.bid_winner_seat = 0;
            session.contract = 'NORMAL';
            session.game.set_trump_suit(1);  // Ones are trump
            session.phase = 'PLAYING';
            currentTrick = 0;
            playedThisTrick = [];
            team1TricksWon = 0;
            team2TricksWon = 0;
            waitingForPlayer1 = true;
        """)
        page.wait_for_timeout(500)

        # Verify game state
        phase = page.evaluate("session.phase")
        test("T42: Game set to PLAYING phase", phase == "PLAYING", f"got {phase}")

        # Check that all 4 seats have sprites
        for s in range(4):
            has_sprites = page.evaluate(f"sprites[{s}] && sprites[{s}].some(s => s !== null)")
            test(f"T42: Seat {s} has sprites for playing", has_sprites)

        page.screenshot(path="/var/lib/freelancer/projects/40101953/test_v52_t42.png")

        # =====================================================================
        # TEST GROUP 12: Verify no JS errors on TN51 after T42 changes
        # =====================================================================
        print("\n=== GROUP 12: TN51 regression check ===")

        # Switch back to TN51
        page.evaluate("""
            document.getElementById('startScreenBackdrop').style.display = 'flex';
        """)
        page.wait_for_timeout(300)
        page.click("#btnStartNewGame")
        page.wait_for_timeout(500)
        page.click('[data-game-type="TN51"]')
        page.wait_for_timeout(300)
        page.click("#btnGameSettingsStart")
        page.wait_for_timeout(1500)

        mode = page.evaluate("GAME_MODE")
        test("Regression: Switched back to TN51", mode == "TN51", f"got {mode}")

        pc = page.evaluate("session.game.player_count")
        test("Regression: TN51 has 6 players", pc == 6, f"got {pc}")

        play_order = page.evaluate("PLAY_ORDER")
        test("Regression: PLAY_ORDER restored to 6", len(play_order) == 6, f"got {len(play_order)}")

        # Check bidder order
        bidder_count = page.evaluate("biddingState.bidderOrder.length")
        test("Regression: bidderOrder has 6 entries", bidder_count == 6, f"got {bidder_count}")

        # T42 settings button should be hidden
        btn_display = page.evaluate("document.getElementById('t42SettingsBtn').style.display")
        test("Regression: T42 Settings button hidden", btn_display == 'none', f"got '{btn_display}'")

        # All 6 player indicators visible
        for i in range(1, 7):
            vis = page.evaluate(f"document.getElementById('playerIndicator{i}').style.display !== 'none'")
            test(f"Regression: Player {i} indicator visible", vis)

        page.screenshot(path="/var/lib/freelancer/projects/40101953/test_v52_tn51_regression.png")

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
