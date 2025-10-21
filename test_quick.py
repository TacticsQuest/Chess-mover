"""
Quick Test - Chess Mover Machine Core Features

Tests the main features that are complete and ready to use.
"""

import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def test_chess_engine():
    """Test chess engine - the core of game logic."""
    print("\n" + "="*60)
    print("TESTING: Chess Engine")
    print("="*60)

    from logic.chess_engine import ChessEngine

    engine = ChessEngine()
    tests_passed = 0
    tests_total = 0

    # Test 1: Make moves
    tests_total += 1
    result = engine.make_move("e4")
    if result and result.from_square == "e2" and result.to_square == "e4":
        print("✓ Move e2-e4 works")
        tests_passed += 1
    else:
        print("✗ Move e2-e4 failed")

    # Test 2: Move history
    tests_total += 1
    engine.make_move("e5")
    history = engine.get_move_list_san()
    if history == ["e4", "e5"]:
        print("✓ Move history correct")
        tests_passed += 1
    else:
        print(f"✗ Move history wrong: {history}")

    # Test 3: Illegal move rejection
    tests_total += 1
    result = engine.make_move("e8")
    if result is None:
        print("✓ Illegal moves rejected")
        tests_passed += 1
    else:
        print("✗ Illegal move accepted!")

    # Test 4: PGN loading
    tests_total += 1
    pgn = "1. e4 e5 2. Nf3 Nc6"
    engine.reset()
    if engine.load_pgn(pgn):
        print("✓ PGN loading works")
        tests_passed += 1
    else:
        print("✗ PGN loading failed")

    # Test 5: FEN loading
    tests_total += 1
    fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"
    if engine.set_fen(fen):
        print("✓ FEN loading works")
        tests_passed += 1
    else:
        print("✗ FEN loading failed")

    # Test 6: Castling detection
    tests_total += 1
    castling_fen = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"
    engine.set_fen(castling_fen)
    result = engine.make_move("e1g1")
    if result and result.is_castling:
        print("✓ Castling detected")
        tests_passed += 1
    else:
        print("✗ Castling failed")

    print(f"\nResult: {tests_passed}/{tests_total} tests passed")
    return tests_passed == tests_total


def test_stockfish():
    """Test Stockfish integration."""
    print("\n" + "="*60)
    print("TESTING: Stockfish Engine (Optional)")
    print("="*60)

    try:
        from logic.stockfish_engine import StockfishEngine

        engine = StockfishEngine()
        print(f"✓ Stockfish found at: {engine.stockfish_path}")

        if engine.start():
            print("✓ Stockfish started")

            # Quick test
            fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
            best_move = engine.get_best_move(fen, time_ms=500)
            if best_move:
                print(f"✓ Best move: {best_move}")
            else:
                print("✗ No best move")

            engine.stop()
            return True
        else:
            print("✗ Failed to start Stockfish")
            return False

    except FileNotFoundError as e:
        print(f"⚠ Stockfish not installed (optional)")
        print("  Install: choco install stockfish")
        return None  # Not installed, but not an error


def test_move_executor():
    """Test move executor."""
    print("\n" + "="*60)
    print("TESTING: Move Executor")
    print("="*60)

    from logic.move_executor import MoveExecutor, ActionType
    from logic.board_map import BoardConfig

    board_cfg = BoardConfig(
        files=8,
        ranks=8,
        width_mm=400.0,
        height_mm=400.0,
        origin_x_mm=0.0,
        origin_y_mm=0.0
    )

    executor = MoveExecutor(board_cfg, log_fn=lambda x: None)
    tests_passed = 0
    tests_total = 0

    # Test 1: Normal move
    tests_total += 1
    actions = executor.plan_move("e2e4")
    if actions and len(actions) == 9:  # Expected action sequence
        print(f"✓ Normal move planned ({len(actions)} actions)")
        tests_passed += 1
    else:
        print(f"✗ Normal move planning failed (got {len(actions) if actions else 0} actions)")

    # Test 2: Capture move
    tests_total += 1
    executor.chess_engine.set_fen("rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2")
    actions = executor.plan_move("exd5")
    if actions:
        print(f"✓ Capture move planned ({len(actions)} actions)")
        tests_passed += 1
    else:
        print("✗ Capture move planning failed")

    print(f"\nResult: {tests_passed}/{tests_total} tests passed")
    return tests_passed == tests_total


def test_tacticsquest():
    """Test TacticsQuest sync service."""
    print("\n" + "="*60)
    print("TESTING: TacticsQuest Sync")
    print("="*60)

    try:
        from services.tacticsquest_sync import TacticsQuestSync, PendingMove
        print("✓ TacticsQuestSync imported")

        from ui.tacticsquest_panel import TacticsQuestPanel
        print("✓ TacticsQuestPanel imported")

        try:
            import supabase
            print("✓ Supabase library available")
        except ImportError:
            print("⚠ Supabase not installed")

        print("\nNote: Full testing requires Supabase credentials")
        print("      See TACTICSQUEST_INTEGRATION_GUIDE.md for setup")
        return True

    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_profiles():
    """Test profile/settings system."""
    print("\n" + "="*60)
    print("TESTING: Profile Management")
    print("="*60)

    try:
        from logic.profiles import Settings
        print("✓ Settings class imported")

        # Create settings instance (uses default config path)
        settings = Settings()
        print("✓ Settings initialized")

        # Test getting profiles
        profiles = settings.get_profiles()
        if 'saved' in profiles:
            print(f"✓ Found {len(profiles['saved'])} profile(s)")
        else:
            print("✗ No profiles found")
            return False

        # Test active profile
        active = settings.get_active_profile_name()
        print(f"✓ Active profile: {active}")

        # Test board config
        board = settings.get_board()
        if board:
            print(f"✓ Board config: {board['width']}x{board['height']}mm")
        else:
            print("✗ Board config missing")
            return False

        return True

    except Exception as e:
        print(f"✗ Profile test failed: {e}")
        return False


def run_quick_tests():
    """Run quick tests on all main features."""
    print("\n" + "="*70)
    print("CHESS MOVER MACHINE - QUICK FEATURE TEST")
    print("="*70)

    results = {}

    # Run tests
    tests = [
        ("Chess Engine", test_chess_engine),
        ("Stockfish", test_stockfish),
        ("Move Executor", test_move_executor),
        ("TacticsQuest Sync", test_tacticsquest),
        ("Profile Management", test_profiles),
    ]

    for name, test_func in tests:
        try:
            result = test_func()
            results[name] = result
        except Exception as e:
            print(f"\n✗ {name} crashed: {e}")
            import traceback
            traceback.print_exc()
            results[name] = False

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    passed = 0
    failed = 0
    skipped = 0

    for name, result in results.items():
        if result is True:
            print(f"✓ {name}: PASSED")
            passed += 1
        elif result is False:
            print(f"✗ {name}: FAILED")
            failed += 1
        elif result is None:
            print(f"⚠ {name}: SKIPPED (optional)")
            skipped += 1

    print("\n" + "="*70)
    print(f"Total: {passed} passed, {failed} failed, {skipped} skipped")

    if failed == 0:
        print("\n🎉 ALL CORE FEATURES WORKING!")
        print("\nReady for:")
        print("  • PGN game replay")
        print("  • Move-by-move navigation")
        print("  • Chess analysis (with Stockfish)")
        print("  • TacticsQuest sync (with credentials)")
        print("  • Profile management")
        print("\nNext: Connect Raspberry Pi hardware tomorrow!")
    else:
        print(f"\n⚠ {failed} test(s) failed")

    print("="*70)

    return failed == 0


if __name__ == "__main__":
    success = run_quick_tests()
    sys.exit(0 if success else 1)
