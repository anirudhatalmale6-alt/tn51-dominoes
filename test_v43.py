#!/usr/bin/env python3
"""Test V10_43: The REAL bug — start normal game, then enable PP with Continue Game.
Also test: new game PP works, and multiple configs."""
import asyncio
from playwright.async_api import async_playwright

HTML = "/var/lib/freelancer/projects/40101953/TN51_Dominoes_V10_43.html"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1024, "height": 768})

        errors = []
        page.on("pageerror", lambda err: errors.append(str(err)))
        logs = []
        page.on("console", lambda msg: logs.append(f"[{msg.type}] {msg.text}"))

        await page.goto(f"file://{HTML}")
        await page.wait_for_timeout(2000)

        # ═══════════════════════════════════════════════════════
        # TEST 1: Client's exact scenario — start normal game, then enable PP
        # ═══════════════════════════════════════════════════════
        print("=" * 60)
        print("TEST 1: Start normal game → Enable PP with Continue Game")
        print("=" * 60)

        # Start a normal game (no PP)
        print("\n  1a. Starting normal game...")
        await page.evaluate("""() => {
            hideStartScreen();
            clearSavedGame();
            PASS_AND_PLAY_MODE = false;
            ppHumanSeats = new Set();
            startNewHand();
        }""")
        await page.wait_for_timeout(2000)

        state1 = await page.evaluate("""() => ({
            ppMode: PASS_AND_PLAY_MODE,
            phase: session.phase,
            current: session.game.current_player
        })""")
        print(f"  Normal game state: {state1}")

        # Now open PP and click Continue Game (P1/P3/P5 human)
        print("\n  1b. Enabling PP with Continue Game (P1/P3/P5)...")
        await page.click('#settingsBtn')
        await page.wait_for_timeout(300)
        await page.click('#menuPassPlay')
        await page.wait_for_timeout(300)

        for seat in range(6):
            cb = await page.query_selector(f'#ppSeat{seat}')
            if cb:
                is_checked = await cb.is_checked()
                if seat in [0, 2, 4]:
                    if not is_checked: await cb.click()
                else:
                    if is_checked: await cb.click()

        priv = await page.query_selector('#ppPrivacy')
        if priv and await priv.is_checked():
            await priv.click()

        await page.wait_for_timeout(200)

        # Click Continue Game (not New Game)
        await page.click('#ppContinue')
        await page.wait_for_timeout(2000)

        state2 = await page.evaluate("""() => ({
            ppMode: PASS_AND_PLAY_MODE,
            humans: [...ppHumanSeats],
            phase: session.phase,
            current: session.game.current_player,
            activeView: ppActiveViewSeat,
            waiting: waitingForPlayer1
        })""")
        print(f"  After continue: {state2}")

        # Handle bidding
        print("\n  1c. Handling bidding...")
        for attempt in range(25):
            await page.wait_for_timeout(500)
            bs = await page.evaluate("""() => ({
                phase: session.phase,
                currentBidder: biddingState ? biddingState.currentBidder : -1,
                isHuman: biddingState ? ppIsHuman(biddingState.currentBidder) : false,
                highBid: biddingState ? biddingState.highBid : 0,
                bidVisible: document.getElementById('bidBackdrop').style.display,
                trumpVisible: document.getElementById('trumpBackdrop').style.display
            })""")

            if bs['phase'] == 'PLAYING':
                print(f"  → PLAYING phase reached!")
                break
            if bs['phase'] == 'NEED_TRUMP' and bs['trumpVisible'] == 'flex':
                await page.evaluate("""() => {
                    const seat = ppActiveViewSeat;
                    const hand = session.game.hands[seat] || [];
                    if (hand.length > 0) {
                        selectedTrump = Math.max(hand[0][0], hand[0][1]);
                        confirmTrumpSelection();
                    }
                }""")
                await page.wait_for_timeout(1000)
                continue

            if bs['phase'] == 'NEED_BID' and bs['bidVisible'] == 'flex' and bs['isHuman']:
                if bs['highBid'] == 0:
                    await page.evaluate("() => humanBid(34)")
                    print(f"  P{bs['currentBidder']+1} bids 34")
                else:
                    await page.evaluate("() => humanPass()")
                    print(f"  P{bs['currentBidder']+1} passes")
                await page.wait_for_timeout(300)

        # Wait for human turn
        await page.wait_for_timeout(2000)
        for i in range(10):
            st = await page.evaluate("""() => ({
                phase: session.phase, current: session.game.current_player,
                waiting: waitingForPlayer1, isAnimating: isAnimating,
                activeView: ppActiveViewSeat
            })""")
            if st['phase'] == 'PLAYING' and st['waiting'] and not st['isAnimating']:
                break
            await page.wait_for_timeout(1000)

        # Play multiple turns
        print("\n  1d. Playing turns...")

        async def human_play():
            return await page.evaluate("""() => {
                const seat = ppActiveViewSeat;
                const cp = session.game.current_player;
                if (seat !== cp) return { error: 'mismatch', view: seat, current: cp };
                if (!waitingForPlayer1) return { error: 'not waiting' };
                if (isAnimating) return { error: 'animating' };

                const legal = session.game.legal_indices_for_player(seat);
                if (legal.length === 0) return { error: 'no legal' };

                const tile = session.game.hands[seat][legal[0]];
                const ss = sprites[seat] || [];
                let si = -1;
                for (let i = 0; i < ss.length; i++) {
                    const d = ss[i];
                    if (!d || !d.tile) continue;
                    if ((d.tile[0] === tile[0] && d.tile[1] === tile[1]) ||
                        (d.tile[0] === tile[1] && d.tile[1] === tile[0])) { si = i; break; }
                }
                if (si < 0) return { error: 'no sprite' };

                const spriteEl = ss[si].sprite.el ? ss[si].sprite.el : ss[si].sprite;
                handlePlayer1Click(spriteEl);
                return { ok: true, seat: seat, tile: tile };
            }""")

        async def wait_for_human(max_s=15):
            last = {}
            for i in range(max_s):
                await page.wait_for_timeout(1000)
                last = await page.evaluate("""() => ({
                    current: session.game.current_player,
                    waiting: waitingForPlayer1,
                    isAnimating: isAnimating,
                    activeView: ppActiveViewSeat,
                    phase: session.phase
                })""")
                if last.get('phase') != 'PLAYING':
                    return {'ok': True, 'reason': 'hand_done', **last, 'waited': i + 1}
                if last.get('waiting') and not last.get('isAnimating'):
                    return {'ok': True, **last, 'waited': i + 1}
            return {'ok': False, 'reason': 'timeout', **last, 'waited': max_s}

        hangs = 0
        turns = 0
        for turn in range(1, 20):
            st = await page.evaluate("() => ({ phase: session.phase })")
            if st['phase'] != 'PLAYING':
                break
            play = await human_play()
            if 'error' in play:
                await page.wait_for_timeout(1000)
                play = await human_play()
                if 'error' in play:
                    print(f"  Turn {turn}: ERROR: {play}")
                    break
            turns += 1
            wait = await wait_for_human()
            if not wait['ok']:
                hangs += 1
                print(f"  Turn {turn}: ✗ HANG!")
                break
            else:
                print(f"  Turn {turn}: ✓ P{play.get('seat',0)+1} → P{wait['current']+1} ({wait['waited']}s)")

        r1 = "✓ PASS" if hangs == 0 and turns > 0 else "✗ FAIL"
        print(f"\n  TEST 1 RESULT: {r1} ({turns} turns, {hangs} hangs)")

        # ═══════════════════════════════════════════════════════
        # TEST 2: Same but with P2/P4/P6
        # ═══════════════════════════════════════════════════════
        print(f"\n{'='*60}")
        print("TEST 2: Normal game → PP Continue with P2/P4/P6")
        print("=" * 60)

        await page.goto(f"file://{HTML}")
        await page.wait_for_timeout(2000)

        # Start normal game
        await page.evaluate("""() => {
            hideStartScreen();
            clearSavedGame();
            PASS_AND_PLAY_MODE = false;
            ppHumanSeats = new Set();
            startNewHand();
        }""")
        await page.wait_for_timeout(2000)

        # Enable PP with P2/P4/P6, Continue Game
        await page.click('#settingsBtn')
        await page.wait_for_timeout(300)
        await page.click('#menuPassPlay')
        await page.wait_for_timeout(300)

        for seat in range(6):
            cb = await page.query_selector(f'#ppSeat{seat}')
            if cb:
                is_checked = await cb.is_checked()
                if seat in [1, 3, 5]:
                    if not is_checked: await cb.click()
                else:
                    if is_checked: await cb.click()

        priv = await page.query_selector('#ppPrivacy')
        if priv and await priv.is_checked():
            await priv.click()

        await page.wait_for_timeout(200)
        await page.click('#ppContinue')
        await page.wait_for_timeout(2000)

        # Handle bidding
        for attempt in range(25):
            await page.wait_for_timeout(500)
            bs = await page.evaluate("""() => ({
                phase: session.phase,
                currentBidder: biddingState ? biddingState.currentBidder : -1,
                isHuman: biddingState ? ppIsHuman(biddingState.currentBidder) : false,
                highBid: biddingState ? biddingState.highBid : 0,
                bidVisible: document.getElementById('bidBackdrop').style.display,
                trumpVisible: document.getElementById('trumpBackdrop').style.display
            })""")
            if bs['phase'] == 'PLAYING':
                break
            if bs['phase'] == 'NEED_TRUMP' and bs['trumpVisible'] == 'flex':
                await page.evaluate("""() => {
                    const seat = ppActiveViewSeat;
                    const hand = session.game.hands[seat] || [];
                    if (hand.length > 0) {
                        selectedTrump = Math.max(hand[0][0], hand[0][1]);
                        confirmTrumpSelection();
                    }
                }""")
                await page.wait_for_timeout(1000)
                continue
            if bs['phase'] == 'NEED_BID' and bs['bidVisible'] == 'flex' and bs['isHuman']:
                if bs['highBid'] == 0:
                    await page.evaluate("() => humanBid(34)")
                else:
                    await page.evaluate("() => humanPass()")
                await page.wait_for_timeout(300)

        await page.wait_for_timeout(2000)
        for i in range(10):
            st = await page.evaluate("""() => ({
                phase: session.phase, waiting: waitingForPlayer1, isAnimating: isAnimating
            })""")
            if st['phase'] == 'PLAYING' and st['waiting'] and not st['isAnimating']:
                break
            await page.wait_for_timeout(1000)

        hangs2 = 0
        turns2 = 0
        for turn in range(1, 20):
            st = await page.evaluate("() => ({ phase: session.phase })")
            if st['phase'] != 'PLAYING':
                break
            play = await human_play()
            if 'error' in play:
                await page.wait_for_timeout(1000)
                play = await human_play()
                if 'error' in play:
                    print(f"  Turn {turn}: ERROR: {play}")
                    break
            turns2 += 1
            wait = await wait_for_human()
            if not wait['ok']:
                hangs2 += 1
                print(f"  Turn {turn}: ✗ HANG!")
                break
            else:
                print(f"  Turn {turn}: ✓ P{play.get('seat',0)+1} → P{wait['current']+1} ({wait['waited']}s)")

        r2 = "✓ PASS" if hangs2 == 0 and turns2 > 0 else "✗ FAIL"
        print(f"\n  TEST 2 RESULT: {r2} ({turns2} turns, {hangs2} hangs)")

        # ═══════════════════════════════════════════════════════
        # TEST 3: PP New Game still works (regression check)
        # ═══════════════════════════════════════════════════════
        print(f"\n{'='*60}")
        print("TEST 3: PP New Game (regression check)")
        print("=" * 60)

        await page.goto(f"file://{HTML}")
        await page.wait_for_timeout(2000)

        await page.click('#settingsBtn')
        await page.wait_for_timeout(300)
        await page.click('#menuPassPlay')
        await page.wait_for_timeout(300)

        for seat in range(6):
            cb = await page.query_selector(f'#ppSeat{seat}')
            if cb:
                is_checked = await cb.is_checked()
                if seat in [0, 2, 4]:
                    if not is_checked: await cb.click()
                else:
                    if is_checked: await cb.click()

        priv = await page.query_selector('#ppPrivacy')
        if priv and await priv.is_checked():
            await priv.click()

        await page.click('#ppNewGame')
        await page.wait_for_timeout(3000)

        # Quick bid
        for attempt in range(25):
            await page.wait_for_timeout(500)
            bs = await page.evaluate("""() => ({
                phase: session.phase,
                bidVisible: document.getElementById('bidBackdrop').style.display,
                isHuman: biddingState ? ppIsHuman(biddingState.currentBidder) : false,
                highBid: biddingState ? biddingState.highBid : 0,
                trumpVisible: document.getElementById('trumpBackdrop').style.display
            })""")
            if bs['phase'] == 'PLAYING': break
            if bs['phase'] == 'NEED_TRUMP' and bs['trumpVisible'] == 'flex':
                await page.evaluate("""() => {
                    const seat = ppActiveViewSeat;
                    const hand = session.game.hands[seat] || [];
                    if (hand.length > 0) { selectedTrump = Math.max(hand[0][0], hand[0][1]); confirmTrumpSelection(); }
                }""")
                await page.wait_for_timeout(1000)
                continue
            if bs['phase'] == 'NEED_BID' and bs['bidVisible'] == 'flex' and bs['isHuman']:
                if bs['highBid'] == 0: await page.evaluate("() => humanBid(34)")
                else: await page.evaluate("() => humanPass()")
                await page.wait_for_timeout(300)

        await page.wait_for_timeout(2000)
        for i in range(10):
            st = await page.evaluate("() => ({ phase: session.phase, waiting: waitingForPlayer1, isAnimating: isAnimating })")
            if st['phase'] == 'PLAYING' and st['waiting'] and not st['isAnimating']: break
            await page.wait_for_timeout(1000)

        hangs3 = 0
        turns3 = 0
        for turn in range(1, 10):
            st = await page.evaluate("() => ({ phase: session.phase })")
            if st['phase'] != 'PLAYING': break
            play = await human_play()
            if 'error' in play:
                await page.wait_for_timeout(1000)
                play = await human_play()
                if 'error' in play: break
            turns3 += 1
            wait = await wait_for_human()
            if not wait['ok']:
                hangs3 += 1; break
            else:
                print(f"  Turn {turn}: ✓ P{play.get('seat',0)+1} → P{wait['current']+1}")

        r3 = "✓ PASS" if hangs3 == 0 and turns3 > 0 else "✗ FAIL"
        print(f"\n  TEST 3 RESULT: {r3} ({turns3} turns)")

        # ═══════════════════════════════════════════════════════
        # Summary
        # ═══════════════════════════════════════════════════════
        print(f"\n{'='*60}")
        print("RESULTS:")
        print(f"  TEST 1 (Normal→PP Continue P1/P3/P5): {r1}")
        print(f"  TEST 2 (Normal→PP Continue P2/P4/P6): {r2}")
        print(f"  TEST 3 (PP New Game P1/P3/P5):        {r3}")
        all_pass = all(r.startswith("✓") for r in [r1, r2, r3])
        print(f"\n{'ALL TESTS PASSED!' if all_pass else 'SOME TESTS FAILED!'}")
        print("=" * 60)

        if errors:
            print(f"\nJS ERRORS:")
            for e in errors[:5]:
                print(f"  ✗ {e[:150]}")

        await browser.close()

asyncio.run(main())
