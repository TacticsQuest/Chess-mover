"""
Consolidated Logging System for Chess Mover Machine

Provides unified logging to both GUI console and file.
"""

import logging
import os
from datetime import datetime
from pathlib import Path

class ChessMoverLogger:
    """Centralized logger for the Chess Mover Machine."""

    def __init__(self, gui_callback=None):
        """
        Initialize logger with optional GUI callback.

        Args:
            gui_callback: Function to call for GUI log display (e.g., text widget insert)
        """
        self.gui_callback = gui_callback

        # Create logs directory
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)

        # Create logger
        self.logger = logging.getLogger("ChessMover")
        self.logger.setLevel(logging.DEBUG)

        # Prevent duplicate handlers
        if self.logger.handlers:
            self.logger.handlers.clear()

        # File handler - rotating by date
        log_file = self.log_dir / f"chess_mover_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        self.info("=" * 60)
        self.info("Chess Mover Machine - Session Started")
        self.info("=" * 60)

    def _log_to_gui(self, message: str):
        """Send message to GUI if callback is set."""
        if self.gui_callback:
            try:
                self.gui_callback(message)
            except Exception as e:
                # Avoid infinite loop if GUI logging fails
                print(f"GUI logging failed: {e}")

    def debug(self, message: str):
        """Log debug message (file only)."""
        self.logger.debug(message)

    def info(self, message: str):
        """Log info message (file + console + GUI)."""
        self.logger.info(message)
        self._log_to_gui(f"[INFO] {message}")

    def warning(self, message: str):
        """Log warning message (file + console + GUI)."""
        self.logger.warning(message)
        self._log_to_gui(f"[WARN] {message}")

    def error(self, message: str, exc_info=None):
        """Log error message with optional exception info."""
        self.logger.error(message, exc_info=exc_info)
        self._log_to_gui(f"[ERROR] {message}")

        if exc_info:
            import traceback
            tb = ''.join(traceback.format_exception(*exc_info))
            self.logger.error(f"Traceback:\n{tb}")

    def gantry(self, message: str):
        """Log gantry-specific message."""
        self.info(f"[GANTRY] {message}")

    def servo(self, message: str):
        """Log servo-specific message."""
        self.info(f"[SERVO] {message}")

    def move(self, message: str):
        """Log movement command."""
        self.info(f"[MOVE] {message}")

    def grbl(self, message: str):
        """Log GRBL response."""
        self.debug(f"[GRBL] {message}")
        self._log_to_gui(f"<< {message}")

    def command(self, message: str):
        """Log user command."""
        self.info(f"[CMD] {message}")


# Global logger instance
_logger_instance = None

def get_logger(gui_callback=None):
    """Get or create the global logger instance."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = ChessMoverLogger(gui_callback)
    elif gui_callback and _logger_instance.gui_callback != gui_callback:
        # Update GUI callback if changed
        _logger_instance.gui_callback = gui_callback
    return _logger_instance
