import tkinter as tk
from tkinter import ttk
from typing import Callable

# Board theme names (must match BOARD_THEMES in editor_window.py)
THEME_NAMES = [
    'Classic Brown',
    'Green',
    'Blue',
    'Gray',
    'Black & White',
    'Wood',
    'Ice',
    'Purple',
    'Red',
    'Newspaper'
]

class SettingsWindow(tk.Toplevel):
    def __init__(self, master, board_cfg: dict, serial_cfg: dict, safety_cfg: dict, ports: list[str], on_save: Callable[[dict, dict, dict], None], settings_obj=None):
        super().__init__(master)
        self.title("Settings")
        self.resizable(False, False)
        self.on_save = on_save
        self.settings_obj = settings_obj  # For profile manager access

        # Profile Manager Button at top
        if self.settings_obj:
            profile_frame = ttk.Frame(self)
            profile_frame.grid(row=0, column=0, padx=8, pady=8, sticky="ew")

            active_profile = self.settings_obj.get_active_profile_name()
            ttk.Label(
                profile_frame,
                text=f"Active Profile: {active_profile}",
                font=("Segoe UI", 10, "bold")
            ).grid(row=0, column=0, sticky="w", padx=6)

            ttk.Button(
                profile_frame,
                text="📁 Manage Profiles",
                command=self._open_profile_manager
            ).grid(row=0, column=1, padx=6)

        # Serial
        frm_serial = ttk.LabelFrame(self, text="Serial")
        frm_serial.grid(row=1, column=0, padx=8, pady=8, sticky="ew")
        ttk.Label(frm_serial, text="Port").grid(row=0, column=0, sticky="w")
        self.cmb_port = ttk.Combobox(frm_serial, values=ports, width=20)
        self.cmb_port.grid(row=0, column=1, padx=6)
        self.cmb_port.set(serial_cfg.get('port', ''))

        ttk.Label(frm_serial, text="Baud").grid(row=1, column=0, sticky="w")
        self.ent_baud = ttk.Entry(frm_serial, width=10)
        self.ent_baud.insert(0, str(serial_cfg.get('baudrate', 115200)))
        self.ent_baud.grid(row=1, column=1, sticky="w", padx=6)

        # Board
        frm_board = ttk.LabelFrame(self, text="Board")
        frm_board.grid(row=2, column=0, padx=8, pady=8, sticky="ew")
        self._add_labeled_entry(frm_board, 0, "Files", board_cfg.get('files', 8))
        self._add_labeled_entry(frm_board, 1, "Ranks", board_cfg.get('ranks', 8))
        self._add_labeled_entry(frm_board, 2, "Width (mm)", board_cfg.get('width_mm', 400.0))
        self._add_labeled_entry(frm_board, 3, "Height (mm)", board_cfg.get('height_mm', 400.0))
        self._add_labeled_entry(frm_board, 4, "Origin X (A1 center, mm)", board_cfg.get('origin_x_mm', 0.0))
        self._add_labeled_entry(frm_board, 5, "Origin Y (A1 center, mm)", board_cfg.get('origin_y_mm', 0.0))
        self._add_labeled_entry(frm_board, 6, "Feedrate (mm/min)", board_cfg.get('feedrate_mm_min', 2000))

        # Safety / Speed Limiter
        frm_safety = ttk.LabelFrame(self, text="Safety & Speed Limits")
        frm_safety.grid(row=3, column=0, padx=8, pady=8, sticky="ew")

        # Speed limit toggle
        self.enable_speed_limit_var = tk.BooleanVar(value=safety_cfg.get('enable_speed_limit', True))
        chk_enable = ttk.Checkbutton(
            frm_safety,
            text="Enable Speed Limiting",
            variable=self.enable_speed_limit_var
        )
        chk_enable.grid(row=0, column=0, columnspan=2, sticky="w", padx=6, pady=4)

        self._add_labeled_entry(frm_safety, 1, "Max Speed (mm/min)", safety_cfg.get('max_speed_mm_min', 5000))
        self._add_labeled_entry(frm_safety, 2, "Min Speed (mm/min)", safety_cfg.get('min_speed_mm_min', 100))

        # UI Settings (Board Theme)
        frm_ui = ttk.LabelFrame(self, text="Appearance")
        frm_ui.grid(row=4, column=0, padx=8, pady=8, sticky="ew")

        ttk.Label(frm_ui, text="Board Theme").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        self.cmb_theme = ttk.Combobox(frm_ui, values=THEME_NAMES, width=20, state="readonly")
        self.cmb_theme.grid(row=0, column=1, padx=6, pady=6, sticky="w")

        # Get current theme from settings
        current_theme = 'Classic Brown'
        if self.settings_obj:
            current_theme = self.settings_obj.get_board_theme()
        self.cmb_theme.set(current_theme)

        # Buttons
        frm_btn = ttk.Frame(self)
        frm_btn.grid(row=5, column=0, padx=8, pady=8, sticky="e")
        ttk.Button(frm_btn, text="Cancel", command=self.destroy).grid(row=0, column=0, padx=6)
        ttk.Button(frm_btn, text="Save", command=self._save).grid(row=0, column=1)

    def _add_labeled_entry(self, parent, row, label, value):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w")
        ent = ttk.Entry(parent, width=18)
        ent.grid(row=row, column=1, sticky="w", padx=6, pady=2)
        ent.insert(0, str(value))
        setattr(self, f"ent_{label.split('(')[0].strip().replace(' ', '_').lower()}", ent)

    def _save(self):
        serial_cfg = {
            'port': self.cmb_port.get().strip(),
            'baudrate': int(self.ent_baud.get().strip() or 115200)
        }
        board_cfg = {
            'files': int(self.ent_files.get().strip() or 8),
            'ranks': int(self.ent_ranks.get().strip() or 8),
            'width_mm': float(self.ent_width.get().strip() or 400.0),
            'height_mm': float(self.ent_height.get().strip() or 400.0),
            'origin_x_mm': float(self.ent_origin_x.get().strip() or 0.0),
            'origin_y_mm': float(self.ent_origin_y.get().strip() or 0.0),
            'feedrate_mm_min': int(self.ent_feedrate.get().strip() or 2000),
        }
        safety_cfg = {
            'enable_speed_limit': self.enable_speed_limit_var.get(),
            'max_speed_mm_min': int(self.ent_max_speed.get().strip() or 5000),
            'min_speed_mm_min': int(self.ent_min_speed.get().strip() or 100),
        }

        # Save board theme
        if self.settings_obj:
            theme_name = self.cmb_theme.get()
            self.settings_obj.set_board_theme(theme_name)
            self.settings_obj.save()

        self.on_save(board_cfg, serial_cfg, safety_cfg)
        self.destroy()

    def _open_profile_manager(self):
        """Open the profile manager window."""
        from .profile_manager_window import ProfileManagerWindow

        def on_profile_changed(profile_name):
            """Handle profile switching."""
            # Update the active profile label in settings window
            if hasattr(self, 'settings_obj') and self.settings_obj:
                # Reload settings to reflect profile change
                # The parent window will handle full reload
                pass

        ProfileManagerWindow(self, self.settings_obj, on_profile_changed)
