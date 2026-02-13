#!/usr/bin/env python3
"""Test V10_46: Hardcoded settings, BONES text toggle on right, no settings panel."""
import asyncio, os
from playwright.async_api import async_playwright

HTML_FILE = os.path.join(os.path.dirname(__file__), 'TN51_Dominoes_V10_46.html')

async def test_v46():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 800, 'height': 600})
        await page.goto(f'file://{HTML_FILE}')
        await page.wait_for_timeout(2000)

        # Start game
        await page.evaluate('''() => {
            document.getElementById('startScreenBackdrop').style.display = 'none';
            hideStartScreen();
            clearSavedGame();
            startNewHand();
        }''')
        await page.wait_for_timeout(2000)

        # Force to playing phase
        await page.evaluate('''() => {
            session.phase = PHASE_PLAYING;
            session.game.trump_suit = 3;
            session.game.trump_mode = 'follow';
            session.contract = 'NORMAL';
            session.current_bid = 34;
            session.bid_marks = 1;
            session.bid_winner_seat = 0;
            const bidBackdrop = document.getElementById('bidBackdrop');
            if(bidBackdrop) bidBackdrop.style.display = 'none';
            const trumpBackdrop = document.getElementById('trumpBackdrop');
            if(trumpBackdrop) trumpBackdrop.style.display = 'none';
            session.game.current_player = 0;
            waitingForPlayer1 = true;
            updateTrumpDisplay();
        }''')
        await page.wait_for_timeout(1000)

        # Tag some sprites as trick history for testing
        await page.evaluate('''() => {
            for(let seat = 1; seat <= 5; seat++){
                if(sprites[seat] && sprites[seat][0] && sprites[seat][0].sprite){
                    const sp = sprites[seat][0].sprite;
                    sp._inTrickHistory = true;
                    if(sp._shadow) sp._shadow._inTrickHistory = true;
                }
            }
        }''')

        # Screenshot baseline
        await page.screenshot(path='/var/lib/freelancer/projects/40101953/test_v46_baseline.png')
        print("Saved: test_v46_baseline.png")

        print("\n=== TEST 1: BONES toggle on right side ===")
        toggle = await page.evaluate('''() => {
            const el = document.getElementById('boneyard2Toggle');
            const rect = el.getBoundingClientRect();
            const tableRect = document.getElementById('tableMain').getBoundingClientRect();
            return {
                right: rect.right,
                tableRight: tableRect.right,
                innerHTML: el.innerHTML.substring(0, 100),
                visible: getComputedStyle(el).display !== 'none'
            };
        }''')
        print(f"  Toggle right edge: {toggle['right']:.0f}px (table right: {toggle['tableRight']:.0f}px)")
        print(f"  HTML: {toggle['innerHTML']}")
        assert toggle['visible'], "Toggle not visible"
        assert 'BONES' in toggle['innerHTML'], "Missing BONES text"
        assert 'by2Arrow' in toggle['innerHTML'], "Missing arrow"
        # Check it's on the right side (within 20% of right edge)
        assert toggle['right'] > toggle['tableRight'] * 0.9, f"Toggle not on right side"
        print("  PASS: BONES text + arrow on right side")

        print("\n=== TEST 2: No settings panel exists ===")
        settings_exists = await page.evaluate('() => !!document.getElementById("by2Controls")')
        assert not settings_exists, "Settings panel should be removed"
        settings_btn = await page.evaluate('() => !!document.getElementById("by2SettingsBtn")')
        assert not settings_btn, "Settings button should be removed"
        print("  PASS: Settings panel and button removed")

        print("\n=== TEST 3: Toggle boneyard 2 ON ===")
        await page.evaluate('() => toggleBoneyard2()')
        await page.wait_for_timeout(500)

        display = await page.evaluate('() => getComputedStyle(document.getElementById("boneyard2Container")).display')
        assert display != 'none', f"Expected visible, got {display}"
        print(f"  PASS: Boneyard 2 visible (display: {display})")

        # Check active class on toggle
        has_active = await page.evaluate('() => document.getElementById("boneyard2Toggle").classList.contains("active")')
        assert has_active, "Toggle should have 'active' class"
        print("  PASS: Toggle has active class")

        await page.screenshot(path='/var/lib/freelancer/projects/40101953/test_v46_open.png')
        print("  Saved: test_v46_open.png")

        print("\n=== TEST 4: Hardcoded settings applied ===")
        # Verify constants exist
        constants = await page.evaluate('''() => ({
            gap: BY2_GAP,
            innerSize: BY2_INNER_SIZE,
            innerRadius: BY2_INNER_RADIUS,
            outerSize: BY2_OUTER_SIZE,
            outerRadius: BY2_OUTER_RADIUS,
            innerColor: BY2_INNER_COLOR,
            outerColor: BY2_OUTER_COLOR,
            playedOpacity: BY2_PLAYED_OPACITY
        })''')
        assert constants['gap'] == 0, f"Gap should be 0, got {constants['gap']}"
        assert constants['innerSize'] == 1, f"Inner size should be 1"
        assert constants['innerRadius'] == 5, f"Inner radius should be 5"
        assert constants['outerSize'] == 6, f"Outer size should be 6"
        assert constants['outerRadius'] == 8, f"Outer radius should be 8"
        assert constants['innerColor'] == '#beb6ab', f"Inner color wrong"
        assert constants['outerColor'] == '#00deff', f"Outer color wrong"
        assert abs(constants['playedOpacity'] - 0.71) < 0.01, f"Played opacity should be 0.71"
        print(f"  PASS: All hardcoded settings correct: {constants}")

        print("\n=== TEST 5: Toggle OFF restores everything ===")
        await page.evaluate('() => toggleBoneyard2()')
        await page.wait_for_timeout(300)

        display = await page.evaluate('() => getComputedStyle(document.getElementById("boneyard2Container")).display')
        assert display == 'none', f"Expected hidden, got {display}"
        th_display = await page.evaluate('() => document.getElementById("trickHistoryBg").style.display')
        assert th_display == '', f"Expected trick history restored"
        print("  PASS: Everything restored")

        await page.screenshot(path='/var/lib/freelancer/projects/40101953/test_v46_closed.png')
        print("  Saved: test_v46_closed.png")

        print("\n=== TEST 6: Player hands remain visible when boneyard open ===")
        await page.evaluate('() => toggleBoneyard2()')
        await page.wait_for_timeout(300)

        hand_visible = await page.evaluate('''() => {
            let count = 0;
            document.querySelectorAll('#spriteLayer .dominoSprite').forEach(el => {
                if(!el._inTrickHistory && getComputedStyle(el).display !== 'none') count++;
            });
            return count;
        }''')
        print(f"  Hand sprites visible: {hand_visible}")
        assert hand_visible > 0, "Player hands should remain visible"
        print("  PASS")

        await browser.close()
        print("\n=== ALL TESTS PASSED ===")

asyncio.run(test_v46())
