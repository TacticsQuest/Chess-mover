"""Launch Chess Mover Machine in compact/touchscreen mode for testing."""
import sys
if sys.platform.startswith("win"):
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

import tkinter as tk

# Monkey-patch screen size detection BEFORE importing BoardApp
# This ensures the app sees 1024x600 during initialization
original_screenwidth = tk.Tk.winfo_screenwidth
original_screenheight = tk.Tk.winfo_screenheight

def mock_screenwidth(self):
    return 1024

def mock_screenheight(self):
    return 600

# Apply patches BEFORE importing the app
tk.Tk.winfo_screenwidth = mock_screenwidth
tk.Tk.winfo_screenheight = mock_screenheight

# NOW import the app (after patching)
from ui.board_window import BoardApp

VERSION = "1.3.0"
print("=" * 60)
print(f"CHESS MOVER MACHINE - 7\" TOUCHSCREEN MODE v{VERSION}")
print("=" * 60)
print("Screen: 1024x600 (simulated)")
print("Features:")
print("  - Maximized board (728x728 - edge to edge)")
print("  - Compact piece palette (272 width, 38px buttons)")
print("  - Profile selector in right panel")
print("  - No title text, theme toggle, or AI Training tab")
print("  - Logs button in toolbar")
print("=" * 60)

# Launch the app
app = BoardApp()

# Force the window to 1024x600 and disable fullscreen for testing
app.attributes('-fullscreen', False)
app.geometry("1024x600")
app.resizable(False, False)  # Prevent resizing

app.mainloop()

# Restore original methods (though app is closing)
tk.Tk.winfo_screenwidth = original_screenwidth
tk.Tk.winfo_screenheight = original_screenheight
