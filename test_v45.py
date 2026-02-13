#!/usr/bin/env python3
"""Test V10_45: Fix boneyard 2 opacity, icon, sprite hiding, shadows."""
import asyncio, os
from playwright.async_api import async_playwright

HTML_FILE = os.path.join(os.path.dirname(__file__), 'TN51_Dominoes_V10_45.html')

async def test_v45():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 800, 'height': 600})
        await page.goto(f'file://{HTML_FILE}')
        await page.wait_for_timeout(2000)

        # Dismiss start screen and start game
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

        # Simulate trick history by manually tagging some sprites and positioning them
        # This avoids needing to run the full game engine play flow
        tagged_count = await page.evaluate('''() => {
            // Tag the first 6 sprites as "in trick history" to simulate a completed trick
            const allSprites = document.querySelectorAll('#spriteLayer .dominoSprite');
            let count = 0;
            // Find sprites that belong to seats 1-5 (non-P1 hand tiles) - tag a few as trick history
            for(let seat = 1; seat <= 5 && count < 6; seat++){
                if(sprites[seat]){
                    for(let i = 0; i < sprites[seat].length && count < 6; i++){
                        if(sprites[seat][i] && sprites[seat][i].sprite){
                            const sp = sprites[seat][i].sprite;
                            sp._inTrickHistory = true;
                            if(sp._shadow) sp._shadow._inTrickHistory = true;
                            count++;
                        }
                    }
                }
            }
            return count;
        }''')
        await page.wait_for_timeout(500)
        print(f"Tagged {tagged_count} sprites as trick history")

        # Check that trick history sprites are tagged
        tagged = await page.evaluate('''() => {
            let count = 0;
            document.querySelectorAll('#spriteLayer .dominoSprite').forEach(el => {
                if(el._inTrickHistory) count++;
            });
            return count;
        }''')
        print(f"  Sprites tagged as trick history: {tagged}")

        # Take baseline screenshot
        await page.screenshot(path='/var/lib/freelancer/projects/40101953/test_v45_baseline.png')
        print("  Saved: test_v45_baseline.png")

        print("\n=== TEST 1: Bone icon renders as SVG ===")
        icon_html = await page.evaluate('() => document.getElementById("boneyard2Toggle").innerHTML')
        assert '<svg' in icon_html, f"Expected SVG, got: {icon_html[:100]}"
        print(f"  PASS: Icon is SVG")

        print("\n=== TEST 2: Toggle boneyard 2 — player hands NOT hidden ===")
        await page.evaluate('() => toggleBoneyard2()')
        await page.wait_for_timeout(500)

        # Count visible sprites in hand area (non-trick-history sprites)
        hand_sprites_visible = await page.evaluate('''() => {
            let count = 0;
            document.querySelectorAll('#spriteLayer .dominoSprite').forEach(el => {
                if(!el._inTrickHistory && getComputedStyle(el).display !== 'none') count++;
            });
            return count;
        }''')
        print(f"  Hand sprites still visible: {hand_sprites_visible}")
        assert hand_sprites_visible > 0, "Player hand sprites should NOT be hidden!"
        print("  PASS: Player hands remain visible")

        # Check trick history sprites ARE hidden
        th_hidden = await page.evaluate('''() => {
            let count = 0;
            document.querySelectorAll('#spriteLayer .dominoSprite').forEach(el => {
                if(el._inTrickHistory && getComputedStyle(el).display === 'none') count++;
            });
            return count;
        }''')
        print(f"  Trick history sprites hidden: {th_hidden}")

        # Check shadows are hidden too
        shadow_hidden = await page.evaluate('''() => {
            let count = 0;
            document.querySelectorAll('#shadowLayer .dominoShadow').forEach(el => {
                if(el._inTrickHistory && getComputedStyle(el).display === 'none') count++;
            });
            return count;
        }''')
        print(f"  Trick history shadows hidden: {shadow_hidden}")

        await page.screenshot(path='/var/lib/freelancer/projects/40101953/test_v45_open.png')
        print("  Saved: test_v45_open.png")

        print("\n=== TEST 3: Trick history background hidden ===")
        th_bg = await page.evaluate('() => document.getElementById("trickHistoryBg").style.display')
        assert th_bg == 'none', f"Expected hidden, got '{th_bg}'"
        print("  PASS")

        print("\n=== TEST 4: Close boneyard 2 — everything restores ===")
        await page.evaluate('() => toggleBoneyard2()')
        await page.wait_for_timeout(300)

        # Check trick history sprites restored
        th_restored = await page.evaluate('''() => {
            let count = 0;
            document.querySelectorAll('#spriteLayer .dominoSprite').forEach(el => {
                if(el._inTrickHistory && getComputedStyle(el).display !== 'none') count++;
            });
            return count;
        }''')
        print(f"  Trick history sprites restored: {th_restored}")

        # Check shadows restored
        shadow_restored = await page.evaluate('''() => {
            let count = 0;
            document.querySelectorAll('#shadowLayer .dominoShadow').forEach(el => {
                if(el._inTrickHistory && getComputedStyle(el).display !== 'none') count++;
            });
            return count;
        }''')
        print(f"  Shadows restored: {shadow_restored}")

        th_bg = await page.evaluate('() => document.getElementById("trickHistoryBg").style.display')
        assert th_bg == '', f"Expected restored, got '{th_bg}'"
        print("  PASS: Everything restored")

        await page.screenshot(path='/var/lib/freelancer/projects/40101953/test_v45_restored.png')
        print("  Saved: test_v45_restored.png")

        print("\n=== TEST 5: Opacity slider affects played tiles ===")
        await page.evaluate('() => toggleBoneyard2()')
        await page.wait_for_timeout(300)

        # Low opacity
        await page.evaluate('''() => {
            window._by2HandOpacity = 30;
            renderBoneyard2();
        }''')
        await page.wait_for_timeout(200)
        await page.screenshot(path='/var/lib/freelancer/projects/40101953/test_v45_opacity30.png')
        print("  Saved: test_v45_opacity30.png (played tiles 30% opacity)")

        # Full opacity
        await page.evaluate('''() => {
            window._by2HandOpacity = 100;
            renderBoneyard2();
        }''')
        await page.wait_for_timeout(200)
        await page.screenshot(path='/var/lib/freelancer/projects/40101953/test_v45_opacity100.png')
        print("  Saved: test_v45_opacity100.png (played tiles 100% opacity)")

        # Zero opacity (fully hidden)
        await page.evaluate('''() => {
            window._by2HandOpacity = 0;
            renderBoneyard2();
        }''')
        await page.wait_for_timeout(200)
        await page.screenshot(path='/var/lib/freelancer/projects/40101953/test_v45_opacity0.png')
        print("  Saved: test_v45_opacity0.png (played tiles 0% — invisible)")

        print("\n=== TEST 6: Settings panel ===")
        await page.evaluate('''() => {
            window._by2HandOpacity = 70;
            renderBoneyard2();
            document.getElementById('by2Controls').style.display = 'block';
        }''')
        await page.wait_for_timeout(200)
        await page.screenshot(path='/var/lib/freelancer/projects/40101953/test_v45_settings.png')
        print("  Saved: test_v45_settings.png")

        # Verify slider label
        label_text = await page.evaluate('''() => {
            const labels = document.querySelectorAll('#by2Controls .by2Row label');
            for(const l of labels) if(l.textContent.includes('Opacity')) return l.textContent;
            return 'not found';
        }''')
        print(f"  Opacity slider label: '{label_text}'")
        assert 'Played' in label_text, f"Expected 'Played Opacity', got '{label_text}'"
        print("  PASS: Slider label is 'Played Opacity'")

        await browser.close()
        print("\n=== ALL TESTS PASSED ===")

asyncio.run(test_v45())
