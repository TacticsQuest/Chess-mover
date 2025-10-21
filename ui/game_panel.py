"""
Chess Game Control Panel

UI for loading PGN files, stepping through games, and controlling chess automation.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Callable

from logic.game_controller import GameController, GameMode


class GamePanel(tk.Frame):
    """
    Game control panel for chess automation.

    Features:
    - Load PGN files
    - Step through moves (next/previous)
    - Auto-play games
    - Display move list
    - Show game state
    """

    def __init__(self, parent, game_controller: GameController, theme: dict):
        super().__init__(parent, bg=theme['panel_bg'])
        self.game_controller = game_controller
        self.theme = theme

        self.auto_play_active = False
        self.auto_play_delay = 2000  # ms between moves

        self._build_ui()

    def _build_ui(self):
        """Build the game panel UI."""
        # Header
        header = tk.Label(
            self,
            text="♟ Chess Game Control",
            font=("Segoe UI", 11, "bold"),
            bg=self.theme['panel_bg'],
            fg=self.theme['fg'],
            anchor="w",
            padx=15,
            pady=10
        )
        header.pack(fill=tk.X)

        # Content frame
        content = tk.Frame(self, bg=self.theme['panel_bg'])
        content.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))

        # PGN controls
        pgn_frame = tk.LabelFrame(content, text="PGN Game", bg=self.theme['input_bg'], fg=self.theme['fg'])
        pgn_frame.pack(fill=tk.X, pady=(0, 10))

        pgn_btn_frame = tk.Frame(pgn_frame, bg=self.theme['input_bg'])
        pgn_btn_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(
            pgn_btn_frame,
            text="📁 Load PGN File",
            command=self._load_pgn_file
        ).pack(side=tk.LEFT, padx=3)

        ttk.Button(
            pgn_btn_frame,
            text="📋 Paste PGN",
            command=self._paste_pgn
        ).pack(side=tk.LEFT, padx=3)

        ttk.Button(
            pgn_btn_frame,
            text="🆕 New Game",
            command=self._new_game
        ).pack(side=tk.LEFT, padx=3)

        # Playback controls
        playback_frame = tk.LabelFrame(content, text="Playback", bg=self.theme['input_bg'], fg=self.theme['fg'])
        playback_frame.pack(fill=tk.X, pady=(0, 10))

        # Progress display
        self.progress_label = tk.Label(
            playback_frame,
            text="Move 0/0",
            font=("Consolas", 9),
            bg=self.theme['input_bg'],
            fg=self.theme['accent']
        )
        self.progress_label.pack(pady=(10, 5))

        # Playback buttons
        playback_btn_frame = tk.Frame(playback_frame, bg=self.theme['input_bg'])
        playback_btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        ttk.Button(
            playback_btn_frame,
            text="⏮ First",
            command=self._goto_first,
            width=8
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            playback_btn_frame,
            text="◀ Prev",
            command=self._prev_move,
            width=8
        ).pack(side=tk.LEFT, padx=2)

        self.play_pause_btn = ttk.Button(
            playback_btn_frame,
            text="▶ Play",
            command=self._toggle_auto_play,
            width=8
        )
        self.play_pause_btn.pack(side=tk.LEFT, padx=2)

        ttk.Button(
            playback_btn_frame,
            text="Next ▶",
            command=self._next_move,
            width=8
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            playback_btn_frame,
            text="Last ⏭",
            command=self._goto_last,
            width=8
        ).pack(side=tk.LEFT, padx=2)

        # Game state display
        state_frame = tk.LabelFrame(content, text="Game State", bg=self.theme['input_bg'], fg=self.theme['fg'])
        state_frame.pack(fill=tk.X, pady=(0, 10))

        self.state_text = tk.Text(
            state_frame,
            height=4,
            bg=self.theme['input_bg'],
            fg=self.theme['input_fg'],
            font=("Consolas", 9),
            relief=tk.FLAT,
            bd=0,
            padx=10,
            pady=10
        )
        self.state_text.pack(fill=tk.X, padx=10, pady=10)
        self.state_text.config(state=tk.DISABLED)

        # Move list
        moves_frame = tk.LabelFrame(content, text="Move List", bg=self.theme['input_bg'], fg=self.theme['fg'])
        moves_frame.pack(fill=tk.BOTH, expand=True)

        # Scrollable move list
        scroll_frame = tk.Frame(moves_frame, bg=self.theme['input_bg'])
        scroll_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        scrollbar = ttk.Scrollbar(scroll_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.move_listbox = tk.Listbox(
            scroll_frame,
            font=("Consolas", 9),
            bg=self.theme['input_bg'],
            fg=self.theme['input_fg'],
            selectbackground=self.theme['accent'],
            selectforeground='white',
            height=8,
            yscrollcommand=scrollbar.set,
            relief=tk.FLAT
        )
        self.move_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.move_listbox.yview)

        # Bind double-click to jump to move
        self.move_listbox.bind("<Double-Button-1>", self._on_move_double_click)

        # Start update loop
        self._update_display()

    def _load_pgn_file(self):
        """Open file dialog to load a PGN file."""
        filename = filedialog.askopenfilename(
            title="Load PGN File",
            filetypes=[("PGN Files", "*.pgn"), ("All Files", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    pgn_content = f.read()

                if self.game_controller.load_pgn(pgn_content):
                    messagebox.showinfo("PGN Loaded", f"Game loaded successfully!\n\n{filename}")
                    self._update_display()
                else:
                    messagebox.showerror("Load Failed", "Failed to parse PGN file.")

            except Exception as e:
                messagebox.showerror("Load Failed", f"Error reading file:\n\n{e}")

    def _paste_pgn(self):
        """Open dialog to paste PGN text."""
        dialog = tk.Toplevel(self)
        dialog.title("Paste PGN")
        dialog.geometry("600x400")

        tk.Label(
            dialog,
            text="Paste PGN text below:",
            font=("Segoe UI", 10, "bold")
        ).pack(padx=10, pady=10)

        text_area = tk.Text(dialog, height=15, width=70, font=("Consolas", 9))
        text_area.pack(padx=10, pady=(0, 10), fill=tk.BOTH, expand=True)

        def load_pgn():
            pgn_content = text_area.get("1.0", tk.END).strip()
            if pgn_content:
                if self.game_controller.load_pgn(pgn_content):
                    messagebox.showinfo("PGN Loaded", "Game loaded successfully!")
                    self._update_display()
                    dialog.destroy()
                else:
                    messagebox.showerror("Load Failed", "Failed to parse PGN.")

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=(0, 10))

        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Load", command=load_pgn).pack(side=tk.LEFT, padx=5)

    def _new_game(self):
        """Start a new game from starting position."""
        result = messagebox.askyesno(
            "New Game",
            "Start a new game from the starting position?\n\nThis will clear the current game.",
            icon='question'
        )

        if result:
            self.game_controller.new_game()
            self._update_display()
            messagebox.showinfo("New Game", "New game started!\n\nYou can now make moves manually.")

    def _next_move(self):
        """Execute next move in PGN replay."""
        if self.game_controller.pgn_next_move(execute_physically=True):
            self._update_display()
        else:
            self.auto_play_active = False
            self.play_pause_btn.config(text="▶ Play")

    def _prev_move(self):
        """Go back one move (engine only, not physical)."""
        if self.game_controller.pgn_previous_move():
            self._update_display()
            messagebox.showinfo(
                "Move Undone",
                "Note: Move undone in engine only.\n\nPhysical board not updated."
            )

    def _goto_first(self):
        """Jump to start of game."""
        if self.game_controller.pgn_goto_move(0):
            self._update_display()

    def _goto_last(self):
        """Jump to end of game."""
        current, total = self.game_controller.get_pgn_progress()
        if self.game_controller.pgn_goto_move(total):
            self._update_display()

    def _toggle_auto_play(self):
        """Toggle auto-play mode."""
        self.auto_play_active = not self.auto_play_active

        if self.auto_play_active:
            self.play_pause_btn.config(text="⏸ Pause")
            self._auto_play_step()
        else:
            self.play_pause_btn.config(text="▶ Play")

    def _auto_play_step(self):
        """Execute one step of auto-play."""
        if not self.auto_play_active:
            return

        if self.game_controller.pgn_next_move(execute_physically=True):
            self._update_display()
            # Schedule next move
            self.after(self.auto_play_delay, self._auto_play_step)
        else:
            # End of game
            self.auto_play_active = False
            self.play_pause_btn.config(text="▶ Play")
            messagebox.showinfo("Auto-Play Complete", "Reached end of game!")

    def _on_move_double_click(self, event):
        """Handle double-click on move list to jump to that move."""
        selection = self.move_listbox.curselection()
        if selection:
            move_index = selection[0]
            if self.game_controller.pgn_goto_move(move_index):
                self._update_display()

    def _update_display(self):
        """Update all displays with current game state."""
        state = self.game_controller.get_state()
        current, total = self.game_controller.get_pgn_progress()

        # Update progress
        self.progress_label.config(text=f"Move {current}/{total}")

        # Update state text
        self.state_text.config(state=tk.NORMAL)
        self.state_text.delete("1.0", tk.END)

        state_info = f"Mode: {state.mode.value}\n"
        state_info += f"Turn: {state.current_turn.capitalize()}\n"
        state_info += f"Moves: {state.move_count}\n"

        if state.is_checkmate:
            state_info += "Status: CHECKMATE!\n"
        elif state.is_stalemate:
            state_info += "Status: STALEMATE\n"
        elif state.is_check:
            state_info += "Status: CHECK\n"
        else:
            state_info += "Status: In progress\n"

        self.state_text.insert("1.0", state_info)
        self.state_text.config(state=tk.DISABLED)

        # Update move list
        self.move_listbox.delete(0, tk.END)
        moves = self.game_controller.get_move_history()

        for i, move in enumerate(moves):
            move_num = (i // 2) + 1
            if i % 2 == 0:  # White's move
                self.move_listbox.insert(tk.END, f"{move_num}. {move}")
            else:  # Black's move
                # Update the last entry to add black's move
                last_entry = self.move_listbox.get(tk.END)
                self.move_listbox.delete(tk.END)
                self.move_listbox.insert(tk.END, f"{last_entry} {move}")

        # Highlight current move
        if current > 0:
            list_index = (current - 1) // 2
            if list_index < self.move_listbox.size():
                self.move_listbox.selection_clear(0, tk.END)
                self.move_listbox.selection_set(list_index)
                self.move_listbox.see(list_index)

        # Schedule next update
        self.after(500, self._update_display)
