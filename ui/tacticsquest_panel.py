"""
TacticsQuest Integration Panel

UI for connecting to TacticsQuest and synchronizing correspondence games.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from services.tacticsquest_sync import TacticsQuestSync


class TacticsQuestPanel(tk.Frame):
    """
    TacticsQuest connection and game sync panel.

    Features:
    - Connect/disconnect from TacticsQuest
    - View synced games
    - Enable/disable sync for games
    - Online/offline mode toggle
    - Connection status
    """

    def __init__(self, parent, theme: dict):
        super().__init__(parent, bg=theme['panel_bg'])
        self.theme = theme

        self.sync_service: Optional[TacticsQuestSync] = None
        self.is_online = False

        # Credentials (will be loaded from config)
        self.supabase_url = ""
        self.supabase_key = ""
        self.user_id = ""

        # Cached game data
        self.cached_games = []

        self._build_ui()

    def _build_ui(self):
        """Build the TacticsQuest panel UI."""
        # Header
        header = tk.Label(
            self,
            text="⚡ TacticsQuest Sync",
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

        # Status frame
        status_frame = tk.LabelFrame(content, text="Connection", bg=self.theme['input_bg'], fg=self.theme['fg'])
        status_frame.pack(fill=tk.X, pady=(0, 10))

        status_content = tk.Frame(status_frame, bg=self.theme['input_bg'])
        status_content.pack(fill=tk.X, padx=10, pady=10)

        # Status indicator
        self.status_label = tk.Label(
            status_content,
            text="● Offline",
            font=("Segoe UI", 10, "bold"),
            bg=self.theme['input_bg'],
            fg=self.theme['danger']
        )
        self.status_label.pack(side=tk.LEFT)

        # Connect/Disconnect button
        self.connect_btn = ttk.Button(
            status_content,
            text="Connect",
            command=self._toggle_connection
        )
        self.connect_btn.pack(side=tk.RIGHT)

        # Sync mode selector
        mode_frame = tk.Frame(status_content, bg=self.theme['input_bg'])
        mode_frame.pack(side=tk.RIGHT, padx=(0, 10))

        tk.Label(
            mode_frame,
            text="Mode:",
            bg=self.theme['input_bg'],
            fg=self.theme['fg']
        ).pack(side=tk.LEFT, padx=(0, 5))

        # Sync modes with appropriate polling intervals
        sync_modes = {
            "Active (10s)": 10,      # Playing live, check every 10 seconds
            "Home (1min)": 60,       # At home, check every minute
            "Away (5min)": 300,      # Away from board, check every 5 minutes
            "Work (15min)": 900,     # At work, check every 15 minutes
            "Sleep (1hr)": 3600,     # Sleeping, check every hour
            "Custom": 0              # Custom interval
        }

        self.mode_var = tk.StringVar(value="Away (5min)")
        mode_combo = ttk.Combobox(
            mode_frame,
            textvariable=self.mode_var,
            values=list(sync_modes.keys()),
            state='readonly',
            width=12
        )
        mode_combo.pack(side=tk.LEFT)
        mode_combo.bind('<<ComboboxSelected>>', lambda e: self._update_poll_interval())

        self.sync_modes = sync_modes
        self.poll_interval = 300  # Default: 5 minutes

        # Configuration frame
        config_frame = tk.LabelFrame(content, text="Configuration", bg=self.theme['input_bg'], fg=self.theme['fg'])
        config_frame.pack(fill=tk.X, pady=(0, 10))

        config_content = tk.Frame(config_frame, bg=self.theme['input_bg'])
        config_content.pack(fill=tk.X, padx=10, pady=10)

        # User email (read-only display)
        tk.Label(
            config_content,
            text="User:",
            bg=self.theme['input_bg'],
            fg=self.theme['fg']
        ).grid(row=0, column=0, sticky="w", pady=5)

        self.user_label = tk.Label(
            config_content,
            text="davidljones88@yahoo.com",
            font=("Segoe UI", 9, "bold"),
            bg=self.theme['input_bg'],
            fg=self.theme['accent']
        )
        self.user_label.grid(row=0, column=1, sticky="w", pady=5, padx=(10, 0))

        # Settings button
        ttk.Button(
            config_content,
            text="⚙ Settings",
            command=self._open_settings
        ).grid(row=1, column=0, columnspan=2, pady=(5, 0), sticky="ew")

        # Synced games frame
        games_frame = tk.LabelFrame(content, text="Synced Games", bg=self.theme['input_bg'], fg=self.theme['fg'])
        games_frame.pack(fill=tk.BOTH, expand=True)

        # Games list
        scroll_frame = tk.Frame(games_frame, bg=self.theme['input_bg'])
        scroll_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        scrollbar = ttk.Scrollbar(scroll_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.games_listbox = tk.Listbox(
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
        self.games_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.games_listbox.yview)

        # Game actions
        actions_frame = tk.Frame(games_frame, bg=self.theme['input_bg'])
        actions_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        ttk.Button(
            actions_frame,
            text="🔄 Refresh",
            command=self._refresh_games
        ).pack(side=tk.LEFT, padx=3)

        ttk.Button(
            actions_frame,
            text="✓ Load to Board",
            command=self._load_selected_game
        ).pack(side=tk.LEFT, padx=3)

        ttk.Button(
            actions_frame,
            text="✗ Unsync",
            command=self._unsync_selected_game
        ).pack(side=tk.LEFT, padx=3)

        # Info label
        info_label = tk.Label(
            content,
            text="Correspondence games from TacticsQuest will\nauto-sync to the physical board.",
            font=("Segoe UI", 8),
            bg=self.theme['panel_bg'],
            fg=self.theme['text_secondary'],
            justify=tk.LEFT
        )
        info_label.pack(pady=(10, 0))

    def set_sync_service(self, sync_service: TacticsQuestSync):
        """
        Set the sync service instance.

        Args:
            sync_service: TacticsQuestSync instance
        """
        self.sync_service = sync_service

    def _update_poll_interval(self):
        """Update poll interval based on selected sync mode."""
        mode = self.mode_var.get()
        interval = self.sync_modes.get(mode, 300)

        if interval == 0:  # Custom mode
            # TODO: Show custom interval dialog
            messagebox.showinfo(
                "Custom Mode",
                "Custom polling interval will be available in next update!\n\nDefaulting to 5 minutes."
            )
            interval = 300

        self.poll_interval = interval

        # Update sync service if running
        if self.sync_service and self.is_online:
            self.sync_service.set_poll_interval(interval)

    def _toggle_connection(self):
        """Toggle connection to TacticsQuest."""
        if not self.sync_service:
            messagebox.showerror(
                "Not Configured",
                "TacticsQuest sync not configured.\n\nPlease configure Supabase credentials in Settings."
            )
            return

        if self.is_online:
            # Disconnect
            self.sync_service.stop()
            self.is_online = False
            self.status_label.config(text="● Offline", fg=self.theme['danger'])
            self.connect_btn.config(text="Connect")
        else:
            # Connect
            try:
                # Update poll interval from current mode
                self._update_poll_interval()
                self.sync_service.set_poll_interval(self.poll_interval)

                # Start sync
                self.sync_service.start()
                self.is_online = True
                self.status_label.config(text="● Online", fg=self.theme['success'])
                self.connect_btn.config(text="Disconnect")

                # Refresh games list
                self._refresh_games()

            except Exception as e:
                messagebox.showerror("Connection Failed", f"Failed to connect:\n\n{e}")

    def _open_settings(self):
        """Open TacticsQuest settings dialog."""
        dialog = tk.Toplevel(self)
        dialog.title("TacticsQuest Settings")
        dialog.geometry("500x300")

        tk.Label(
            dialog,
            text="Supabase Configuration",
            font=("Segoe UI", 12, "bold")
        ).pack(padx=20, pady=20)

        # Form
        form = tk.Frame(dialog)
        form.pack(fill=tk.BOTH, expand=True, padx=20)

        tk.Label(form, text="Supabase URL:").grid(row=0, column=0, sticky="w", pady=5)
        url_entry = ttk.Entry(form, width=40)
        url_entry.grid(row=0, column=1, pady=5, padx=(10, 0))
        url_entry.insert(0, self.supabase_url)

        tk.Label(form, text="Anon Key:").grid(row=1, column=0, sticky="w", pady=5)
        key_entry = ttk.Entry(form, width=40, show="*")
        key_entry.grid(row=1, column=1, pady=5, padx=(10, 0))
        key_entry.insert(0, self.supabase_key)

        tk.Label(form, text="User ID:").grid(row=2, column=0, sticky="w", pady=5)
        user_entry = ttk.Entry(form, width=40)
        user_entry.grid(row=2, column=1, pady=5, padx=(10, 0))
        user_entry.insert(0, self.user_id)

        def save_settings():
            self.supabase_url = url_entry.get().strip()
            self.supabase_key = key_entry.get().strip()
            self.user_id = user_entry.get().strip()

            # TODO: Save to config file
            messagebox.showinfo("Settings Saved", "TacticsQuest settings saved!\n\nRestart connection to apply.")
            dialog.destroy()

        # Buttons
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=20)

        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Save", command=save_settings).pack(side=tk.LEFT, padx=5)

    def _refresh_games(self):
        """Refresh the synced games list."""
        if not self.sync_service or not self.is_online:
            return

        try:
            games = self.sync_service.get_synced_games()

            # Cache for later use
            self.cached_games = games

            self.games_listbox.delete(0, tk.END)

            if not games:
                self.games_listbox.insert(tk.END, "No synced games")
                return

            for game in games:
                white = game.get('white_username', '?')
                black = game.get('black_username', '?')
                status = game.get('status', 'active')
                time_control = game.get('time_control', 'rapid')

                display = f"{white} vs {black} | {time_control} | {status}"
                self.games_listbox.insert(tk.END, display)

        except Exception as e:
            messagebox.showerror("Refresh Failed", f"Failed to refresh games:\n\n{e}")

    def _load_selected_game(self):
        """Load the selected game to the physical board."""
        selection = self.games_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a game to load.")
            return

        if not self.sync_service:
            messagebox.showerror("Not Available", "Sync service not configured.")
            return

        # Get selected game from cache
        game_index = selection[0]
        if game_index >= len(self.cached_games):
            messagebox.showerror("Error", "Invalid game selection.")
            return

        game = self.cached_games[game_index]
        game_id = game.get('id', '')
        fen = game.get('fen', '')
        white = game.get('white_username', '?')
        black = game.get('black_username', '?')

        # Confirm load
        result = messagebox.askyesno(
            "Load Game",
            f"Load this game to the physical board?\n\n{white} vs {black}\n\nThis will replace the current board position.",
            icon='question'
        )

        if not result:
            return

        # Load game via sync service (which has access to game_controller)
        try:
            # Use the sync service's internal method to load
            game_controller = self.sync_service.game_controller
            if game_controller.load_fen(fen):
                self.sync_service.active_game_id = game_id
                messagebox.showinfo("Game Loaded", f"Game loaded successfully!\n\n{white} vs {black}")
            else:
                messagebox.showerror("Load Failed", f"Failed to load game position.\n\nFEN: {fen}")

        except Exception as e:
            messagebox.showerror("Load Failed", f"Error loading game:\n\n{e}")

    def _unsync_selected_game(self):
        """Unsync the selected game."""
        selection = self.games_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a game to unsync.")
            return

        if not self.sync_service:
            messagebox.showerror("Not Available", "Sync service not configured.")
            return

        # Get selected game from cache
        game_index = selection[0]
        if game_index >= len(self.cached_games):
            messagebox.showerror("Error", "Invalid game selection.")
            return

        game = self.cached_games[game_index]
        game_id = game.get('id', '')
        white = game.get('white_username', '?')
        black = game.get('black_username', '?')

        result = messagebox.askyesno(
            "Unsync Game",
            f"Stop syncing this game to the physical board?\n\n{white} vs {black}",
            icon='question'
        )

        if result:
            try:
                if self.sync_service.disable_game_sync(game_id):
                    messagebox.showinfo("Unsynced", f"Game unsynced successfully!\n\n{white} vs {black}")
                    self._refresh_games()
                else:
                    messagebox.showerror("Unsync Failed", "Failed to unsync game.")

            except Exception as e:
                messagebox.showerror("Unsync Failed", f"Error unsyncing game:\n\n{e}")
