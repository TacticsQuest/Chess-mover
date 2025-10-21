import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
from logic.board_map import BoardConfig
from logic.move_planner import MovePlanner
from logic.profiles import Settings
from controllers.gantry_controller import GantryController, ConnectionState, Position, SafetyLimits
from controllers.servo_controller import ServoController
from .settings_window import SettingsWindow
from .editor_window import EditorWindow
from logic.board_state import BoardState

GRID_PAD = 16
CANVAS_MIN = 520

# Modern color themes
THEMES = {
    'light': {
        'bg': '#ffffff',
        'fg': '#2c3e50',
        'canvas_bg': '#f8f9fa',
        'panel_bg': '#f0f2f5',
        'input_bg': '#ffffff',
        'input_fg': '#2c3e50',
        'button_bg': '#3498db',
        'button_fg': '#ffffff',
        'button_hover': '#2980b9',
        'accent': '#3498db',
        'success': '#27ae60',
        'warning': '#f39c12',
        'danger': '#e74c3c',
        'border': '#dce0e5',
        'text_secondary': '#7f8c8d',
        'board_light': '#f0d9b5',
        'board_dark': '#b58863',
        'board_border': '#8b6f47'
    },
    'dark': {
        'bg': '#1e1e1e',
        'fg': '#e0e0e0',
        'canvas_bg': '#2d2d2d',
        'panel_bg': '#252525',
        'input_bg': '#3a3a3a',
        'input_fg': '#e0e0e0',
        'button_bg': '#3498db',
        'button_fg': '#ffffff',
        'button_hover': '#2980b9',
        'accent': '#3498db',
        'success': '#27ae60',
        'warning': '#f39c12',
        'danger': '#e74c3c',
        'border': '#3a3a3a',
        'text_secondary': '#95a5a6',
        'board_light': '#ebecd0',
        'board_dark': '#779556',
        'board_border': '#5a7a3c'
    }
}

class BoardApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Chess Mover Machine")
        self.geometry("1000x700")
        self.minsize(900, 600)

        # Theme management
        self.current_theme = 'dark'
        self.theme = THEMES[self.current_theme]

        self.settings = Settings()
        self.board_cfg = self._cfg_to_board(self.settings.get_board())

        # Initialize gantry with machine limits and speed limits
        machine_cfg = self.settings.get_machine()
        machine_limits = SafetyLimits(
            x_min=machine_cfg.get('x_min', 0.0),
            x_max=machine_cfg.get('x_max', 450.0),
            y_min=machine_cfg.get('y_min', 0.0),
            y_max=machine_cfg.get('y_max', 450.0),
            z_min=machine_cfg.get('z_min', 0.0),
            z_max=machine_cfg.get('z_max', 100.0)
        )
        self.gantry = GantryController(self._log, safety_limits=machine_limits)

        safety_cfg = self.settings.get_safety()
        self.gantry.max_speed_mm_min = safety_cfg.get('max_speed_mm_min', 5000)
        self.gantry.min_speed_mm_min = safety_cfg.get('min_speed_mm_min', 100)
        self.gantry.enable_speed_limit = safety_cfg.get('enable_speed_limit', True)

        self.servos = ServoController(self._log)
        self.move_planner = MovePlanner(self.board_cfg)

        # Track gantry position for highlighting
        self.current_gantry_square = None
        self.highlight_square_tag = None

        # Board state for editor
        self.board_state = BoardState()

        # View management
        self.current_view = 'main'  # 'main' or 'editor'
        self.main_view_frame = None
        self.editor_view_frame = None

        self._build_ui()
        self._poll_grbl()
        self._poll_servos()
        self._poll_position()  # Poll gantry position for highlighting

    def _cfg_to_board(self, d: dict) -> BoardConfig:
        return BoardConfig(
            files=int(d.get('files', 8)),
            ranks=int(d.get('ranks', 8)),
            width_mm=float(d.get('width_mm', 400.0)),
            height_mm=float(d.get('height_mm', 400.0)),
            origin_x_mm=float(d.get('origin_x_mm', 0.0)),
            origin_y_mm=float(d.get('origin_y_mm', 0.0)),
        )

    def _apply_theme(self):
        """Apply current theme to all widgets."""
        self.configure(bg=self.theme['bg'])
        self._redraw_board()

    def _toggle_theme(self):
        """Toggle between light and dark themes."""
        self.current_theme = 'light' if self.current_theme == 'dark' else 'dark'
        self.theme = THEMES[self.current_theme]

        # Rebuild UI with new theme
        for widget in self.winfo_children():
            widget.destroy()
        self._build_ui()

    def _create_button(self, parent, text, command, **kwargs):
        """Create a modern styled button."""
        bg = kwargs.pop('bg', self.theme['button_bg'])
        fg = kwargs.pop('fg', self.theme['button_fg'])
        padx = kwargs.pop('padx', 16)
        pady = kwargs.pop('pady', 8)
        font = kwargs.pop('font', ("Segoe UI", 9))

        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            font=font,
            relief=tk.FLAT,
            bd=0,
            padx=padx,
            pady=pady,
            cursor="hand2",
            activebackground=self.theme['button_hover'],
            activeforeground=fg,
            **kwargs
        )

        # Hover effects
        def on_enter(e):
            btn['bg'] = kwargs.get('hover_bg', self.theme['button_hover'])
        def on_leave(e):
            btn['bg'] = bg

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

        return btn

    def _build_ui(self):
        self.configure(bg=self.theme['bg'])

        # Modern top toolbar
        toolbar = tk.Frame(self, bg=self.theme['panel_bg'], height=60)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        toolbar.pack_propagate(False)

        # Left side - branding
        left_toolbar = tk.Frame(toolbar, bg=self.theme['panel_bg'])
        left_toolbar.pack(side=tk.LEFT, padx=20, pady=10)

        tk.Label(
            left_toolbar,
            text="♟ Chess Mover Machine",
            font=("Segoe UI", 14, "bold"),
            bg=self.theme['panel_bg'],
            fg=self.theme['accent']
        ).pack(side=tk.LEFT)

        # Middle - Profile selector
        middle_toolbar = tk.Frame(toolbar, bg=self.theme['panel_bg'])
        middle_toolbar.pack(side=tk.LEFT, expand=True)

        tk.Label(
            middle_toolbar,
            text="Profile:",
            font=("Segoe UI", 9),
            bg=self.theme['panel_bg'],
            fg=self.theme['text_secondary']
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.profile_var = tk.StringVar(value=self.settings.get_active_profile_name())
        self.profile_combo = ttk.Combobox(
            middle_toolbar,
            textvariable=self.profile_var,
            values=self.settings.get_profile_names(),
            state='readonly',
            width=25,
            font=("Segoe UI", 9)
        )
        self.profile_combo.pack(side=tk.LEFT)
        self.profile_combo.bind('<<ComboboxSelected>>', lambda e: self._switch_profile())

        # Right side - controls
        right_toolbar = tk.Frame(toolbar, bg=self.theme['panel_bg'])
        right_toolbar.pack(side=tk.RIGHT, padx=20, pady=10)

        # Theme toggle button
        theme_icon = "☀" if self.current_theme == 'dark' else "☾"
        self._create_button(
            right_toolbar,
            text=theme_icon,
            command=self._toggle_theme,
            bg=self.theme['panel_bg'],
            fg=self.theme['fg'],
            padx=12,
            pady=6,
            font=("Segoe UI", 12)
        ).pack(side=tk.RIGHT, padx=4)

        self._create_button(right_toolbar, text="Test Path", command=self._test_path).pack(side=tk.RIGHT, padx=4)
        self._create_button(right_toolbar, text="Settings", command=self._open_settings).pack(side=tk.RIGHT, padx=4)

        # Single toggle button for Connect/Disconnect
        self.connect_btn = self._create_button(right_toolbar, text="Connect", command=self._toggle_connection, bg=self.theme['success'])
        self.connect_btn.pack(side=tk.RIGHT, padx=4)

        # Main content area - unified editor view
        self.content_container = tk.Frame(self, bg=self.theme['bg'])
        self.content_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create unified editor view with all machine controls
        self.editor_view = EditorWindow(
            self.content_container,
            self.board_state,
            self.board_cfg,
            self.gantry,
            self.servos,
            on_send_to_machine=self._editor_send_to_machine,
            on_get_from_machine=self._editor_get_from_machine,
            on_auto_update=self._editor_auto_update,
            on_move_to_square=self._move_to_square_handler,
            on_calibrate=self._calibrate_handler,
            on_jog=self._jog_handler,
            on_home=self._home
        )
        self.editor_view.pack(fill=tk.BOTH, expand=True)

        # Keep canvas reference for board highlighting (used by _poll_position)
        self.canvas = self.editor_view.canvas

        # Create log widget for machine output (outside of editor)
        log_frame = tk.Frame(self, bg=self.theme['bg'])
        log_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        tk.Label(
            log_frame,
            text="📋 Command Log",
            font=("Segoe UI", 10, "bold"),
            bg=self.theme['bg'],
            fg=self.theme['fg']
        ).pack(anchor="w")

        self.txt_log = tk.Text(
            log_frame,
            height=6,
            bg=self.theme['input_bg'],
            fg=self.theme['input_fg'],
            font=("Consolas", 8),
            relief=tk.FLAT,
            bd=0,
            padx=8,
            pady=8
        )
        self.txt_log.pack(fill=tk.X)

        # Status bar
        self.status = tk.StringVar(value="Disconnected")
        status_bar = tk.Frame(self, bg=self.theme['panel_bg'], height=30)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        status_bar.pack_propagate(False)

        tk.Label(
            status_bar,
            textvariable=self.status,
            anchor="w",
            bg=self.theme['panel_bg'],
            fg=self.theme['fg'],
            font=("Segoe UI", 9),
            padx=20,
            pady=5
        ).pack(fill=tk.X)

    # Callback wrapper methods for editor
    def _jog_handler(self, x_dir: int, y_dir: int, distance: int):
        """Wrapper for jog callback from editor."""
        feed = self.settings.get_board().get('feedrate_mm_min', 2000)

        self._log(f"[JOG] Querying current position...")
        current_pos = self.gantry.get_current_position_blocking(timeout=2.0)

        if current_pos is None:
            self._log(f"[JOG] Warning: Could not read position, moving without limits")
            x_delta = x_dir * distance
            y_delta = y_dir * distance
        else:
            limits = self.gantry.safety_limits
            desired_x = current_pos.x + (x_dir * distance)
            desired_y = current_pos.y + (y_dir * distance)

            if x_dir > 0:
                actual_x = min(desired_x, limits.x_max)
                x_delta = actual_x - current_pos.x
            elif x_dir < 0:
                actual_x = max(desired_x, limits.x_min)
                x_delta = actual_x - current_pos.x
            else:
                x_delta = 0

            if y_dir > 0:
                actual_y = min(desired_y, limits.y_max)
                y_delta = actual_y - current_pos.y
            elif y_dir < 0:
                actual_y = max(desired_y, limits.y_min)
                y_delta = actual_y - current_pos.y
            else:
                y_delta = 0

            if abs(x_delta) < abs(x_dir * distance) or abs(y_delta) < abs(y_dir * distance):
                self._log(f"[JOG] Movement limited by boundaries (requested {distance}mm, moving {abs(x_delta if x_dir else y_delta):.1f}mm)")

        self._log(f"[JOG] Moving X{x_delta:+.1f} Y{y_delta:+.1f}mm")

        try:
            self.gantry.unlock()
            self.gantry.send("G91")
            self.gantry.send(f"G0 X{x_delta:.1f} Y{y_delta:.1f} F{feed}")
            self.gantry.send("G90")
        except Exception as e:
            self._log(f"[ERROR] Jog failed: {e}")
            messagebox.showerror("Jog Failed", str(e))

    def _move_to_square_handler(self, square: str):
        """Wrapper for move to square callback from editor."""
        square = square.strip().lower()

        if len(square) != 2:
            messagebox.showerror("Invalid Square", "Enter a square like E4, A1, or H8")
            return

        file_char = square[0]
        rank_char = square[1]

        if file_char not in 'abcdefgh' or rank_char not in '12345678':
            messagebox.showerror("Invalid Square", "Enter a valid square (A-H, 1-8)")
            return

        try:
            x, y = self.board_cfg.square_center_xy(square)
            feed = self.settings.get_board().get('feedrate_mm_min', 2000)

            self._log(f"[MOVE] Going to square {square.upper()} → X{x:.2f} Y{y:.2f}")

            self.gantry.unlock()
            self.gantry.set_mm_absolute()
            self.gantry.rapid_to(x, y, feed)
        except Exception as e:
            self._log(f"[ERROR] Move to {square.upper()} failed: {e}")
            messagebox.showerror("Move Failed", str(e))

    def _calibrate_handler(self, square: str):
        """Wrapper for calibration callback from editor."""
        square = square.strip().upper()

        if len(square) != 2:
            messagebox.showerror("Invalid Square", "Enter a square like A1, E4, or H8")
            return

        file_char = square[0].lower()
        rank_char = square[1]

        if file_char not in 'abcdefgh' or rank_char not in '12345678':
            messagebox.showerror("Invalid Square", "Enter a valid square (A-H, 1-8)")
            return

        result = messagebox.askyesno(
            "Calibrate Position",
            f"This will set the current gantry position as the center of square {square}.\n\n"
            f"Make sure the gantry head is positioned exactly over the center of {square}.\n\n"
            f"Continue?",
            icon='question'
        )

        if not result:
            return

        self._log(f"[CALIBRATE] Requesting current position for {square}...")
        pos = self.gantry.get_current_position_blocking(timeout=3.0)

        if pos is None:
            messagebox.showerror(
                "Calibration Failed",
                "Could not read current position from GRBL.\n\n"
                "Make sure the machine is connected and try again."
            )
            return

        file_idx = ord(file_char) - ord('a')
        rank_idx = int(rank_char) - 1

        board_cfg = self.settings.get_board()
        square_width = board_cfg['width_mm'] / board_cfg['files']
        square_height = board_cfg['height_mm'] / board_cfg['ranks']

        x_offset = file_idx * square_width
        y_offset = rank_idx * square_height

        origin_x = pos.x - x_offset
        origin_y = pos.y - y_offset

        board_cfg['origin_x_mm'] = origin_x
        board_cfg['origin_y_mm'] = origin_y

        self.settings.set_board(board_cfg)
        self.settings.save()

        self.board_cfg = self._cfg_to_board(board_cfg)
        self.move_planner = MovePlanner(self.board_cfg)

        self.editor_view._redraw_board()

        self._log(f"[CALIBRATE] ✓ Set {square} at X={pos.x:.2f}, Y={pos.y:.2f}")
        self._log(f"[CALIBRATE] ✓ Calculated A1 origin: X={origin_x:.2f}, Y={origin_y:.2f}")
        self.status.set(f"✓ Calibrated: {square} = ({pos.x:.2f}, {pos.y:.2f})")

        messagebox.showinfo(
            "Calibration Complete",
            f"Board successfully calibrated!\n\n"
            f"{square} center: X={pos.x:.2f}, Y={pos.y:.2f}\n"
            f"A1 origin: X={origin_x:.2f}, Y={origin_y:.2f}\n\n"
            f"You can now move to any square accurately."
        )

    def _redraw_board(self):
        """Redirect to editor's redraw method."""
        if hasattr(self, 'editor_view'):
            self.editor_view._redraw_board()

    def _update_square_highlight(self):
        """Redirect to editor's redraw method for square highlighting."""
        if hasattr(self, 'editor_view'):
            self.editor_view._redraw_board()

    def _board_square_from_xy(self, px: float, py: float) -> Optional[str]:
        """Not needed with editor-only interface."""
        return None

    def _on_click_board(self, ev):
        """Not needed with editor-only interface."""
        pass

        # Jog distance selector with modern radio buttons
        jog_label = tk.Label(
            control_content,
            text="Jog Distance:",
            font=("Segoe UI", 9),
            bg=self.theme['panel_bg'],
            fg=self.theme['text_secondary']
        )
        jog_label.pack(anchor="w", pady=(0, 5))

        jog_frame = tk.Frame(control_content, bg=self.theme['panel_bg'])
        jog_frame.pack(fill=tk.X, pady=(0, 10))

        self.jog_distance = tk.IntVar(value=10)
        for i, dist in enumerate([1, 10, 50, 100]):
            rb = tk.Radiobutton(
                jog_frame,
                text=f"{dist}mm",
                variable=self.jog_distance,
                value=dist,
                font=("Segoe UI", 9),
                bg=self.theme['panel_bg'],
                fg=self.theme['fg'],
                selectcolor=self.theme['input_bg'],
                activebackground=self.theme['panel_bg'],
                activeforeground=self.theme['accent'],
                cursor="hand2"
            )
            rb.pack(side=tk.LEFT, padx=(0, 15))

        # Modern arrow button grid
        arrow_container = tk.Frame(control_content, bg=self.theme['panel_bg'])
        arrow_container.pack(pady=10)

        def create_arrow_button(parent, direction, row, col, cmd):
            """Create an arrow-shaped button with sharp edges and wider body."""
            size = 70  # Canvas size

            canvas = tk.Canvas(
                parent,
                width=size,
                height=size,
                bg=self.theme['panel_bg'],
                highlightthickness=0,
                cursor="hand2"
            )
            canvas.grid(row=row, column=col, padx=2, pady=2)

            arrow_color = self.theme['button_bg']
            hover_color = self.theme['button_hover']

            # Wider arrow shapes with sharp points (no smoothing)
            if direction == 'up':
                # Point at top, wider shaft
                points = [35, 8, 62, 40, 50, 40, 50, 62, 20, 62, 20, 40, 8, 40]
            elif direction == 'down':
                # Point at bottom, wider shaft
                points = [35, 62, 8, 30, 20, 30, 20, 8, 50, 8, 50, 30, 62, 30]
            elif direction == 'left':
                # Point at left, wider shaft
                points = [8, 35, 40, 8, 40, 20, 62, 20, 62, 50, 40, 50, 40, 62]
            elif direction == 'right':
                # Point at right, wider shaft
                points = [62, 35, 30, 8, 30, 20, 8, 20, 8, 50, 30, 50, 30, 62]

            # Draw sharp arrow (smooth=False for sharp edges)
            arrow = canvas.create_polygon(points, fill=arrow_color, outline='', smooth=False)

            def on_enter(e):
                canvas.itemconfig(arrow, fill=hover_color)

            def on_leave(e):
                canvas.itemconfig(arrow, fill=arrow_color)

            def on_click(e):
                cmd()

            canvas.bind('<Enter>', on_enter)
            canvas.bind('<Leave>', on_leave)
            canvas.bind('<Button-1>', on_click)

            return canvas

        # Arrow buttons in cross pattern
        create_arrow_button(arrow_container, 'up', 0, 1, lambda: self._jog(0, 1))
        create_arrow_button(arrow_container, 'left', 1, 0, lambda: self._jog(-1, 0))

        # Home button (center) - house shape
        home_canvas = tk.Canvas(
            arrow_container,
            width=70,
            height=70,
            bg=self.theme['panel_bg'],
            highlightthickness=0,
            cursor="hand2"
        )
        home_canvas.grid(row=1, column=1, padx=2, pady=2)

        home_color = self.theme['warning']
        hover_color = "#d68910"

        # House shape with sharp edges
        # Roof triangle
        roof_points = [35, 12, 58, 35, 12, 35]
        # Base rectangle
        base_points = [15, 35, 55, 35, 55, 58, 15, 58]
        # Door
        door_points = [28, 45, 42, 45, 42, 58, 28, 58]

        home_roof = home_canvas.create_polygon(roof_points, fill=home_color, outline='', smooth=False)
        home_base = home_canvas.create_polygon(base_points, fill=home_color, outline='', smooth=False)
        home_door = home_canvas.create_polygon(door_points, fill='#2c3e50', outline='', smooth=False)

        def home_enter(e):
            home_canvas.itemconfig(home_roof, fill=hover_color)
            home_canvas.itemconfig(home_base, fill=hover_color)

        def home_leave(e):
            home_canvas.itemconfig(home_roof, fill=home_color)
            home_canvas.itemconfig(home_base, fill=home_color)

        def home_click(e):
            self._home()

        home_canvas.bind('<Enter>', home_enter)
        home_canvas.bind('<Leave>', home_leave)
        home_canvas.bind('<Button-1>', home_click)

        create_arrow_button(arrow_container, 'right', 1, 2, lambda: self._jog(1, 0))
        create_arrow_button(arrow_container, 'down', 2, 1, lambda: self._jog(0, -1))

        # Move to square - Modern input
        move_label = tk.Label(
            control_content,
            text="Move to Square:",
            font=("Segoe UI", 9),
            bg=self.theme['panel_bg'],
            fg=self.theme['text_secondary']
        )
        move_label.pack(anchor="w", pady=(15, 5))

        move_frame = tk.Frame(control_content, bg=self.theme['panel_bg'])
        move_frame.pack(fill=tk.X)

        self.square_entry = tk.Entry(
            move_frame,
            font=("Consolas", 11),
            bg=self.theme['input_bg'],
            fg=self.theme['input_fg'],
            relief=tk.FLAT,
            bd=0,
            width=6,
            insertbackground=self.theme['accent']
        )
        self.square_entry.pack(side=tk.LEFT, ipady=8, ipadx=10)

        go_btn = tk.Button(
            move_frame,
            text="Go →",
            font=("Segoe UI", 9, "bold"),
            bg=self.theme['accent'],
            fg="white",
            relief=tk.FLAT,
            bd=0,
            padx=20,
            pady=8,
            cursor="hand2",
            command=self._move_to_square,
            activebackground=self.theme['button_hover'],
            activeforeground="white"
        )
        go_btn.pack(side=tk.LEFT, padx=(10, 0))

        hint_label = tk.Label(
            control_content,
            text="e.g. E4, A1, H8",
            font=("Segoe UI", 8),
            bg=self.theme['panel_bg'],
            fg=self.theme['text_secondary']
        )
        hint_label.pack(anchor="w", pady=(3, 0))

        # Bind Enter key to move
        self.square_entry.bind("<Return>", lambda e: self._move_to_square())

        # Calibration section
        cal_label = tk.Label(
            control_content,
            text="Calibration:",
            font=("Segoe UI", 9),
            bg=self.theme['panel_bg'],
            fg=self.theme['text_secondary']
        )
        cal_label.pack(anchor="w", pady=(15, 5))

        cal_frame = tk.Frame(control_content, bg=self.theme['panel_bg'])
        cal_frame.pack(fill=tk.X)

        # Square entry for calibration
        self.cal_square_entry = tk.Entry(
            cal_frame,
            font=("Consolas", 11),
            bg=self.theme['input_bg'],
            fg=self.theme['input_fg'],
            relief=tk.FLAT,
            bd=0,
            width=6,
            insertbackground=self.theme['accent']
        )
        self.cal_square_entry.pack(side=tk.LEFT, ipady=8, ipadx=10)
        self.cal_square_entry.insert(0, "A1")  # Default to A1

        cal_btn = tk.Button(
            cal_frame,
            text="📍 Set Position",
            font=("Segoe UI", 9, "bold"),
            bg=self.theme['accent'],
            fg="white",
            relief=tk.FLAT,
            bd=0,
            padx=12,
            pady=8,
            cursor="hand2",
            command=self._calibrate_square,
            activebackground=self.theme['button_hover'],
            activeforeground="white"
        )
        cal_btn.pack(side=tk.LEFT, padx=(10, 0))

        cal_hint = tk.Label(
            control_content,
            text="Jog head to square center, enter square (e.g. A1, E4), click to calibrate",
            font=("Segoe UI", 8),
            bg=self.theme['panel_bg'],
            fg=self.theme['text_secondary']
        )
        cal_hint.pack(anchor="w", pady=(3, 0))

        # Bind Enter key to calibrate
        self.cal_square_entry.bind("<Return>", lambda e: self._calibrate_square())

        # Servo control panel - Modern design
        servo_frame = tk.Frame(right_panel, bg=self.theme["panel_bg"], relief=tk.FLAT)
        servo_frame.pack(fill=tk.X, pady=(0, 10))

        # Servo header (more compact)
        tk.Label(
            servo_frame,
            text="⚙ Servo Control",
            font=("Segoe UI", 10, "bold"),
            bg=self.theme["panel_bg"],
            fg=self.theme["fg"],
            anchor="w",
            padx=10,
            pady=5
        ).pack(fill=tk.X)

        servo_content = tk.Frame(servo_frame, bg=self.theme["panel_bg"])
        servo_content.pack(fill=tk.X, padx=10, pady=(0, 5))

        # Lift (Rack & Pinion) section
        lift_section = tk.Frame(servo_content, bg=self.theme["input_bg"], relief=tk.FLAT, bd=1)
        lift_section.pack(fill=tk.X, pady=(0,5))

        # Lift header with status
        lift_header = tk.Frame(lift_section, bg=self.theme["input_bg"])
        lift_header.pack(fill=tk.X, padx=10, pady=(5,3))

        tk.Label(
            lift_header,
            text="↕ LIFT",
            font=("Segoe UI", 10, "bold"),
            bg=self.theme["input_bg"],
            fg=self.theme["fg"]
        ).pack(side=tk.LEFT)

        self.lift_status = tk.StringVar(value="UP (180°)")
        self.lift_status_label = tk.Label(
            lift_header,
            textvariable=self.lift_status,
            font=("Consolas", 9, "bold"),
            bg="#27ae60",
            fg="white",
            padx=8,
            pady=2,
            relief=tk.RAISED,
            bd=1
        )
        self.lift_status_label.pack(side=tk.RIGHT)

        # Lift main buttons (centered, more compact)
        lift_main_frame = tk.Frame(lift_section, bg=self.theme["input_bg"])
        lift_main_frame.pack(pady=(0,5), padx=10)

        tk.Button(
            lift_main_frame,
            text="▲ UP",
            width=8,
            height=1,
            font=("Segoe UI", 8, "bold"),
            bg="#3498db",
            fg="white",
            activebackground="#2980b9",
            activeforeground="white",
            relief=tk.RAISED,
            bd=1,
            cursor="hand2",
            command=self._lift_up
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            lift_main_frame,
            text="■ MID",
            width=6,
            height=1,
            font=("Segoe UI", 8, "bold"),
            bg="#95a5a6",
            fg="white",
            activebackground="#7f8c8d",
            activeforeground="white",
            relief=tk.RAISED,
            bd=1,
            cursor="hand2",
            command=self._lift_mid
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            lift_main_frame,
            text="▼ DOWN",
            width=8,
            height=1,
            font=("Segoe UI", 8, "bold"),
            bg="#e74c3c",
            fg="white",
            activebackground="#c0392b",
            activeforeground="white",
            relief=tk.RAISED,
            bd=1,
            cursor="hand2",
            command=self._lift_down
        ).pack(side=tk.LEFT, padx=2)

        # Lift fine controls (more compact)
        lift_inc_frame = tk.Frame(lift_section, bg=self.theme["input_bg"])
        lift_inc_frame.pack(pady=(0,5), padx=10)

        tk.Button(
            lift_inc_frame,
            text="+ 5°",
            width=6,
            font=("Segoe UI", 7),
            bg="#bdc3c7",
            fg="#2c3e50",
            activebackground="#95a5a6",
            relief=tk.RAISED,
            bd=1,
            cursor="hand2",
            command=lambda: self._lift_increment(1)
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            lift_inc_frame,
            text="- 5°",
            width=6,
            font=("Segoe UI", 7),
            bg="#bdc3c7",
            fg="#2c3e50",
            activebackground="#95a5a6",
            relief=tk.RAISED,
            bd=1,
            cursor="hand2",
            command=lambda: self._lift_increment(-1)
        ).pack(side=tk.LEFT, padx=2)

        # Gripper section
        grip_section = tk.Frame(servo_content, bg=self.theme["input_bg"], relief=tk.FLAT, bd=1)
        grip_section.pack(fill=tk.X)

        # Gripper header with status
        grip_header = tk.Frame(grip_section, bg=self.theme["input_bg"])
        grip_header.pack(fill=tk.X, padx=10, pady=(5,3))

        tk.Label(
            grip_header,
            text="✋ GRIPPER",
            font=("Segoe UI", 10, "bold"),
            bg=self.theme["input_bg"],
            fg=self.theme["fg"]
        ).pack(side=tk.LEFT)

        self.grip_status = tk.StringVar(value="OPEN (0°)")
        self.grip_status_label = tk.Label(
            grip_header,
            textvariable=self.grip_status,
            font=("Consolas", 9, "bold"),
            bg="#27ae60",
            fg="white",
            padx=8,
            pady=2,
            relief=tk.RAISED,
            bd=1
        )
        self.grip_status_label.pack(side=tk.RIGHT)

        # Gripper main buttons (centered, more compact)
        grip_main_frame = tk.Frame(grip_section, bg=self.theme["input_bg"])
        grip_main_frame.pack(pady=(0,5), padx=10)

        tk.Button(
            grip_main_frame,
            text="◀ OPEN ▶",
            width=12,
            height=1,
            font=("Segoe UI", 8, "bold"),
            bg="#27ae60",
            fg="white",
            activebackground="#229954",
            activeforeground="white",
            relief=tk.RAISED,
            bd=1,
            cursor="hand2",
            command=self._grip_open
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            grip_main_frame,
            text="▶ CLOSE ◀",
            width=12,
            height=1,
            font=("Segoe UI", 8, "bold"),
            bg="#e67e22",
            fg="white",
            activebackground="#d35400",
            activeforeground="white",
            relief=tk.RAISED,
            bd=1,
            cursor="hand2",
            command=self._grip_close
        ).pack(side=tk.LEFT, padx=2)

        # Gripper fine controls (more compact)
        grip_inc_frame = tk.Frame(grip_section, bg=self.theme["input_bg"])
        grip_inc_frame.pack(pady=(0,5), padx=10)

        tk.Button(
            grip_inc_frame,
            text="+ 3° Close",
            width=8,
            font=("Segoe UI", 7),
            bg="#bdc3c7",
            fg="#2c3e50",
            activebackground="#95a5a6",
            relief=tk.RAISED,
            bd=1,
            cursor="hand2",
            command=lambda: self._grip_increment(1)
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            grip_inc_frame,
            text="- 3° Open",
            width=8,
            font=("Segoe UI", 7),
            bg="#bdc3c7",
            fg="#2c3e50",
            activebackground="#95a5a6",
            relief=tk.RAISED,
            bd=1,
            cursor="hand2",
            command=lambda: self._grip_increment(-1)
        ).pack(side=tk.LEFT, padx=2)

        # Command log (more compact)
        tk.Label(right_panel, text="📋 Command Log", font=("Segoe UI", 10, "bold"), bg=self.theme["bg"], fg=self.theme["fg"], anchor="w", padx=10, pady=5).pack(anchor="w", padx=6, pady=(5,2))
        self.txt_log = tk.Text(
            right_panel,
            height=8,
            bg=self.theme["input_bg"],
            fg=self.theme["input_fg"],
            font=("Consolas", 8),
            relief=tk.FLAT,
            bd=0,
            padx=8,
            pady=8,
            insertbackground=self.theme["accent"]
        )
        self.txt_log.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 8))

        # Status bar
        self.status = tk.StringVar(value="Disconnected")
        status_bar = tk.Frame(self, bg=self.theme["panel_bg"], height=30)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        status_bar.pack_propagate(False)

        stbar = tk.Label(
            status_bar,
            textvariable=self.status,
            anchor="w",
            bg=self.theme["panel_bg"],
            fg=self.theme["fg"],
            font=("Segoe UI", 9),
            padx=20,
            pady=5
        )
        stbar.pack(side=tk.BOTTOM, fill=tk.X)

        self._redraw_board()

    def _redraw_board(self):
        c = self.canvas
        c.delete("all")
        canvas_w = c.winfo_width()
        canvas_h = c.winfo_height()

        # Make board square - use smaller dimension
        # Reduce by 5% and leave margin for labels
        size = (min(canvas_w, canvas_h) * 0.95) - 50  # 5% smaller + more margin

        # Center the board
        offset_x = (canvas_w - size) / 2
        offset_y = (canvas_h - size) / 2

        files = self.board_cfg.files
        ranks = self.board_cfg.ranks
        sq_size = size / files  # Square size (same for width and height)

        # Draw squares
        light = self.theme["board_light"]
        dark = self.theme["board_dark"]
        for r in range(ranks):
            for f in range(files):
                x0 = offset_x + f * sq_size
                y0 = offset_y + (ranks - r - 1) * sq_size  # Flip Y for chess coords
                x1 = x0 + sq_size
                y1 = y0 + sq_size
                color = light if (r + f) % 2 == 0 else dark
                c.create_rectangle(x0, y0, x1, y1, fill=color, outline=self.theme["board_border"])

        # File/rank labels
        for f in range(files):
            label = chr(ord('A') + f)
            x = offset_x + (f + 0.5) * sq_size
            y = offset_y + size + 15
            c.create_text(x, y, text=label, fill=self.theme["text_secondary"], font=("Arial", 10))
        for r in range(ranks):
            label = str(r+1)
            x = offset_x - 15
            y = offset_y + (ranks - r - 0.5) * sq_size
            c.create_text(x, y, text=label, fill=self.theme["text_secondary"], font=("Arial", 10))

        # Highlight current gantry square
        if self.current_gantry_square:
            square = self.current_gantry_square
            # Parse square notation (e.g., "e4")
            file_char = square[0].lower()
            rank_char = square[1]
            file_idx = ord(file_char) - ord('a')
            rank_idx = int(rank_char) - 1

            # Calculate square position
            x0 = offset_x + file_idx * sq_size
            y0 = offset_y + (ranks - rank_idx - 1) * sq_size
            x1 = x0 + sq_size
            y1 = y0 + sq_size

            # Draw semi-transparent yellow overlay
            c.create_rectangle(
                x0, y0, x1, y1,
                fill='',
                outline='#FFD700',  # Gold color
                width=4,
                tags='gantry_highlight'
            )

            # Add crosshair at center
            center_x = x0 + sq_size / 2
            center_y = y0 + sq_size / 2
            crosshair_size = sq_size * 0.15

            # Horizontal line
            c.create_line(
                center_x - crosshair_size, center_y,
                center_x + crosshair_size, center_y,
                fill='#FFD700',
                width=3,
                tags='gantry_highlight'
            )

            # Vertical line
            c.create_line(
                center_x, center_y - crosshair_size,
                center_x, center_y + crosshair_size,
                fill='#FFD700',
                width=3,
                tags='gantry_highlight'
            )

    def _board_square_from_xy(self, px: float, py: float) -> Optional[str]:
        c = self.canvas
        canvas_w = c.winfo_width()
        canvas_h = c.winfo_height()

        # Calculate board dimensions (same as in _redraw_board)
        size = (min(canvas_w, canvas_h) * 0.95) - 50
        offset_x = (canvas_w - size) / 2
        offset_y = (canvas_h - size) / 2

        files = self.board_cfg.files
        ranks = self.board_cfg.ranks
        sq_size = size / files

        # Adjust click position for offset
        board_x = px - offset_x
        board_y = py - offset_y

        # Check if click is within board bounds
        if board_x < 0 or board_y < 0 or board_x >= size or board_y >= size:
            return None

        # Convert to file/rank
        f = int(board_x // sq_size)
        r = int((size - board_y) // sq_size)  # Flip Y

        if f < 0 or f >= files or r < 0 or r >= ranks:
            return None

        return f"{chr(ord('a')+f)}{r+1}"

    def _toggle_connection(self):
        """Toggle between connected and disconnected states."""
        if self.gantry._state == ConnectionState.CONNECTED:
            # Disconnect
            self.gantry.disconnect()
            self.status.set("Disconnected")
        else:
            # Connect
            ports = self._list_ports()
            ser_cfg = self.settings.get_serial()
            port = ser_cfg.get('port') or (ports[0] if ports else "")
            if not port:
                messagebox.showerror("No Port", "No serial ports found. Plug the machine in and try again.")
                return
            try:
                self.gantry.connect(port, ser_cfg.get('baudrate', 115200))
                self.status.set(f"Connected: {port}")
            except Exception as e:
                messagebox.showerror("Connect Failed", str(e))

    def _connect(self):
        """Legacy connect method - calls toggle."""
        if self.gantry._state != ConnectionState.CONNECTED:
            self._toggle_connection()

    def _disconnect(self):
        """Legacy disconnect method - calls toggle."""
        if self.gantry._state == ConnectionState.CONNECTED:
            self._toggle_connection()

    def _home(self):
        self.gantry.home()

    def _jog(self, x_dir: int, y_dir: int):
        """
        Manual jog movement with intelligent boundary limiting.
        x_dir: -1 (left), 0 (no change), +1 (right)
        y_dir: -1 (down), 0 (no change), +1 (up)
        """
        distance = self.jog_distance.get()
        feed = self.settings.get_board().get('feedrate_mm_min', 2000)

        # Get current position from GRBL
        self._log("[JOG] Querying current position...")
        current_pos = self.gantry.get_current_position_blocking(timeout=2.0)

        if current_pos is None:
            self._log("[JOG] Warning: Could not read position, moving without limits")
            # Fallback to original behavior if position unavailable
            x_delta = x_dir * distance
            y_delta = y_dir * distance
        else:
            # Get machine workspace limits (hard-coded, not affected by board calibration)
            limits = self.gantry.safety_limits
            max_x = limits.x_max
            max_y = limits.y_max
            min_x = limits.x_min
            min_y = limits.y_min

            # Calculate desired movement
            desired_x = current_pos.x + (x_dir * distance)
            desired_y = current_pos.y + (y_dir * distance)

            # Calculate actual movement (limited by boundaries)
            if x_dir > 0:  # Moving right
                actual_x = min(desired_x, max_x)
                x_delta = actual_x - current_pos.x
            elif x_dir < 0:  # Moving left
                actual_x = max(desired_x, min_x)
                x_delta = actual_x - current_pos.x
            else:
                x_delta = 0

            if y_dir > 0:  # Moving forward
                actual_y = min(desired_y, max_y)
                y_delta = actual_y - current_pos.y
            elif y_dir < 0:  # Moving back
                actual_y = max(desired_y, min_y)
                y_delta = actual_y - current_pos.y
            else:
                y_delta = 0

            # Log if movement was limited
            if abs(x_delta) < abs(x_dir * distance) or abs(y_delta) < abs(y_dir * distance):
                self._log(f"[JOG] Movement limited by boundaries (requested {distance}mm, moving {abs(x_delta if x_dir else y_delta):.1f}mm)")

        self._log(f"[JOG] Moving X{x_delta:+.1f} Y{y_delta:+.1f}mm")

        try:
            self.gantry.unlock()
            # Use relative positioning for jog
            self.gantry.send("G91")  # Relative mode
            self.gantry.send(f"G0 X{x_delta:.1f} Y{y_delta:.1f} F{feed}")
            self.gantry.send("G90")  # Back to absolute mode
        except Exception as e:
            self._log(f"[ERROR] Jog failed: {e}")
            messagebox.showerror("Jog Failed", str(e))

    def _move_to_square(self):
        """Move to a specific square by chess notation (e.g., E4, A1, H8)."""
        square = self.square_entry.get().strip().lower()

        if not square:
            return

        # Validate square format
        if len(square) != 2:
            messagebox.showerror("Invalid Square", "Enter a square like E4, A1, or H8")
            return

        file_char = square[0]
        rank_char = square[1]

        # Validate file (a-h)
        if file_char not in 'abcdefgh':
            messagebox.showerror("Invalid Square", "File must be A-H")
            return

        # Validate rank (1-8)
        if rank_char not in '12345678':
            messagebox.showerror("Invalid Square", "Rank must be 1-8")
            return

        # Calculate center coordinates
        try:
            x, y = self.board_cfg.square_center_xy(square)
            feed = self.settings.get_board().get('feedrate_mm_min', 2000)

            self._log(f"[MOVE] Going to square {square.upper()} → X{x:.2f} Y{y:.2f}")

            self.gantry.unlock()
            self.gantry.set_mm_absolute()
            self.gantry.rapid_to(x, y, feed)

            # Clear entry after successful move
            self.square_entry.delete(0, tk.END)

        except Exception as e:
            self._log(f"[ERROR] Move to {square.upper()} failed: {e}")
            messagebox.showerror("Move Failed", str(e))

    def _calibrate_square(self):
        """Calibrate board by setting current position as the center of any square."""
        square = self.cal_square_entry.get().strip().upper()

        if not square:
            messagebox.showerror("Invalid Input", "Please enter a square (e.g. A1, E4, H8)")
            return

        # Validate square format
        if len(square) != 2:
            messagebox.showerror("Invalid Square", "Enter a square like A1, E4, or H8")
            return

        file_char = square[0].lower()
        rank_char = square[1]

        # Validate file (a-h)
        if file_char not in 'abcdefgh':
            messagebox.showerror("Invalid Square", "File must be A-H")
            return

        # Validate rank (1-8)
        if rank_char not in '12345678':
            messagebox.showerror("Invalid Square", "Rank must be 1-8")
            return

        # Confirm with user
        result = messagebox.askyesno(
            "Calibrate Position",
            f"This will set the current gantry position as the center of square {square}.\n\n"
            f"Make sure the gantry head is positioned exactly over the center of {square}.\n\n"
            f"Continue?",
            icon='question'
        )

        if not result:
            return

        # Get current position
        self._log(f"[CALIBRATE] Requesting current position for {square}...")
        pos = self.gantry.get_current_position_blocking(timeout=3.0)

        if pos is None:
            messagebox.showerror(
                "Calibration Failed",
                "Could not read current position from GRBL.\n\n"
                "Make sure the machine is connected and try again."
            )
            return

        # Calculate what A1 origin should be based on this square's position
        # Convert square to file/rank indices
        file_idx = ord(file_char) - ord('a')  # 0-7
        rank_idx = int(rank_char) - 1  # 0-7

        # Get board dimensions
        board_cfg = self.settings.get_board()
        square_width = board_cfg['width_mm'] / board_cfg['files']
        square_height = board_cfg['height_mm'] / board_cfg['ranks']

        # Calculate offset from A1 to this square's center
        x_offset = file_idx * square_width
        y_offset = rank_idx * square_height

        # Calculate A1 origin (bottom-left corner offset by half square)
        origin_x = pos.x - x_offset
        origin_y = pos.y - y_offset

        # Update board configuration with calculated origin
        board_cfg['origin_x_mm'] = origin_x
        board_cfg['origin_y_mm'] = origin_y

        # Save settings
        self.settings.set_board(board_cfg)
        self.settings.save()

        # Update internal config
        self.board_cfg = self._cfg_to_board(board_cfg)
        self.move_planner = MovePlanner(self.board_cfg)

        # Redraw board
        self._redraw_board()

        # Notify user
        self._log(f"[CALIBRATE] ✓ Set {square} at X={pos.x:.2f}, Y={pos.y:.2f}")
        self._log(f"[CALIBRATE] ✓ Calculated A1 origin: X={origin_x:.2f}, Y={origin_y:.2f}")
        self.status.set(f"✓ Calibrated: {square} = ({pos.x:.2f}, {pos.y:.2f})")

        messagebox.showinfo(
            "Calibration Complete",
            f"Board successfully calibrated!\n\n"
            f"{square} center: X={pos.x:.2f}, Y={pos.y:.2f}\n"
            f"A1 origin: X={origin_x:.2f}, Y={origin_y:.2f}\n\n"
            f"You can now move to any square accurately."
        )

    def _calibrate_origin(self):
        """Legacy method - calls _calibrate_square with A1."""
        self.cal_square_entry.delete(0, tk.END)
        self.cal_square_entry.insert(0, "A1")
        self._calibrate_square()

    def _show_editor_view(self):
        """Show editor view (replaces main view)."""
        # Hide main view
        for widget in self.content_container.winfo_children():
            widget.pack_forget()

        # Create or show editor view
        if self.editor_view_frame is None:
            self.editor_view_frame = EditorWindow(
                self.content_container,
                self.board_state,
                self.board_cfg,
                on_send_to_machine=self._editor_send_to_machine,
                on_get_from_machine=self._editor_get_from_machine,
                on_auto_update=self._editor_auto_update,
                on_close=self._show_main_view
            )

        self.editor_view_frame.pack(fill=tk.BOTH, expand=True)
        self.current_view = 'editor'

    def _show_main_view(self):
        """Show main view (hides editor)."""
        # Hide editor view
        if self.editor_view_frame:
            self.editor_view_frame.pack_forget()

        # Show main view widgets again
        for widget in self.content_container.winfo_children():
            if widget != self.editor_view_frame:
                widget.pack(fill=tk.BOTH, expand=True)

        self.current_view = 'main'

    def _editor_send_to_machine(self, board_state: BoardState):
        """Handle 'Send to Machine' from editor."""
        # Mark virtual position as physical truth
        board_state.sync_physical_to_virtual()
        messagebox.showinfo(
            "Position Sent",
            "Virtual position marked as physical truth.\n\n"
            "The machine now knows where all pieces are located."
        )

    def _editor_get_from_machine(self, board_state: BoardState):
        """Handle 'Get from Machine' from editor."""
        # In the future, this could query actual sensor data
        # For now, we assume physical matches what we think it is
        messagebox.showinfo(
            "Get Position",
            "In a future version, this will query sensors to detect piece positions.\n\n"
            "For now, physical position is assumed to match the last known state."
        )

    def _editor_auto_update(self, board_state: BoardState, auto_mode: bool = True):
        """Handle 'Auto Update' from editor - move pieces to match virtual position."""
        to_add, to_remove, to_move = board_state.get_differences()

        if not (to_add or to_remove or to_move):
            messagebox.showinfo("Already Synced", "Positions already match!")
            return

        # Build move list summary
        total_changes = len(to_add) + len(to_remove) + len(to_move)
        msg = f"The machine will make {total_changes} adjustments:\n\n"

        if to_remove:
            msg += f"• Remove {len(to_remove)} piece(s)\n"
        if to_add:
            msg += f"• Add {len(to_add)} piece(s)\n"
        if to_move:
            msg += f"• Move/change {len(to_move)} piece(s)\n"

        if auto_mode:
            msg += "\n⚠️ This feature is not yet implemented.\n"
            msg += "The machine will need move planning logic to:\n"
            msg += "1. Identify which pieces to move\n"
            msg += "2. Plan collision-free paths\n"
            msg += "3. Execute moves in correct order"

            result = messagebox.showinfo("Auto Update", msg)

            # TODO: Implement actual move execution
            # For now, just mark as synced
            # board_state.sync_physical_to_virtual()
        else:
            messagebox.showinfo("Manual Update", msg)

    def _open_settings(self):
        ser_cfg = self.settings.get_serial()
        board_cfg = self.settings.get_board()
        safety_cfg = self.settings.get_safety()
        ports = self._list_ports()
        def on_save(new_board: dict, new_serial: dict, new_safety: dict):
            self.settings.set_board(new_board)
            self.settings.set_serial(new_serial)
            self.settings.set_safety(new_safety)
            self.settings.save()
            self.board_cfg = self._cfg_to_board(new_board)
            self.move_planner = MovePlanner(self.board_cfg)

            # Update gantry speed limits
            self.gantry.max_speed_mm_min = new_safety.get('max_speed_mm_min', 5000)
            self.gantry.min_speed_mm_min = new_safety.get('min_speed_mm_min', 100)
            self.gantry.enable_speed_limit = new_safety.get('enable_speed_limit', True)

            self._redraw_board()
            self.status.set("Settings saved.")
        SettingsWindow(self, board_cfg, ser_cfg, safety_cfg, ports, on_save, settings_obj=self.settings)

    def _test_path(self):
        # Corners and center test
        files, ranks = self.board_cfg.files, self.board_cfg.ranks
        path = [f"a1", f"{chr(ord('a')+files-1)}1", f"{chr(ord('a')+files-1)}{ranks}", f"a{ranks}", f"{chr(ord('a')+files//2)}{(ranks//2)+1}", "a1"]
        self._log(f"[TEST] Path: {' → '.join(path)}")
        self.gantry.unlock()
        self.gantry.set_mm_absolute()
        feed = self.settings.get_board().get('feedrate_mm_min', 2000)
        for sq in path:
            x, y = self.board_cfg.square_center_xy(sq)
            self.gantry.rapid_to(x, y, feed)

    def _on_click_board(self, ev):
        sq = self._board_square_from_xy(ev.x, ev.y)
        if not sq:
            return
        self._log(f"[UI] Clicked square {sq}")
        try:
            self.gantry.unlock()
            self.gantry.set_mm_absolute()
            feed = self.settings.get_board().get('feedrate_mm_min', 2000)
            x, y = self.board_cfg.square_center_xy(sq)
            self.gantry.rapid_to(x, y, feed)
        except Exception as e:
            messagebox.showerror("Move Failed", str(e))

    def _switch_profile(self):
        """Switch to a different profile."""
        new_profile_name = self.profile_var.get()
        current_profile = self.settings.get_active_profile_name()

        if new_profile_name == current_profile:
            return

        # Confirm switch
        result = messagebox.askyesno(
            "Switch Profile",
            f"Switch to profile '{new_profile_name}'?\n\n"
            f"This will reload board settings and calibration for that profile.",
            icon='question'
        )

        if not result:
            # Reset combo to current profile
            self.profile_var.set(current_profile)
            return

        # Set new active profile
        self.settings.set_active_profile_name(new_profile_name)
        self.settings.save()

        # Reload board configuration
        self.board_cfg = self._cfg_to_board(self.settings.get_board())
        self.move_planner = MovePlanner(self.board_cfg)

        # Redraw board
        self._redraw_board()

        # Update status
        self.status.set(f"✓ Profile switched to: {new_profile_name}")
        self._log(f"[PROFILE] Switched to: {new_profile_name}")

        messagebox.showinfo(
            "Profile Switched",
            f"Now using profile: {new_profile_name}\n\n"
            f"Board configuration has been reloaded."
        )

    def _list_ports(self):
        try:
            return self.gantry.list_ports()
        except Exception:
            return []

    def _log(self, msg: str):
        self.txt_log.insert(tk.END, msg + "\n")
        self.txt_log.see(tk.END)

    def _poll_grbl(self):
        line = self.gantry.read_line_nowait()
        if line:
            self._log(f"<< {line}")

        # Update connect button based on connection state
        if self.gantry._state == ConnectionState.CONNECTED:
            self.connect_btn.config(text="Disconnect", bg=self.theme['danger'])
        else:
            self.connect_btn.config(text="Connect", bg=self.theme['success'])

        self.after(50, self._poll_grbl)

    def _poll_servos(self):
        """Update servo status displays with color coding."""
        status = self.servos.get_status()
        lift_pos = status['lift_pos']
        lift_state = status['lift_state']
        grip_pos = status['grip_pos']
        grip_state = status['grip_state']

        # Update lift status with color coding
        self.lift_status.set(f"{lift_state} ({lift_pos}°)")
        if lift_state == "UP":
            self.lift_status_label.config(bg="#3498db", fg="white")  # Blue
        elif lift_state == "DOWN":
            self.lift_status_label.config(bg="#e74c3c", fg="white")  # Red
        else:  # MID
            self.lift_status_label.config(bg="#95a5a6", fg="white")  # Gray

        # Update gripper status with color coding
        self.grip_status.set(f"{grip_state} ({grip_pos}°)")
        if grip_state == "OPEN":
            self.grip_status_label.config(bg="#27ae60", fg="white")  # Green
        elif grip_state == "CLOSED":
            self.grip_status_label.config(bg="#e67e22", fg="white")  # Orange
        else:  # PARTIAL
            self.grip_status_label.config(bg="#f39c12", fg="white")  # Yellow-orange

        self.after(200, self._poll_servos)

    # ========== SERVO CONTROL METHODS ==========

    def _lift_up(self):
        """Raise lift to maximum height."""
        self.servos.lift_up()

    def _lift_down(self):
        """Lower lift to board level."""
        self.servos.lift_down()

    def _lift_mid(self):
        """Move lift to middle position."""
        self.servos.lift_mid()

    def _lift_increment(self, direction: int):
        """
        Move lift incrementally.
        direction: +1 for up, -1 for down
        """
        self.servos.lift_increment(direction)

    def _grip_open(self):
        """Open gripper fully."""
        self.servos.grip_open()

    def _grip_close(self):
        """Close gripper on piece."""
        self.servos.grip_close()

    def _grip_increment(self, direction: int):
        """
        Move gripper incrementally.
        direction: +1 for close, -1 for open
        """
        self.servos.grip_increment(direction)

    def _poll_position(self):
        """Poll gantry position and highlight the square it's hovering over."""
        # Only poll if connected
        if self.gantry._state == ConnectionState.CONNECTED:
            # Request status update to get latest position
            self.gantry.request_status()

            # Get cached position
            pos = self.gantry.get_position()

            if pos is not None:
                # Determine which square the gantry is over
                square = self._machine_coords_to_square(pos.x, pos.y)

                # Update highlight if square changed
                if square != self.current_gantry_square:
                    self.current_gantry_square = square
                    self._update_square_highlight()
        else:
            # Clear highlight when disconnected
            if self.current_gantry_square is not None:
                self.current_gantry_square = None
                self._update_square_highlight()

        # Poll every 250ms
        self.after(250, self._poll_position)

    def _machine_coords_to_square(self, x_mm: float, y_mm: float) -> Optional[str]:
        """
        Convert machine coordinates (mm) to chess square notation.
        Returns None if position is outside the board.
        """
        # Get board config
        board_cfg = self.settings.get_board()
        origin_x = board_cfg.get('origin_x_mm', 0.0)
        origin_y = board_cfg.get('origin_y_mm', 0.0)
        width_mm = board_cfg.get('width_mm', 400.0)
        height_mm = board_cfg.get('height_mm', 400.0)
        files = board_cfg.get('files', 8)
        ranks = board_cfg.get('ranks', 8)

        # Calculate relative position from origin
        rel_x = x_mm - origin_x
        rel_y = y_mm - origin_y

        # Check if within board bounds
        if rel_x < 0 or rel_y < 0 or rel_x > width_mm or rel_y > height_mm:
            return None

        # Calculate square indices
        square_width = width_mm / files
        square_height = height_mm / ranks

        file_idx = int(rel_x / square_width)
        rank_idx = int(rel_y / square_height)

        # Clamp to valid range
        file_idx = max(0, min(files - 1, file_idx))
        rank_idx = max(0, min(ranks - 1, rank_idx))

        # Convert to square notation
        return f"{chr(ord('a') + file_idx)}{rank_idx + 1}"

    def _update_square_highlight(self):
        """Redraw board with current square highlighted."""
        self._redraw_board()
