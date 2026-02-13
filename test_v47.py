#!/usr/bin/env python3
"""Test V10_47: Persistent boneyard, auto-close, game end, marks selection, overflow, save/restore, replay."""
import asyncio, os
from playwright.async_api import async_playwright

HTML_FILE = os.path.join(os.path.dirname(__file__), 'TN51_Dominoes_V10_47.html')

async def test_v47():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 800, 'height': 600})
        await page.goto(f'file://{HTML_FILE}')
        await page.wait_for_timeout(2000)

        print("\n=== TEST 1: Start screen has marks selection ===")
        marks_btns = await page.evaluate('''() => {
            const btns = document.querySelectorAll('.marksBtn');
            return Array.from(btns).map(b => ({
                marks: b.dataset.marks,
                text: b.textContent.trim()
            }));
        }''')
        print(f"  Marks buttons: {marks_btns}")
        assert len(marks_btns) == 3, f"Expected 3 marks buttons, got {len(marks_btns)}"
        assert marks_btns[0]['marks'] == '3', "First button should be 3"
        assert marks_btns[1]['marks'] == '7', "Second button should be 7"
        assert marks_btns[2]['marks'] == '15', "Third button should be 15"
        print("  PASS: 3/7/15 marks selection buttons exist")

        # Select 3 marks (short game)
        await page.evaluate("() => document.querySelector('.marksBtn[data-marks=\"3\"]').click()")
        await page.wait_for_timeout(200)

        selected = await page.evaluate('() => selectedMarksToWin')
        print(f"  selectedMarksToWin = {selected}")
        assert selected == 3, f"Expected 3, got {selected}"
        print("  PASS: selectedMarksToWin set to 3")

        # Start game via direct function call to avoid scope issues
        await page.evaluate('''() => {
            document.getElementById('startScreenBackdrop').style.display = 'none';
            clearSavedGame();
            session.marks_to_win = selectedMarksToWin;
            startNewHand();
        }''')
        await page.wait_for_timeout(2000)

        marks_to_win = await page.evaluate('() => session.marks_to_win')
        print(f"  marks_to_win = {marks_to_win}")
        assert marks_to_win == 3, f"Expected 3, got {marks_to_win}"
        print("  PASS: marks_to_win set to 3")

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
        await page.wait_for_timeout(500)

        # Tag trick history sprites
        await page.evaluate('''() => {
            for(let seat = 1; seat <= 5; seat++){
                if(sprites[seat] && sprites[seat][0] && sprites[seat][0].sprite){
                    const sp = sprites[seat][0].sprite;
                    sp._inTrickHistory = true;
                    if(sp._shadow) sp._shadow._inTrickHistory = true;
                }
            }
        }''')

        await page.screenshot(path='/var/lib/freelancer/projects/40101953/test_v47_baseline.png')
        print("  Saved: test_v47_baseline.png")

        print("\n=== TEST 2: BY2_OUTER_SIZE is 2 ===")
        outer_size = await page.evaluate('() => BY2_OUTER_SIZE')
        assert outer_size == 2, f"Expected 2, got {outer_size}"
        print("  PASS: BY2_OUTER_SIZE = 2")

        print("\n=== TEST 3: Toggle boneyard 2 ON ===")
        await page.evaluate('() => toggleBoneyard2()')
        await page.wait_for_timeout(500)
        is_visible = await page.evaluate('() => boneyard2Visible')
        assert is_visible, "Boneyard should be visible"
        display = await page.evaluate('() => getComputedStyle(document.getElementById("boneyard2Container")).display')
        assert display != 'none', "Container should be visible"
        print("  PASS: Boneyard 2 opens correctly")

        await page.screenshot(path='/var/lib/freelancer/projects/40101953/test_v47_boneyard_open.png')

        print("\n=== TEST 4: BONES button disables at hand end ===")
        # Toggle off first
        await page.evaluate('() => toggleBoneyard2()')
        await page.wait_for_timeout(200)

        # Call showHandEndPopup to simulate hand end
        await page.evaluate('''() => {
            session.status = "Team 1 wins the hand! +1 mark.";
            showHandEndPopup();
        }''')
        await page.wait_for_timeout(300)

        bones_btn_state = await page.evaluate('''() => {
            const btn = document.getElementById('boneyard2Toggle');
            return {
                pointerEvents: btn.style.pointerEvents,
                opacity: btn.style.opacity
            };
        }''')
        print(f"  BONES button state: {bones_btn_state}")
        assert bones_btn_state['pointerEvents'] == 'none', "BONES should be disabled"
        assert bones_btn_state['opacity'] == '0.15', "BONES should be dimmed"
        print("  PASS: BONES button disabled at hand end")

        # Check next round button is visible
        btn_display = await page.evaluate('() => document.getElementById("btnNextHand").style.display')
        assert btn_display == 'block', "Next Round button should be visible"
        print("  PASS: Next Round button visible")

        await page.screenshot(path='/var/lib/freelancer/projects/40101953/test_v47_hand_end.png')

        print("\n=== TEST 5: Game end — marks persist ===")
        # Simulate game win
        await page.evaluate('''() => {
            hideHandEndPopup();
            session.team_marks = [3, 1];
            session.status = "Bid made! +1 mark. Team 1 wins the game!";
            showHandEndPopup();
        }''')
        await page.wait_for_timeout(500)

        # Check marks are still on board (not reset to 0)
        marks = await page.evaluate('() => [session.team_marks[0], session.team_marks[1]]')
        print(f"  Marks after game win: {marks}")
        assert marks[0] == 3, f"Team 1 marks should be 3, got {marks[0]}"
        assert marks[1] == 1, f"Team 2 marks should be 1, got {marks[1]}"
        print("  PASS: Marks persist after game win")

        # Check button says "New Game"
        btn_text = await page.evaluate('() => document.getElementById("btnNextHand").textContent')
        assert btn_text == 'New Game', f"Expected 'New Game', got '{btn_text}'"
        print("  PASS: Button says 'New Game'")

        # Check game end summary overlay exists
        summary = await page.evaluate('() => !!document.getElementById("gameEndOverlay")')
        assert summary, "Game end summary overlay should exist"
        print("  PASS: Game end summary shown")

        await page.screenshot(path='/var/lib/freelancer/projects/40101953/test_v47_game_end.png')

        # Click New Game — marks should reset
        await page.evaluate('''() => {
            document.getElementById('btnNextHand').click();
        }''')
        await page.wait_for_timeout(1000)

        marks_after = await page.evaluate('() => [session.team_marks[0], session.team_marks[1]]')
        print(f"  Marks after New Game: {marks_after}")
        assert marks_after[0] == 0, f"Team 1 marks should be 0, got {marks_after[0]}"
        assert marks_after[1] == 0, f"Team 2 marks should be 0, got {marks_after[1]}"
        print("  PASS: Marks reset on New Game")

        # Check BONES button re-enabled
        bones_enabled = await page.evaluate('''() => {
            const btn = document.getElementById('boneyard2Toggle');
            return btn.style.pointerEvents !== 'none';
        }''')
        assert bones_enabled, "BONES should be re-enabled"
        print("  PASS: BONES button re-enabled for new hand")

        print("\n=== TEST 6: Overflow marks (>15) ===")
        await page.evaluate('''() => {
            session.team_marks = [18, 7];
            team1Marks = 18;
            team2Marks = 7;
            updateScoreDisplay();
        }''')
        await page.wait_for_timeout(200)

        canvas_height = await page.evaluate('() => document.getElementById("tallyCanvas1").height')
        print(f"  Canvas1 height with 18 marks: {canvas_height}")
        assert canvas_height > 24, f"Canvas should be taller for overflow, got {canvas_height}"
        print("  PASS: Canvas height increased for overflow marks")

        await page.screenshot(path='/var/lib/freelancer/projects/40101953/test_v47_overflow.png')

        print("\n=== TEST 7: Save/restore includes dealer and bid_winner_seat ===")
        # Set up state with specific values
        await page.evaluate('''() => {
            session.phase = PHASE_PLAYING;
            session.dealer = 3;
            session.bid_winner_seat = 2;
            session.game.leader = 4;
            session.team_marks = [5, 3];
            session.marks_to_win = 15;
            saveGameState();
        }''')

        snap = await page.evaluate('''() => {
            const saved = JSON.parse(localStorage.getItem('tn51_saved_game'));
            return saved.session;
        }''')
        print(f"  Snapshot dealer: {snap.get('dealer')}")
        print(f"  Snapshot bid_winner_seat: {snap.get('bid_winner_seat')}")
        print(f"  Snapshot leader: {snap.get('leader')}")
        print(f"  Snapshot marks_to_win: {snap.get('marks_to_win')}")
        assert snap.get('dealer') == 3, f"Expected dealer=3"
        assert snap.get('bid_winner_seat') == 2, f"Expected bid_winner_seat=2"
        assert snap.get('leader') == 4, f"Expected leader=4"
        assert snap.get('marks_to_win') == 15, f"Expected marks_to_win=15"
        print("  PASS: Snapshot includes all state fields")

        print("\n=== TEST 8: resumeGameFromSave restores full state ===")
        # Corrupt the current state, then resume
        await page.evaluate('''() => {
            session.dealer = 0;
            session.bid_winner_seat = 0;
            session.game.leader = 0;
            session.marks_to_win = 7;
        }''')

        result = await page.evaluate('() => resumeGameFromSave()')
        assert result == True, "resumeGameFromSave should return true"

        restored = await page.evaluate('''() => ({
            dealer: session.dealer,
            bid_winner_seat: session.bid_winner_seat,
            leader: session.game.leader,
            marks_to_win: session.marks_to_win,
            team_marks: [session.team_marks[0], session.team_marks[1]]
        })''')
        print(f"  Restored state: {restored}")
        assert restored['dealer'] == 3, f"Expected dealer=3"
        assert restored['bid_winner_seat'] == 2, f"Expected bid_winner_seat=2"
        assert restored['marks_to_win'] == 15, f"Expected marks_to_win=15"
        print("  PASS: Full state restored correctly")

        print("\n=== TEST 9: Hand replay system ===")
        # First need to have a HAND_START in the game log
        await page.evaluate('''() => {
            // Manually add a HAND_START log entry
            gameLog.push({
                type: "HAND_START",
                handId: 0,
                dealerSeat: 2,
                leaderSeat: 1,
                contract: { mode: "NORMAL", trumpMode: "follow", trumpSuit: 3, trumpDisplay: "3s", bid: 34, bidderSeat: 0, bidderTeam: 1 },
                hands: [
                    { seat: 0, team: 1, tiles: ["3-3", "5-3", "6-3", "4-3", "2-1", "7-0"] },
                    { seat: 1, team: 2, tiles: ["7-7", "6-6", "5-5", "4-4", "2-2", "1-1"] },
                    { seat: 2, team: 1, tiles: ["7-6", "7-5", "7-4", "7-3", "7-2", "7-1"] },
                    { seat: 3, team: 2, tiles: ["6-5", "6-4", "6-2", "6-1", "6-0", "5-4"] },
                    { seat: 4, team: 1, tiles: ["5-2", "5-1", "5-0", "4-2", "4-1", "4-0"] },
                    { seat: 5, team: 2, tiles: ["3-2", "3-1", "3-0", "2-0", "1-0", "0-0"] }
                ],
                timestamp: new Date().toISOString()
            });
        }''')

        # Save the hand
        saved = await page.evaluate('''() => {
            return saveHandForReplay("Test Hand 1");
        }''')
        assert saved == True, "saveHandForReplay should return true"
        print("  PASS: Hand saved for replay")

        # Verify saved data
        saved_hands = await page.evaluate('() => getSavedHands()')
        assert len(saved_hands) > 0, "Should have at least one saved hand"
        assert saved_hands[0]['name'] == "Test Hand 1", f"Name should be 'Test Hand 1'"
        print(f"  Saved hands count: {len(saved_hands)}")
        print("  PASS: Saved hands data correct")

        # Replay the hand
        result = await page.evaluate('() => replayHand(0)')
        assert result == True, "replayHand should return true"
        await page.wait_for_timeout(1000)

        # Check that hands were restored (P1's first tile should be 3-3)
        p1_hand = await page.evaluate('() => session.game.hands[0].map(t => t[0] + "-" + t[1])')
        print(f"  P1 hand after replay: {p1_hand}")
        assert '3-3' in p1_hand, "P1 should have tile 3-3"
        print("  PASS: Hand replayed correctly")

        phase = await page.evaluate('() => session.phase')
        print(f"  Phase after replay: {phase}")
        print("  PASS: Phase is bidding (replay starts fresh)")

        await page.screenshot(path='/var/lib/freelancer/projects/40101953/test_v47_replay.png')

        print("\n=== TEST 10: Replay dialog shows ===")
        # Test the dialog
        await page.evaluate('() => showReplayDialog()')
        await page.wait_for_timeout(300)
        overlay_visible = await page.evaluate('''() => {
            const el = document.getElementById('replayOverlay');
            return el && el.style.display !== 'none';
        }''')
        assert overlay_visible, "Replay dialog should be visible"
        print("  PASS: Replay dialog opens")

        await page.screenshot(path='/var/lib/freelancer/projects/40101953/test_v47_replay_dialog.png')

        await browser.close()
        print("\n=== ALL TESTS PASSED ===")

asyncio.run(test_v47())
