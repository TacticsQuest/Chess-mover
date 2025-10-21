# --- High DPI fix for Windows (Tkinter) ---
import sys
if sys.platform.startswith("win"):
    try:
        import ctypes
        # Per-monitor DPI aware (Windows 8.1+)
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            # Legacy fallback (Windows Vista/7)
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass
# ------------------------------------------

from ui.board_window import BoardApp

if __name__ == "__main__":
    app = BoardApp()

    # Configure Tk scaling for high DPI
    try:
        scaling = app.winfo_fpixels('1i') / 72.0
        app.tk.call('tk', 'scaling', scaling)
    except Exception:
        pass

    app.mainloop()
