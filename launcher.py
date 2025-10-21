"""
Chess Mover Machine - Enhanced Launcher
This launcher provides better error handling and startup checks
"""

import sys
import os
from pathlib import Path

def check_python_version():
    """Ensure Python version is 3.11+"""
    if sys.version_info < (3, 11):
        print("=" * 60)
        print("ERROR: Python 3.11 or higher is required")
        print(f"Current version: {sys.version}")
        print("\nPlease install Python 3.11+ from python.org")
        print("=" * 60)
        input("\nPress Enter to exit...")
        sys.exit(1)

def check_dependencies():
    """Check if required packages are installed"""
    print("Checking dependencies...")

    missing = []

    try:
        import serial
        print("  [OK] pyserial")
    except ImportError:
        print("  [MISSING] pyserial")
        missing.append("pyserial")

    try:
        import yaml
        print("  [OK] pyyaml")
    except ImportError:
        print("  [MISSING] pyyaml")
        missing.append("pyyaml")

    if missing:
        print(f"\nMissing packages: {', '.join(missing)}")
        print("\nInstalling dependencies...")

        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                check=True,
                capture_output=True,
                text=True
            )
            print("[OK] Dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"\n[ERROR] Failed to install dependencies:")
            print(e.stderr)
            input("\nPress Enter to exit...")
            sys.exit(1)
        except Exception as e:
            print(f"\n[ERROR] Error: {e}")
            input("\nPress Enter to exit...")
            sys.exit(1)
    else:
        print("[OK] All dependencies installed\n")

def check_config():
    """Ensure config directory exists"""
    config_dir = Path("config")
    settings_file = config_dir / "settings.yaml"

    if not config_dir.exists():
        print("Creating config directory...")
        config_dir.mkdir(exist_ok=True)

    if not settings_file.exists():
        print("[WARN] settings.yaml not found")
        print("       Settings will be created with defaults on first run")

def main():
    """Main launcher"""
    print("=" * 60)
    print("  Chess Mover Machine - Control Application")
    print("=" * 60)
    print()

    # Check Python version
    print(f"Python version: {sys.version.split()[0]}")
    check_python_version()
    print()

    # Check dependencies
    check_dependencies()

    # Check config
    check_config()
    print()

    # Launch application
    print("=" * 60)
    print("Starting Chess Mover Machine...")
    print("Close this window or press Ctrl+C to exit the application")
    print("=" * 60)
    print()

    try:
        # Import and run the application
        from ui.board_window import BoardApp

        app = BoardApp()
        app.mainloop()

    except KeyboardInterrupt:
        print("\n\nApplication stopped by user (Ctrl+C)")
    except Exception as e:
        print("\n" + "=" * 60)
        print("ERROR: Application crashed")
        print("=" * 60)
        print(f"\nError type: {type(e).__name__}")
        print(f"Error message: {e}")
        print("\nFull traceback:")
        import traceback
        traceback.print_exc()
        print("\n" + "=" * 60)
        input("\nPress Enter to exit...")
        sys.exit(1)

if __name__ == "__main__":
    main()
