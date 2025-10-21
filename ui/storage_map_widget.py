"""
Storage Map Widget - Visual representation of captured piece storage.

Displays a compact grid showing which storage squares are occupied and by which pieces.
"""

import tkinter as tk
from typing import Optional, Dict
from logic.smart_storage import SmartStorage, StorageStrategy
from logic.board_state import Piece


class StorageMapWidget(tk.Frame):
    """
    Visual storage map widget showing occupied/available storage squares.
    """

    def __init__(self, parent, smart_storage: SmartStorage, theme: Dict):
        super().__init__(parent)
        self.smart_storage = smart_storage
        self.theme = theme

        self.configure(bg=theme['panel_bg'])
        self._build_ui()

    def _build_ui(self):
        """Build the storage map UI."""
        # Title
        title_frame = tk.Frame(self, bg=self.theme['panel_bg'])
        title_frame.pack(fill=tk.X, pady=(0, 5))

        tk.Label(
            title_frame,
            text="Storage Map",
            font=("Segoe UI", 9, "bold"),
            bg=self.theme['panel_bg'],
            fg=self.theme['fg']
        ).pack(side=tk.LEFT)

        # Strategy selector (small dropdown)
        self.strategy_var = tk.StringVar(value=self.smart_storage.strategy.value)

        strategy_menu = tk.OptionMenu(
            title_frame,
            self.strategy_var,
            *[s.value for s in StorageStrategy],
            command=self._on_strategy_change
        )
        strategy_menu.config(
            font=("Segoe UI", 7),
            bg=self.theme['input_bg'],
            fg=self.theme['fg'],
            relief=tk.FLAT,
            highlightthickness=0
        )
        strategy_menu.pack(side=tk.RIGHT)

        # Stats row
        self.stats_label = tk.Label(
            self,
            text="",
            font=("Segoe UI", 8),
            bg=self.theme['panel_bg'],
            fg=self.theme['text_secondary'],
            justify=tk.LEFT
        )
        self.stats_label.pack(fill=tk.X, pady=(0, 5))

        # Canvas for visual grid
        self.canvas = tk.Canvas(
            self,
            bg=self.theme['canvas_bg'],
            highlightthickness=0,
            height=120  # Compact size
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self._update_display()

    def _on_strategy_change(self, value: str):
        """Handle strategy change."""
        try:
            strategy = StorageStrategy(value)
            self.smart_storage.set_strategy(strategy)
            self._update_display()
        except ValueError:
            pass

    def _update_display(self):
        """Update the visual storage map display."""
        self.canvas.delete("all")

        # Get board configuration
        files = self.smart_storage.board_config.files
        ranks = self.smart_storage.board_config.ranks

        # Calculate square size
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width <= 1:
            canvas_width = 200  # Default before window is shown

        sq_size = min(canvas_width / files, canvas_height / ranks)

        # Center the grid
        grid_width = files * sq_size
        grid_height = ranks * sq_size
        offset_x = (canvas_width - grid_width) / 2
        offset_y = (canvas_height - grid_height) / 2

        # Draw grid
        for rank_idx in range(ranks):
            for file_idx in range(files):
                square = f"{chr(ord('a') + file_idx)}{rank_idx + 1}"

                x0 = offset_x + file_idx * sq_size
                y0 = offset_y + (ranks - 1 - rank_idx) * sq_size
                x1 = x0 + sq_size
                y1 = y0 + sq_size

                # Check if this is a storage square
                if self.smart_storage.is_storage_square(square):
                    piece = self.smart_storage.get_piece_at(square)

                    if piece:
                        # Occupied - show piece color
                        color = '#d4af37' if piece.color.value == 'w' else '#4a4a4a'  # Gold/dark
                        self.canvas.create_rectangle(
                            x0, y0, x1, y1,
                            fill=color,
                            outline='#666',
                            width=1
                        )

                        # Show piece symbol
                        symbol = str(piece)
                        text_color = '#000' if piece.color.value == 'w' else '#fff'
                        self.canvas.create_text(
                            (x0 + x1) / 2,
                            (y0 + y1) / 2,
                            text=symbol,
                            fill=text_color,
                            font=("Segoe UI", int(sq_size * 0.5), "bold")
                        )
                    else:
                        # Empty storage
                        self.canvas.create_rectangle(
                            x0, y0, x1, y1,
                            fill='#3a3a3a',
                            outline='#555',
                            width=1
                        )
                else:
                    # Playing square - very faint
                    self.canvas.create_rectangle(
                        x0, y0, x1, y1,
                        fill='#2d2d2d',
                        outline='#333',
                        width=1
                    )

        # Update stats
        stats = self.smart_storage.get_storage_stats()
        self.stats_label.config(
            text=f"Occupied: {stats['occupied']}/{stats['total']} "
                 f"({stats['utilization']:.0f}%) | "
                 f"Strategy: {stats['strategy']}"
        )

    def refresh(self, board_state=None):
        """
        Refresh the storage map display.

        Args:
            board_state: Optional BoardState to sync with
        """
        if board_state:
            self.smart_storage.sync_with_board_state(board_state)

        self._update_display()

    def get_stats(self) -> Dict:
        """Get current storage statistics."""
        return self.smart_storage.get_storage_stats()
