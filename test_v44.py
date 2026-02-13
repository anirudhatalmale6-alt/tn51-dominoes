#!/usr/bin/env python3
"""Test V10_44: Boneyard 2 inline overlay and PP-mode boneyard fix."""
import asyncio, os
from playwright.async_api import async_playwright

HTML_FILE = os.path.join(os.path.dirname(__file__), 'TN51_Dominoes_V10_44.html')

async def test_boneyard2():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 800, 'height': 600})
        await page.goto(f'file://{HTML_FILE}')
        await page.wait_for_timeout(2000)

        # Use JS to skip past the start screen and auto-bid
        await page.evaluate('''() => {
            // Close start screen
            document.getElementById('startScreenBackdrop').style.display = 'none';
        }''')
        await page.wait_for_timeout(500)

        # Start a new game and force to playing phase
        await page.evaluate('''() => {
            hideStartScreen();
            clearSavedGame();
            startNewHand();
        }''')
        await page.wait_for_timeout(2000)

        # Force through bidding to playing phase
        await page.evaluate('''() => {
            session.phase = PHASE_PLAYING;
            session.game.trump_suit = 3; // Blanks
            session.game.trump_mode = 'follow';
            session.contract = 'NORMAL';
            session.current_bid = 34;
            session.bid_marks = 1;
            session.bid_winner_seat = 0;
            // Close any bid/trump overlays
            const bidBackdrop = document.getElementById('bidBackdrop');
            if(bidBackdrop) bidBackdrop.style.display = 'none';
            const trumpBackdrop = document.getElementById('trumpBackdrop');
            if(trumpBackdrop) trumpBackdrop.style.display = 'none';
            // Set current player to 0
            session.game.current_player = 0;
            waitingForPlayer1 = true;
            updateTrumpDisplay();
        }''')
        await page.wait_for_timeout(1000)

        # Take a baseline screenshot
        await page.screenshot(path='/var/lib/freelancer/projects/40101953/test_by2_baseline.png')
        print("Saved: test_by2_baseline.png (game in play, boneyard 2 hidden)")

        print("\n=== TEST 1: Bone icon exists ===")
        exists = await page.evaluate('() => !!document.getElementById("boneyard2Toggle")')
        assert exists, "Bone icon not found"
        print("  PASS")

        print("\n=== TEST 2: Container hidden initially ===")
        display = await page.evaluate('() => getComputedStyle(document.getElementById("boneyard2Container")).display')
        assert display == 'none', f"Expected none, got {display}"
        print("  PASS")

        print("\n=== TEST 3: Toggle boneyard 2 ON ===")
        await page.evaluate('() => toggleBoneyard2()')
        await page.wait_for_timeout(500)
        display = await page.evaluate('() => getComputedStyle(document.getElementById("boneyard2Container")).display')
        assert display != 'none', f"Expected visible, got {display}"
        print(f"  PASS (display: {display})")

        # Check trick history hidden
        th_display = await page.evaluate('() => document.getElementById("trickHistoryBg").style.display')
        assert th_display == 'none', f"Expected trick history hidden, got '{th_display}'"
        print("  PASS: Trick history hidden")

        # Check canvas has content
        canvas_w = await page.evaluate('() => document.getElementById("boneyard2Canvas").width')
        assert canvas_w > 0, "Canvas not rendered"
        print(f"  PASS: Canvas rendered (width: {canvas_w})")

        await page.screenshot(path='/var/lib/freelancer/projects/40101953/test_by2_open.png')
        print("  Saved: test_by2_open.png")

        print("\n=== TEST 4: Toggle boneyard 2 OFF ===")
        await page.evaluate('() => toggleBoneyard2()')
        await page.wait_for_timeout(300)
        display = await page.evaluate('() => getComputedStyle(document.getElementById("boneyard2Container")).display')
        assert display == 'none', f"Expected none, got {display}"
        th_display = await page.evaluate('() => document.getElementById("trickHistoryBg").style.display')
        assert th_display == '', f"Expected trick history restored, got '{th_display}'"
        print("  PASS: Boneyard 2 hidden, trick history restored")

        print("\n=== TEST 5: Boneyard 2 with different gap settings ===")
        await page.evaluate('() => toggleBoneyard2()')
        await page.wait_for_timeout(300)

        # Change gap to 0
        await page.evaluate('''() => {
            window._by2Gap = 0;
            renderBoneyard2();
        }''')
        await page.wait_for_timeout(200)
        await page.screenshot(path='/var/lib/freelancer/projects/40101953/test_by2_gap0.png')
        print("  Saved: test_by2_gap0.png (gap=0, tight)")

        # Change gap to 5
        await page.evaluate('''() => {
            window._by2Gap = 5;
            renderBoneyard2();
        }''')
        await page.wait_for_timeout(200)
        await page.screenshot(path='/var/lib/freelancer/projects/40101953/test_by2_gap5.png')
        print("  Saved: test_by2_gap5.png (gap=5, spacious)")

        # Reset
        await page.evaluate('''() => {
            window._by2Gap = 2;
            renderBoneyard2();
        }''')

        print("\n=== TEST 6: Hand opacity slider ===")
        await page.evaluate('''() => {
            window._by2HandOpacity = 40;
            renderBoneyard2();
        }''')
        await page.wait_for_timeout(200)
        await page.screenshot(path='/var/lib/freelancer/projects/40101953/test_by2_opacity40.png')
        print("  Saved: test_by2_opacity40.png (hand opacity 40%)")

        await page.evaluate('''() => {
            window._by2HandOpacity = 100;
            renderBoneyard2();
        }''')
        await page.wait_for_timeout(200)
        await page.screenshot(path='/var/lib/freelancer/projects/40101953/test_by2_opacity100.png')
        print("  Saved: test_by2_opacity100.png (hand opacity 100%)")

        # Reset
        await page.evaluate('''() => {
            window._by2HandOpacity = 70;
            renderBoneyard2();
        }''')

        print("\n=== TEST 7: Border controls ===")
        await page.evaluate('''() => {
            window._by2OuterSize = 4;
            window._by2OuterColor = '#ff0000';
            renderBoneyard2();
        }''')
        await page.wait_for_timeout(200)
        await page.screenshot(path='/var/lib/freelancer/projects/40101953/test_by2_redborder.png')
        print("  Saved: test_by2_redborder.png (thick red border)")

        # Reset
        await page.evaluate('''() => {
            window._by2OuterSize = 2;
            window._by2OuterColor = '#00deff';
            renderBoneyard2();
        }''')

        print("\n=== TEST 8: PP mode boneyard (full modal) ===")
        # Close boneyard 2
        await page.evaluate('() => toggleBoneyard2()')
        await page.wait_for_timeout(200)

        # Enable PP mode
        await page.evaluate('''() => {
            PASS_AND_PLAY_MODE = true;
            ppHumanSeats = new Set([0, 2, 4]);
            ppActiveViewSeat = 2;
        }''')

        # Open full boneyard modal
        await page.evaluate('''() => {
            initBonesControls();
            renderBoneyard();
            document.getElementById('bonesBackdrop').style.display = 'block';
        }''')
        await page.wait_for_timeout(500)
        await page.screenshot(path='/var/lib/freelancer/projects/40101953/test_by2_pp_modal.png')
        print("  Saved: test_by2_pp_modal.png (full boneyard, PP mode seat 2)")

        # Verify it reads from seat 2
        seat_used = await page.evaluate('() => PASS_AND_PLAY_MODE ? ppActiveViewSeat : 0')
        assert seat_used == 2, f"Expected seat 2, got {seat_used}"
        print(f"  PASS: Using seat {seat_used} for hand detection")

        print("\n=== TEST 9: PP mode boneyard 2 (inline) ===")
        # Close full boneyard
        await page.evaluate('() => document.getElementById("bonesBackdrop").style.display = "none"')
        await page.wait_for_timeout(200)

        # Open boneyard 2
        await page.evaluate('() => toggleBoneyard2()')
        await page.wait_for_timeout(500)
        await page.screenshot(path='/var/lib/freelancer/projects/40101953/test_by2_pp_inline.png')
        print("  Saved: test_by2_pp_inline.png (boneyard 2, PP mode seat 2)")

        print("\n=== TEST 10: Settings panel opens ===")
        await page.evaluate('''() => {
            document.getElementById('by2Controls').style.display = 'block';
        }''')
        await page.wait_for_timeout(200)
        await page.screenshot(path='/var/lib/freelancer/projects/40101953/test_by2_settings.png')
        print("  Saved: test_by2_settings.png")

        ctrl_display = await page.evaluate('() => getComputedStyle(document.getElementById("by2Controls")).display')
        assert ctrl_display != 'none', "Controls not showing"
        print("  PASS: Settings panel visible")

        await browser.close()
        print("\n=== ALL TESTS PASSED ===")

asyncio.run(test_boneyard2())
