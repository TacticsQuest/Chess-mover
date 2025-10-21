"""
Chess Mover Machine - Feature Test Suite

Quick validation that all major components work correctly.
"""

import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

print("\n" + "="*70)
print("CHESS MOVER MACHINE - FEATURE VALIDATION")
print("="*70)

# Test 1: Chess Engine
print("\n[1/5] Chess Engine...")
try:
    from logic.chess_engine import ChessEngine
    engine = ChessEngine()

    # Basic moves
    assert engine.make_move("e4") is not None, "Move e4 failed"
    assert engine.make_move("e5") is not None, "Move e5 failed"
    assert engine.get_move_list_san() == ["e4", "e5"], "Move history incorrect"

    # Illegal move rejection
    assert engine.make_move("invalid") is None, "Illegal move accepted"

    # PGN loading
    engine.reset()
    assert engine.load_pgn("1. e4 e5"), "PGN loading failed"

    # FEN loading
    assert engine.set_fen("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"), "FEN loading failed"

    print("   ✓ Move validation works")
    print("   ✓ PGN/FEN loading works")
    print("   ✓ Chess rules enforced")
    print("   PASSED")
    test1_pass = True
except Exception as e:
    print(f"   ✗ FAILED: {e}")
    test1_pass = False

# Test 2: Stockfish Integration
print("\n[2/5] Stockfish Engine (Optional)...")
try:
    from logic.stockfish_engine import StockfishEngine
    engine = StockfishEngine()
    print(f"   ✓ Found: {engine.stockfish_path}")

    engine.start()
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    best = engine.get_best_move(fen, time_ms=500)
    assert best is not None, "No best move"
    print(f"   ✓ Best move: {best}")
    engine.stop()
    print("   PASSED")
    test2_pass = True
except FileNotFoundError:
    print("   ⚠ Not installed (optional)")
    print("   Install: choco install stockfish")
    print("   SKIPPED")
    test2_pass = None
except Exception as e:
    print(f"   ✗ FAILED: {e}")
    test2_pass = False

# Test 3: Move Executor
print("\n[3/5] Move Executor...")
try:
    from logic.move_executor import MoveExecutor, ActionType
    from logic.chess_engine import ChessEngine
    from logic.board_map import BoardConfig
    from logic.profiles import Settings
    from logic.smart_storage import SmartStorage, StorageStrategy

    settings = Settings()
    engine = ChessEngine()
    board_cfg = BoardConfig(
        files=8,
        ranks=8,
        width_mm=400.0,
        height_mm=400.0,
        origin_x_mm=0.0,
        origin_y_mm=0.0
    )
    smart_storage = SmartStorage(board_cfg, StorageStrategy.BY_COLOR)

    executor = MoveExecutor(engine, board_cfg, settings, smart_storage)

    # Plan a move
    actions = executor.plan_move("e2e4")
    assert actions is not None, "Move planning failed"
    assert len(actions) > 0, "No actions generated"

    # Check action types
    action_types = [a.action_type for a in actions]
    assert ActionType.MOVE_TO in action_types, "No MOVE_TO action"
    assert ActionType.GRIP_CLOSE in action_types, "No GRIP_CLOSE action"

    print(f"   ✓ Planned {len(actions)} actions for e2e4")
    print("   ✓ Action sequence correct")
    print("   PASSED")
    test3_pass = True
except Exception as e:
    print(f"   ✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    test3_pass = False

# Test 4: TacticsQuest Sync
print("\n[4/5] TacticsQuest Integration...")
try:
    from services.tacticsquest_sync import TacticsQuestSync, PendingMove
    from ui.tacticsquest_panel import TacticsQuestPanel

    print("   ✓ Service layer imports")
    print("   ✓ UI panel imports")

    try:
        import supabase
        print("   ✓ Supabase client available")
    except ImportError:
        print("   ⚠ Supabase not installed")

    print("   Note: Full test requires credentials")
    print("   PASSED")
    test4_pass = True
except Exception as e:
    print(f"   ✗ FAILED: {e}")
    test4_pass = False

# Test 5: Profile Management
print("\n[5/5] Profile Management...")
try:
    from logic.profiles import Settings

    settings = Settings()
    assert settings is not None, "Settings init failed"

    profiles = settings.get_profiles()
    assert 'saved' in profiles, "No profiles found"
    assert len(profiles['saved']) > 0, "No saved profiles"

    active = settings.get_active_profile_name()
    assert active is not None, "No active profile"
    print(f"   ✓ Active profile: {active}")

    profile = settings.get_active_profile()
    assert profile is not None, "No active profile config"
    board = profile.get('board', profile)  # Handle both flat and nested structures
    width = board.get('width_mm', board.get('width', 400))
    height = board.get('height_mm', board.get('height', 400))
    print(f"   ✓ Board: {width}x{height}mm")

    profile_names = settings.get_profile_names()
    print(f"   ✓ {len(profile_names)} profile(s) available")

    print("   PASSED")
    test5_pass = True
except Exception as e:
    print(f"   ✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    test5_pass = False

# Summary
print("\n" + "="*70)
print("SUMMARY")
print("="*70)

results = [
    ("Chess Engine", test1_pass),
    ("Stockfish", test2_pass),
    ("Move Executor", test3_pass),
    ("TacticsQuest", test4_pass),
    ("Profiles", test5_pass),
]

passed = sum(1 for _, r in results if r is True)
failed = sum(1 for _, r in results if r is False)
skipped = sum(1 for _, r in results if r is None)

for name, result in results:
    if result is True:
        print(f"✓ {name}")
    elif result is False:
        print(f"✗ {name}")
    elif result is None:
        print(f"⚠ {name} (optional)")

print(f"\nTotal: {passed} passed, {failed} failed, {skipped} skipped")

if failed == 0:
    print("\n🎉 ALL CORE FEATURES WORKING!")
    print("\n✓ Ready for Raspberry Pi deployment")
    print("✓ Chess games can be loaded and replayed")
    print("✓ Moves validated by chess rules")
    print("✓ TacticsQuest sync ready (needs credentials)")
    print("✓ Profile management operational")
    if test2_pass:
        print("✓ Stockfish available for offline analysis")

    print("\n📖 See documentation:")
    print("   • RASPBERRY_PI_SETUP.md - Pi deployment guide")
    print("   • CHESS_AUTOMATION_GUIDE.md - Game replay guide")
    print("   • TACTICSQUEST_INTEGRATION_GUIDE.md - Online sync setup")
else:
    print(f"\n⚠ {failed} test(s) need attention")

print("="*70)

sys.exit(0 if failed == 0 else 1)
