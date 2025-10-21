"""
Board Editor Window - Visual piece placement with physical/virtual tracking.

Allows users to:
- Place/remove pieces visually
- Track physical vs virtual positions
- Sync positions to/from the machine
- Update position automatically or manually
"""

import tkinter as tk
from tkinter import messagebox
from typing import Optional, Callable, Dict
from logic.board_state import BoardState, Piece, PieceType, PieceColor
from logic.board_map import BoardConfig, StorageLayout
from controllers.gantry_controller import GantryController
from controllers.servo_controller import ServoController
from PIL import Image, ImageTk
import io
import os


# Piece unicode symbols for display (fallback)
PIECE_SYMBOLS = {
    'wK': '♔', 'wQ': '♕', 'wR': '♖', 'wB': '♗', 'wN': '♘', 'wP': '♙',
    'bK': '♚', 'bQ': '♛', 'bR': '♜', 'bB': '♝', 'bN': '♞', 'bP': '♟'
}

# Global cache for piece images
_piece_image_cache: Dict[tuple, ImageTk.PhotoImage] = {}


def load_piece_svg(piece_code: str, size: int) -> Optional[ImageTk.PhotoImage]:
    """
    Load a piece image (PNG with transparency) and return as PhotoImage.
    Loads pre-rendered 128x128 PNG files and scales to requested size.
    Caches images by (piece_code, size) for performance.
    """
    cache_key = (piece_code, size)

    # Return cached image if available
    if cache_key in _piece_image_cache:
        return _piece_image_cache[cache_key]

    # Construct path to PNG file
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    png_path = os.path.join(project_root, 'assets', 'pieces', 'png', f'{piece_code}.png')

    if not os.path.exists(png_path):
        print(f"PNG file not found: {png_path}")
        return None

    try:
        # Load PNG with PIL (preserves alpha channel)
        img = Image.open(png_path).convert("RGBA")

        # Scale to requested size using high-quality resampling
        if img.size != (size, size):
            img = img.resize((size, size), Image.Resampling.LANCZOS)

        # Convert to PhotoImage
        photo = ImageTk.PhotoImage(img)

        # Cache it
        _piece_image_cache[cache_key] = photo

        return photo

    except Exception as e:
        print(f"Error loading piece image {piece_code}: {e}")
        import traceback
        traceback.print_exc()
        return None


class ToolTip:
    """Simple tooltip helper class for tkinter widgets."""

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self._show)
        self.widget.bind("<Leave>", self._hide)

    def _show(self, event=None):
        """Display the tooltip."""
        if self.tooltip_window or not self.text:
            return

        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5

        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            tw,
            text=self.text,
            justify=tk.LEFT,
            background="#2d2d2d",
            foreground="#e0e0e0",
            relief=tk.SOLID,
            borderwidth=1,
            font=("Segoe UI", 9),
            padx=8,
            pady=6
        )
        label.pack()

    def _hide(self, event=None):
        """Hide the tooltip."""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


class EditorWindow(tk.Frame):
    """Board editor frame for piece placement and position management."""

    def __init__(self, parent, board_state: BoardState, board_cfg: BoardConfig,
                 gantry: GantryController, servos: ServoController,
                 on_send_to_machine: Optional[Callable] = None,
                 on_get_from_machine: Optional[Callable] = None,
                 on_auto_update: Optional[Callable] = None,
                 on_move_to_square: Optional[Callable] = None,
                 on_calibrate: Optional[Callable] = None,
                 on_jog: Optional[Callable] = None,
                 on_home: Optional[Callable] = None):
        super().__init__(parent)

        self.board_state = board_state
        self.board_cfg = board_cfg
        self.gantry = gantry
        self.servos = servos
        self.selected_piece = None  # Currently selected piece to place
        self.board_orientation = 'white'  # 'white' or 'black'
        self.highlight_occupied_storage = False  # Toggle for storage square occupied highlighting

        # Get machine workspace dimensions from gantry
        self.workspace_width_mm = gantry.safety_limits.x_max - gantry.safety_limits.x_min
        self.workspace_height_mm = gantry.safety_limits.y_max - gantry.safety_limits.y_min

        # Undo stack for board edits
        self.undo_stack = []  # List of (square, piece_or_none) tuples

        # Keep references to piece images to prevent garbage collection
        self.piece_images = []
        self.button_images = []  # Piece picker button images

        # Callbacks for machine interaction
        self.on_send_to_machine = on_send_to_machine
        self.on_get_from_machine = on_get_from_machine
        self.on_auto_update = on_auto_update
        self.on_move_to_square = on_move_to_square
        self.on_calibrate = on_calibrate
        self.on_jog = on_jog
        self.on_home = on_home

        # Theme colors
        self.theme = {
            'bg': '#1e1e1e',
            'panel_bg': '#252525',
            'canvas_bg': '#2d2d2d',
            'input_bg': '#3a3a3a',
            'accent': '#3498db',
            'success': '#27ae60',
            'warning': '#f39c12',
            'danger': '#e74c3c',
            'board_light': '#ebecd0',
            'board_dark': '#779556',
            'fg': '#e0e0e0',
            'text_secondary': '#95a5a6',
        }

        self.configure(bg=self.theme['bg'])
        self._build_ui()

    def _build_ui(self):
        """Build the unified UI with editor and machine controls."""

        # Main container using grid for better control
        container = tk.Frame(self, bg=self.theme['bg'])
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Configure grid weights for responsive layout
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=0)  # Left panel - fixed width
        container.grid_columnconfigure(1, weight=1)  # Center panel - expandable
        container.grid_columnconfigure(2, weight=0)  # Right panel - fixed width

        # Left panel - Piece palette
        left_panel = tk.Frame(container, bg=self.theme['panel_bg'], width=150)
        left_panel.grid(row=0, column=0, sticky="ns", padx=(0, 10))
        left_panel.grid_propagate(False)

        tk.Label(
            left_panel,
            text="Piece Palette",
            font=("Segoe UI", 11, "bold"),
            bg=self.theme['panel_bg'],
            fg=self.theme['accent']
        ).pack(pady=10)

        # White pieces - 2 column grid layout with dark background for contrast
        tk.Label(
            left_panel,
            text="White Pieces",
            font=("Segoe UI", 9),
            bg=self.theme['panel_bg'],
            fg=self.theme['text_secondary']
        ).pack(pady=(10, 5))

        # Dark container for white pieces (for contrast)
        white_container = tk.Frame(left_panel, bg="#0e0e10", relief=tk.FLAT, bd=1)
        white_container.pack(padx=5, pady=(0, 10), fill=tk.X)

        white_pieces_frame = tk.Frame(white_container, bg="#0e0e10")
        white_pieces_frame.pack(padx=8, pady=8)

        white_pieces = [
            ('wK', '♔'), ('wQ', '♕'), ('wR', '♖'),
            ('wB', '♗'), ('wN', '♘'), ('wP', '♙')
        ]

        for idx, (piece_code, symbol) in enumerate(white_pieces):
            row = idx // 2
            col = idx % 2
            self._create_piece_button_grid(white_pieces_frame, piece_code, symbol, row, col)

        # Black pieces - 2 column grid layout with light background for contrast
        tk.Label(
            left_panel,
            text="Black Pieces",
            font=("Segoe UI", 9),
            bg=self.theme['panel_bg'],
            fg=self.theme['text_secondary']
        ).pack(pady=(10, 5))

        # Light container for black pieces (for contrast)
        black_container = tk.Frame(left_panel, bg="#f3f3f3", relief=tk.FLAT, bd=1)
        black_container.pack(padx=5, pady=(0, 10), fill=tk.X)

        black_pieces_frame = tk.Frame(black_container, bg="#f3f3f3")
        black_pieces_frame.pack(padx=8, pady=8)

        black_pieces = [
            ('bK', '♚'), ('bQ', '♛'), ('bR', '♜'),
            ('bB', '♝'), ('bN', '♞'), ('bP', '♟')
        ]

        for idx, (piece_code, symbol) in enumerate(black_pieces):
            row = idx // 2
            col = idx % 2
            self._create_piece_button_grid(black_pieces_frame, piece_code, symbol, row, col)

        # Delete button - full width
        tk.Label(
            left_panel,
            text="Tools",
            font=("Segoe UI", 9),
            bg=self.theme['panel_bg'],
            fg=self.theme['text_secondary']
        ).pack(pady=(20, 5))

        delete_btn = tk.Button(
            left_panel,
            text="🗑️ Delete",
            font=("Segoe UI", 9),
            bg=self.theme['danger'],
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=lambda: self._select_piece('delete')
        )
        delete_btn.pack(pady=5, padx=10, fill=tk.X)

        # Center panel - Chess board on left, machine controls on right
        center_panel = tk.Frame(container, bg=self.theme['bg'])
        center_panel.grid(row=0, column=1, sticky="nsew", padx=(0, 10))

        # Configure center panel grid - side by side layout
        center_panel.grid_rowconfigure(0, weight=1)
        center_panel.grid_columnconfigure(0, weight=1)  # Board - expandable
        center_panel.grid_columnconfigure(1, weight=0)  # Machine controls - fixed width

        # Board container - bigger now!
        board_container = tk.Frame(center_panel, bg=self.theme['canvas_bg'])
        board_container.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # Board canvas - larger dimensions
        self.canvas = tk.Canvas(
            board_container,
            bg=self.theme['canvas_bg'],
            highlightthickness=0,
            width=700,
            height=700
        )
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.canvas.bind("<Button-1>", self._on_square_click)
        self.canvas.bind("<Configure>", lambda e: self._redraw_board())

        # Machine controls to the right of board (vertical stack)
        machine_panel = tk.Frame(center_panel, bg=self.theme['panel_bg'], width=200)
        machine_panel.grid(row=0, column=1, sticky="ns")
        machine_panel.grid_propagate(False)

        # Title for machine controls
        tk.Label(
            machine_panel,
            text="Machine Control",
            font=("Segoe UI", 10, "bold"),
            bg=self.theme['panel_bg'],
            fg=self.theme['accent']
        ).pack(pady=(10, 10))

        # Manual Jog section
        jog_frame = tk.Frame(machine_panel, bg=self.theme['panel_bg'])
        jog_frame.pack(fill=tk.X, padx=10, pady=(0, 15))

        tk.Label(
            jog_frame,
            text="Jog",
            font=("Segoe UI", 9, "bold"),
            bg=self.theme['panel_bg'],
            fg=self.theme['fg']
        ).pack(anchor="w", pady=(0, 5))

        # Jog distance selector - more compact
        self.jog_distance = tk.IntVar(value=10)
        jog_dist_frame = tk.Frame(jog_frame, bg=self.theme['panel_bg'])
        jog_dist_frame.pack(fill=tk.X, pady=(0, 5))

        for dist in [1, 10, 50, 100]:
            rb = tk.Radiobutton(
                jog_dist_frame,
                text=f"{dist}",
                variable=self.jog_distance,
                value=dist,
                font=("Segoe UI", 7),
                bg=self.theme['panel_bg'],
                fg=self.theme['fg'],
                selectcolor=self.theme['input_bg'],
                activebackground=self.theme['panel_bg'],
                activeforeground=self.theme['accent'],
                cursor="hand2"
            )
            rb.pack(side=tk.LEFT, padx=1, expand=True)

        # Arrow buttons
        arrow_container = tk.Frame(jog_frame, bg=self.theme['panel_bg'])
        arrow_container.pack(pady=5)

        def create_arrow_btn(parent, text, row, col, cmd):
            btn = tk.Button(
                parent,
                text=text,
                font=("Segoe UI", 10, "bold"),
                width=3,
                height=1,
                bg=self.theme['accent'],
                fg="white",
                relief=tk.FLAT,
                cursor="hand2",
                command=cmd
            )
            btn.grid(row=row, column=col, padx=2, pady=2)
            return btn

        up_btn = create_arrow_btn(arrow_container, "▲", 0, 1, lambda: self._handle_jog(0, 1))
        left_btn = create_arrow_btn(arrow_container, "◄", 1, 0, lambda: self._handle_jog(-1, 0))

        # Home button
        home_btn = tk.Button(
            arrow_container,
            text="⌂",
            font=("Segoe UI", 12, "bold"),
            width=3,
            height=1,
            bg=self.theme['warning'],
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self._handle_home
        )
        home_btn.grid(row=1, column=1, padx=2, pady=2)
        self._create_tooltip(home_btn, "Return machine to home position (X=0, Y=0)")

        right_btn = create_arrow_btn(arrow_container, "►", 1, 2, lambda: self._handle_jog(1, 0))
        down_btn = create_arrow_btn(arrow_container, "▼", 2, 1, lambda: self._handle_jog(0, -1))

        self._create_tooltip(up_btn, "Jog machine forward (Y+)")
        self._create_tooltip(left_btn, "Jog machine left (X-)")
        self._create_tooltip(right_btn, "Jog machine right (X+)")
        self._create_tooltip(down_btn, "Jog machine backward (Y-)")

        # Move to Square section
        move_section = tk.Frame(machine_panel, bg=self.theme['panel_bg'])
        move_section.pack(fill=tk.X, padx=10, pady=(0, 15))

        tk.Label(
            move_section,
            text="Move to Square",
            font=("Segoe UI", 9, "bold"),
            bg=self.theme['panel_bg'],
            fg=self.theme['fg']
        ).pack(anchor="w", pady=(0, 5))

        move_frame = tk.Frame(move_section, bg=self.theme['panel_bg'])
        move_frame.pack(fill=tk.X)

        self.square_entry = tk.Entry(
            move_frame,
            font=("Consolas", 10),
            bg=self.theme['input_bg'],
            fg=self.theme['fg'],
            relief=tk.FLAT,
            bd=0,
            width=6
        )
        self.square_entry.pack(side=tk.LEFT, ipady=4, ipadx=6)
        self.square_entry.bind("<Return>", lambda e: self._handle_move_to_square())
        self._create_tooltip(self.square_entry, "Enter square (e.g., E4)")

        move_go_btn = tk.Button(
            move_frame,
            text="Go",
            font=("Segoe UI", 9, "bold"),
            bg=self.theme['accent'],
            fg="white",
            relief=tk.FLAT,
            bd=0,
            padx=12,
            pady=4,
            cursor="hand2",
            command=self._handle_move_to_square
        )
        move_go_btn.pack(side=tk.LEFT, padx=(6, 0))

        # Calibration section
        cal_section = tk.Frame(machine_panel, bg=self.theme['panel_bg'])
        cal_section.pack(fill=tk.X, padx=10, pady=(0, 15))

        tk.Label(
            cal_section,
            text="Calibration",
            font=("Segoe UI", 9, "bold"),
            bg=self.theme['panel_bg'],
            fg=self.theme['fg']
        ).pack(anchor="w", pady=(0, 5))

        cal_frame = tk.Frame(cal_section, bg=self.theme['panel_bg'])
        cal_frame.pack(fill=tk.X)

        self.cal_square_entry = tk.Entry(
            cal_frame,
            font=("Consolas", 10),
            bg=self.theme['input_bg'],
            fg=self.theme['fg'],
            relief=tk.FLAT,
            bd=0,
            width=6
        )
        self.cal_square_entry.pack(side=tk.LEFT, ipady=4, ipadx=6)
        self.cal_square_entry.insert(0, "A1")
        self.cal_square_entry.bind("<Return>", lambda e: self._handle_calibrate())
        self._create_tooltip(self.cal_square_entry, "Square machine is over")

        cal_set_btn = tk.Button(
            cal_frame,
            text="Set",
            font=("Segoe UI", 9, "bold"),
            bg=self.theme['accent'],
            fg="white",
            relief=tk.FLAT,
            bd=0,
            padx=12,
            pady=4,
            cursor="hand2",
            command=self._handle_calibrate
        )
        cal_set_btn.pack(side=tk.LEFT, padx=(6, 0))

        # Servos section
        servo_section = tk.Frame(machine_panel, bg=self.theme['panel_bg'])
        servo_section.pack(fill=tk.X, padx=10, pady=(0, 10))

        tk.Label(
            servo_section,
            text="Servos",
            font=("Segoe UI", 9, "bold"),
            bg=self.theme['panel_bg'],
            fg=self.theme['fg']
        ).pack(anchor="w", pady=(0, 5))

        # Lift controls
        lift_container = tk.Frame(servo_section, bg=self.theme['panel_bg'])
        lift_container.pack(fill=tk.X, pady=(0, 5))

        tk.Label(
            lift_container,
            text="Lift:",
            font=("Segoe UI", 8),
            bg=self.theme['panel_bg'],
            fg=self.theme['text_secondary']
        ).pack(side=tk.LEFT, padx=(0, 5))

        lift_up_btn = tk.Button(
            lift_container,
            text="▲",
            width=3,
            font=("Segoe UI", 8),
            bg="#3498db",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self._lift_up
        )
        lift_up_btn.pack(side=tk.LEFT, padx=1)
        self._create_tooltip(lift_up_btn, "Lift UP")

        lift_mid_btn = tk.Button(
            lift_container,
            text="■",
            width=3,
            font=("Segoe UI", 8),
            bg="#95a5a6",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self._lift_mid
        )
        lift_mid_btn.pack(side=tk.LEFT, padx=1)
        self._create_tooltip(lift_mid_btn, "Lift MID")

        lift_down_btn = tk.Button(
            lift_container,
            text="▼",
            width=3,
            font=("Segoe UI", 8),
            bg="#e74c3c",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self._lift_down
        )
        lift_down_btn.pack(side=tk.LEFT, padx=1)
        self._create_tooltip(lift_down_btn, "Lift DOWN")

        # Gripper controls
        grip_container = tk.Frame(servo_section, bg=self.theme['panel_bg'])
        grip_container.pack(fill=tk.X)

        tk.Label(
            grip_container,
            text="Gripper:",
            font=("Segoe UI", 8),
            bg=self.theme['panel_bg'],
            fg=self.theme['text_secondary']
        ).pack(side=tk.LEFT, padx=(0, 5))

        grip_open_btn = tk.Button(
            grip_container,
            text="OPEN",
            width=5,
            font=("Segoe UI", 8),
            bg="#27ae60",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self._grip_open
        )
        grip_open_btn.pack(side=tk.LEFT, padx=1)
        self._create_tooltip(grip_open_btn, "Open gripper")

        grip_close_btn = tk.Button(
            grip_container,
            text="CLOSE",
            width=5,
            font=("Segoe UI", 8),
            bg="#e67e22",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self._grip_close
        )
        grip_close_btn.pack(side=tk.LEFT, padx=1)
        self._create_tooltip(grip_close_btn, "Close gripper")

        # Right panel - Settings and Sync Controls
        right_panel = tk.Frame(container, bg=self.theme['panel_bg'], width=280)
        right_panel.grid(row=0, column=2, sticky="ns")
        right_panel.grid_propagate(False)

        # === BOARD SETUP SECTION ===
        tk.Label(
            right_panel,
            text="Board Setup",
            font=("Segoe UI", 11, "bold"),
            bg=self.theme['panel_bg'],
            fg=self.theme['accent']
        ).pack(pady=10)

        # Quick setup buttons
        setup_frame = tk.Frame(right_panel, bg=self.theme['panel_bg'])
        setup_frame.pack(fill=tk.X, padx=10, pady=5)

        start_pos_btn = tk.Button(
            setup_frame,
            text="Starting Position",
            font=("Segoe UI", 9),
            bg=self.theme['input_bg'],
            fg=self.theme['fg'],
            relief=tk.FLAT,
            cursor="hand2",
            command=self._set_starting_position
        )
        start_pos_btn.pack(fill=tk.X, pady=2)
        self._create_tooltip(start_pos_btn, "Set up the standard chess starting position")

        clear_btn = tk.Button(
            setup_frame,
            text="Clear Board",
            font=("Segoe UI", 9),
            bg=self.theme['input_bg'],
            fg=self.theme['fg'],
            relief=tk.FLAT,
            cursor="hand2",
            command=self._clear_board
        )
        clear_btn.pack(fill=tk.X, pady=2)
        self._create_tooltip(clear_btn, "Remove all pieces from the board")

        flip_btn = tk.Button(
            setup_frame,
            text="Flip Board",
            font=("Segoe UI", 9),
            bg=self.theme['input_bg'],
            fg=self.theme['fg'],
            relief=tk.FLAT,
            cursor="hand2",
            command=self._flip_board
        )
        flip_btn.pack(fill=tk.X, pady=2)
        self._create_tooltip(flip_btn, "Flip the board view (rotate 180°)")

        # Storage Square Highlighting Toggle
        self.storage_highlight_btn = tk.Button(
            setup_frame,
            text="◻ Show Occupied Storage",
            font=("Segoe UI", 9),
            bg=self.theme['input_bg'],
            fg=self.theme['fg'],
            relief=tk.FLAT,
            cursor="hand2",
            command=self._toggle_storage_highlight
        )
        self.storage_highlight_btn.pack(fill=tk.X, pady=2)
        self._create_tooltip(self.storage_highlight_btn, "Highlight occupied storage squares with darker color")

        self.undo_btn = tk.Button(
            setup_frame,
            text="↶ Undo",
            font=("Segoe UI", 9),
            bg=self.theme['input_bg'],
            fg=self.theme['fg'],
            relief=tk.FLAT,
            cursor="hand2",
            command=self._undo_last_edit,
            state=tk.DISABLED
        )
        self.undo_btn.pack(fill=tk.X, pady=2)
        self._create_tooltip(self.undo_btn, "Undo the last piece placement or removal")

        # === PHYSICAL ↔ VIRTUAL SYNC SECTION ===
        tk.Label(
            right_panel,
            text="Physical ↔ Virtual Sync",
            font=("Segoe UI", 11, "bold"),
            bg=self.theme['panel_bg'],
            fg=self.theme['accent']
        ).pack(pady=(20, 5))

        # Help text explaining the workflow
        help_text = (
            "Virtual = what you see on screen\n"
            "Physical = real pieces on the board"
        )
        tk.Label(
            right_panel,
            text=help_text,
            font=("Segoe UI", 8),
            bg=self.theme['panel_bg'],
            fg=self.theme['text_secondary'],
            justify=tk.LEFT
        ).pack(pady=(0, 10), padx=10)

        # Sync status indicator
        self.sync_status_label = tk.Label(
            right_panel,
            text="● Synced" if self.board_state.is_synced() else "● Out of Sync",
            font=("Segoe UI", 9),
            bg=self.theme['success'] if self.board_state.is_synced() else self.theme['warning'],
            fg="white",
            padx=10,
            pady=5
        )
        self.sync_status_label.pack(pady=5)

        sync_frame = tk.Frame(right_panel, bg=self.theme['panel_bg'])
        sync_frame.pack(fill=tk.X, padx=10, pady=5)

        # Renamed button: Physical matches Virtual
        self.send_btn = tk.Button(
            sync_frame,
            text="✓ Physical Matches Virtual",
            font=("Segoe UI", 9),
            bg=self.theme['success'],
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self._send_to_machine
        )
        self.send_btn.pack(fill=tk.X, pady=2)
        self._create_tooltip(self.send_btn, "Click AFTER you've manually arranged the physical board to match the screen")

        # Renamed button: Move Pieces Automatically
        self.auto_btn = tk.Button(
            sync_frame,
            text="🤖 Move Pieces Automatically",
            font=("Segoe UI", 9),
            bg=self.theme['accent'],
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self._auto_update_position
        )
        self.auto_btn.pack(fill=tk.X, pady=2)
        self._create_tooltip(self.auto_btn, "Machine will automatically move pieces on the physical board to match the screen")

        # Renamed button: Show Move Instructions
        self.manual_btn = tk.Button(
            sync_frame,
            text="📋 Show Move Instructions",
            font=("Segoe UI", 9),
            bg=self.theme['warning'],
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self._manual_update_position
        )
        self.manual_btn.pack(fill=tk.X, pady=2)
        self._create_tooltip(self.manual_btn, "Get a list of moves to make manually on the physical board")

        # === FEN IMPORT/EXPORT SECTION ===
        tk.Label(
            right_panel,
            text="FEN Import/Export",
            font=("Segoe UI", 10, "bold"),
            bg=self.theme['panel_bg'],
            fg=self.theme['fg']
        ).pack(pady=(20, 5))

        fen_frame = tk.Frame(right_panel, bg=self.theme['panel_bg'])
        fen_frame.pack(fill=tk.X, padx=10, pady=5)

        self.fen_entry = tk.Entry(
            fen_frame,
            font=("Consolas", 8),
            bg=self.theme['input_bg'],
            fg=self.theme['fg'],
            relief=tk.FLAT,
            bd=0
        )
        self.fen_entry.pack(fill=tk.X, pady=2, ipady=5, ipadx=5)

        load_fen_btn = tk.Button(
            fen_frame,
            text="Load FEN",
            font=("Segoe UI", 9),
            bg=self.theme['input_bg'],
            fg=self.theme['fg'],
            relief=tk.FLAT,
            cursor="hand2",
            command=self._load_fen
        )
        load_fen_btn.pack(fill=tk.X, pady=2)
        self._create_tooltip(load_fen_btn, "Load a chess position from FEN notation above")

        copy_fen_btn = tk.Button(
            fen_frame,
            text="Copy FEN",
            font=("Segoe UI", 9),
            bg=self.theme['input_bg'],
            fg=self.theme['fg'],
            relief=tk.FLAT,
            cursor="hand2",
            command=self._copy_fen
        )
        copy_fen_btn.pack(fill=tk.X, pady=2)
        self._create_tooltip(copy_fen_btn, "Copy current position as FEN notation to clipboard")

        # Add TacticsQuest logo (small, bottom-right)
        logo_frame = tk.Frame(right_panel, bg=self.theme['panel_bg'])
        logo_frame.pack(side=tk.BOTTOM, pady=10)

        try:
            logo_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'assets', 'logos', 'tacticsquest_logo.png'
            )
            if os.path.exists(logo_path):
                logo_img = Image.open(logo_path).convert("RGBA")
                # Resize to small (40x40 pixels)
                logo_img = logo_img.resize((40, 40), Image.Resampling.LANCZOS)
                logo_photo = ImageTk.PhotoImage(logo_img)
                # Keep reference to prevent garbage collection
                self.logo_image = logo_photo

                logo_label = tk.Label(
                    logo_frame,
                    image=logo_photo,
                    bg=self.theme['panel_bg'],
                    cursor="hand2"
                )
                logo_label.pack()
                self._create_tooltip(logo_label, "Powered by TacticsQuest")
        except Exception as e:
            # Silently fail if logo not found
            pass

        # Done building UI - draw initial board
        self._redraw_board()
        self._update_fen_display()

    def _create_tooltip(self, widget, text):
        """Create a tooltip for a widget."""
        return ToolTip(widget, text)

    def _create_piece_button(self, parent, piece_code: str, symbol: str):
        """Create a piece selection button (pack layout)."""
        btn = tk.Button(
            parent,
            text=symbol,
            font=("Segoe UI", 20),
            bg=self.theme['input_bg'],
            fg=self.theme['fg'],
            relief=tk.FLAT,
            cursor="hand2",
            command=lambda: self._select_piece(piece_code)
        )
        btn.pack(pady=2, padx=10, fill=tk.X)

    def _create_piece_button_grid(self, parent, piece_code: str, symbol: str, row: int, col: int):
        """Create a piece selection button in grid layout with SVG image."""
        # Determine background color based on piece color
        # White pieces on dark background, black pieces on light background
        is_white_piece = piece_code[0] == 'w'
        bg_color = "#0e0e10" if is_white_piece else "#f3f3f3"
        hover_color = "#1a1a1c" if is_white_piece else "#e5e5e5"

        # Try to load PNG image for the piece
        piece_img = load_piece_svg(piece_code, 50)  # 50px size for buttons

        if piece_img:
            # Keep reference to prevent garbage collection
            self.button_images.append(piece_img)

            # Create button with image (transparent background)
            btn = tk.Button(
                parent,
                image=piece_img,
                bg=bg_color,
                activebackground=hover_color,
                relief=tk.FLAT,
                cursor="hand2",
                width=60,
                height=60,
                bd=0,
                highlightthickness=0,
                command=lambda: self._select_piece(piece_code)
            )
        else:
            # Fallback to Unicode text if PNG fails
            btn = tk.Button(
                parent,
                text=symbol,
                font=("Segoe UI", 18),
                bg=bg_color,
                fg="#ffffff" if is_white_piece else "#000000",
                relief=tk.FLAT,
                cursor="hand2",
                width=3,
                height=1,
                command=lambda: self._select_piece(piece_code)
            )

        btn.grid(row=row, column=col, padx=2, pady=2, sticky="ew")

    def _select_piece(self, piece_code: str):
        """Select a piece for placement."""
        self.selected_piece = piece_code
        # Visual feedback could be added here

    def _get_piece_counts(self, color: PieceColor) -> Dict[PieceType, int]:
        """Count how many pieces of each type are on the board for a given color."""
        counts = {
            PieceType.KING: 0,
            PieceType.QUEEN: 0,
            PieceType.ROOK: 0,
            PieceType.BISHOP: 0,
            PieceType.KNIGHT: 0,
            PieceType.PAWN: 0
        }

        # Count pieces on the virtual board across all squares
        files = self.board_cfg.files
        ranks = self.board_cfg.ranks

        for file_idx in range(files):
            for rank_idx in range(ranks):
                square = f"{chr(ord('a') + file_idx)}{rank_idx + 1}"
                piece = self.board_state.get_piece_virtual(square)
                if piece and piece.color == color:
                    counts[piece.type] += 1

        return counts

    def _can_place_piece(self, piece_type: PieceType, color: PieceColor) -> tuple[bool, str]:
        """
        Check if a piece can be placed based on maximum allowed counts.
        Returns (can_place, error_message).

        Standard chess piece limits:
        - King: 1
        - Queen: 2 (1 original + 1 from promotion)
        - Rook: 2
        - Bishop: 2
        - Knight: 2
        - Pawn: 8
        """
        max_counts = {
            PieceType.KING: 1,
            PieceType.QUEEN: 2,  # Allow 1 extra queen for pawn promotion
            PieceType.ROOK: 2,
            PieceType.BISHOP: 2,
            PieceType.KNIGHT: 2,
            PieceType.PAWN: 8
        }

        current_counts = self._get_piece_counts(color)
        current_count = current_counts[piece_type]
        max_count = max_counts[piece_type]

        if current_count >= max_count:
            color_name = "White" if color == PieceColor.WHITE else "Black"
            piece_name = piece_type.value.capitalize()

            if piece_type == PieceType.QUEEN and max_count == 2:
                return False, f"{color_name} already has {current_count} {piece_name}s (max {max_count}: 1 original + 1 from promotion)"
            else:
                return False, f"{color_name} already has {current_count} {piece_name}s (max {max_count})"

        return True, ""

    def _on_square_click(self, event):
        """Handle click on board square."""
        if not self.selected_piece:
            return

        square = self._get_square_from_coords(event.x, event.y)
        if not square:
            return

        # Get what's currently on this square
        old_piece = self.board_state.get_piece_virtual(square)

        if self.selected_piece == 'delete':
            # Always allow deletion
            self.undo_stack.append((square, old_piece))
            if len(self.undo_stack) > 50:
                self.undo_stack.pop(0)

            self.board_state.set_piece_virtual(square, None)

            if hasattr(self, 'undo_btn'):
                self.undo_btn.config(state=tk.NORMAL)

            self._redraw_board()
            self._update_sync_status()
            self._update_fen_display()
            return

        # Placing a piece
        color = PieceColor.WHITE if self.selected_piece[0] == 'w' else PieceColor.BLACK
        piece_type = PieceType(self.selected_piece[1].lower())

        # If replacing a piece of the same type and color, just ignore (no-op)
        if old_piece and old_piece.type == piece_type and old_piece.color == color:
            return

        # Check if we can place this piece (only if adding new or replacing with different type)
        # If replacing, we need to check if we'd exceed limits after removing the old piece
        if old_piece and old_piece.type == piece_type and old_piece.color == color:
            # Same piece, same type - no validation needed
            pass
        elif old_piece and old_piece.color == color:
            # Replacing same color piece with different type - net count change
            # Remove old piece temporarily for count check
            self.board_state.set_piece_virtual(square, None)
            can_place, error_msg = self._can_place_piece(piece_type, color)
            # Restore old piece for now
            self.board_state.set_piece_virtual(square, old_piece)

            if not can_place:
                messagebox.showwarning("Cannot Place Piece", error_msg)
                return
        elif not old_piece or (old_piece and old_piece.color != color):
            # Adding new piece or replacing opponent's piece
            can_place, error_msg = self._can_place_piece(piece_type, color)
            if not can_place:
                messagebox.showwarning("Cannot Place Piece", error_msg)
                return

        # Save current state for undo
        self.undo_stack.append((square, old_piece))
        if len(self.undo_stack) > 50:
            self.undo_stack.pop(0)

        # Place the piece
        piece = Piece(type=piece_type, color=color)
        self.board_state.set_piece_virtual(square, piece)

        # Enable undo button
        if hasattr(self, 'undo_btn'):
            self.undo_btn.config(state=tk.NORMAL)

        self._redraw_board()
        self._update_sync_status()
        self._update_fen_display()

    def _get_square_from_coords(self, x: int, y: int) -> Optional[str]:
        """Convert canvas coordinates to square notation (updated for workspace scaling)."""
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()

        # Calculate scale (same as in _redraw_board)
        available_pixels = min(canvas_w, canvas_h) * 0.90
        workspace_size_mm = max(self.workspace_width_mm, self.workspace_height_mm)
        pixels_per_mm = available_pixels / workspace_size_mm

        # Calculate workspace dimensions in pixels
        workspace_width_px = self.workspace_width_mm * pixels_per_mm
        workspace_height_px = self.workspace_height_mm * pixels_per_mm

        # Center workspace in canvas
        workspace_offset_x = (canvas_w - workspace_width_px) / 2
        workspace_offset_y = (canvas_h - workspace_height_px) / 2

        # Get board dimensions from config
        board_width_mm = self.board_cfg.width_mm
        board_height_mm = self.board_cfg.height_mm
        board_origin_x_mm = self.board_cfg.origin_x_mm
        board_origin_y_mm = self.board_cfg.origin_y_mm

        # Calculate board size in pixels
        board_width_px = board_width_mm * pixels_per_mm
        board_height_px = board_height_mm * pixels_per_mm

        # Position board within workspace
        board_offset_x = workspace_offset_x + (board_origin_x_mm * pixels_per_mm)
        board_offset_y = workspace_offset_y + (workspace_height_px - board_origin_y_mm * pixels_per_mm) - board_height_px

        files = self.board_cfg.files
        ranks = self.board_cfg.ranks
        sq_size = board_width_px / files

        board_x = x - board_offset_x
        board_y = y - board_offset_y

        if board_x < 0 or board_y < 0 or board_x >= board_width_px or board_y >= board_height_px:
            return None

        file_idx = int(board_x // sq_size)
        rank_idx = int((board_height_px - board_y) // sq_size)

        if self.board_orientation == 'black':
            file_idx = (files - 1) - file_idx
            rank_idx = (ranks - 1) - rank_idx

        if file_idx < 0 or file_idx >= files or rank_idx < 0 or rank_idx >= ranks:
            return None

        return f"{chr(ord('a') + file_idx)}{rank_idx + 1}"

    def _redraw_board(self):
        """Redraw the chess board with current position, scaled within machine workspace."""
        c = self.canvas
        c.delete("all")

        # Clear image references for garbage collection of old images
        self.piece_images.clear()

        canvas_w = c.winfo_width()
        canvas_h = c.winfo_height()

        # Calculate scale: pixels per mm based on workspace dimensions
        # Use 90% of canvas for workspace (5% margin on each side)
        available_pixels = min(canvas_w, canvas_h) * 0.90
        workspace_size_mm = max(self.workspace_width_mm, self.workspace_height_mm)
        pixels_per_mm = available_pixels / workspace_size_mm

        # Calculate workspace dimensions in pixels
        workspace_width_px = self.workspace_width_mm * pixels_per_mm
        workspace_height_px = self.workspace_height_mm * pixels_per_mm

        # Center workspace in canvas
        workspace_offset_x = (canvas_w - workspace_width_px) / 2
        workspace_offset_y = (canvas_h - workspace_height_px) / 2

        # Draw workspace boundary (dark border)
        c.create_rectangle(
            workspace_offset_x, workspace_offset_y,
            workspace_offset_x + workspace_width_px,
            workspace_offset_y + workspace_height_px,
            outline=self.theme['accent'],
            width=2,
            dash=(5, 3)
        )

        # Add workspace label
        c.create_text(
            workspace_offset_x + 5,
            workspace_offset_y + 5,
            text=f"Workspace: {self.workspace_width_mm:.0f}×{self.workspace_height_mm:.0f}mm",
            fill=self.theme['text_secondary'],
            font=("Segoe UI", 8),
            anchor="nw"
        )

        # Add storage layout indicator
        layout_name_map = {
            StorageLayout.NONE: "Standard Board (No Storage)",
            StorageLayout.TOP: "Storage: Top 2 Ranks",
            StorageLayout.BOTTOM: "Storage: Bottom 2 Ranks",
            StorageLayout.PERIMETER: "Storage: Perimeter Border"
        }
        layout_text = layout_name_map.get(self.board_cfg.storage_layout, "Unknown Layout")

        c.create_text(
            workspace_offset_x + 5,
            workspace_offset_y + 20,
            text=layout_text,
            fill=self.theme['accent'],
            font=("Segoe UI", 8, "bold"),
            anchor="nw"
        )

        # Get board dimensions from config
        board_width_mm = self.board_cfg.width_mm
        board_height_mm = self.board_cfg.height_mm
        board_origin_x_mm = self.board_cfg.origin_x_mm
        board_origin_y_mm = self.board_cfg.origin_y_mm

        # Calculate board size in pixels
        board_width_px = board_width_mm * pixels_per_mm
        board_height_px = board_height_mm * pixels_per_mm

        # Position board within workspace (origin is bottom-left in machine coords)
        # Canvas Y increases downward, machine Y increases upward
        board_offset_x = workspace_offset_x + (board_origin_x_mm * pixels_per_mm)
        board_offset_y = workspace_offset_y + (workspace_height_px - board_origin_y_mm * pixels_per_mm) - board_height_px

        # Calculate square size based on board dimensions
        files = self.board_cfg.files
        ranks = self.board_cfg.ranks
        sq_size = board_width_px / files

        # Draw board boundary
        c.create_rectangle(
            board_offset_x, board_offset_y,
            board_offset_x + board_width_px,
            board_offset_y + board_height_px,
            outline=self.theme['fg'],
            width=2
        )

        # Draw squares
        for rank in range(ranks):
            for file in range(files):
                # Determine if this square is in the playing area
                is_playing = self.board_cfg.is_playing_square(file, rank)

                display_file = file if self.board_orientation == 'white' else (files - 1 - file)
                display_rank = rank if self.board_orientation == 'white' else (ranks - 1 - rank)

                x0 = board_offset_x + file * sq_size
                y0 = board_offset_y + (ranks - 1 - rank) * sq_size
                x1 = x0 + sq_size
                y1 = y0 + sq_size

                # Color: Storage squares use distinct colors (NOT chess pattern)
                if is_playing:
                    # Playing area: standard chess board pattern
                    color = self.theme['board_light'] if (rank + file) % 2 == 0 else self.theme['board_dark']
                    outline_color = ''
                    outline_width = 0
                else:
                    # Storage squares: Use distinct colors (never chess pattern colors)
                    square_for_check = f"{chr(ord('a') + file)}{rank + 1}"
                    has_piece = self.board_state.get_piece_virtual(square_for_check) is not None

                    if self.highlight_occupied_storage and has_piece:
                        color = '#1a1a1a'  # Very dark gray for occupied storage squares
                    else:
                        color = '#3a3a3a'  # Medium-dark gray for empty storage squares

                    outline_color = '#555555'  # Gray border for storage squares
                    outline_width = 1

                c.create_rectangle(x0, y0, x1, y1, fill=color, outline=outline_color, width=outline_width)

                # Draw piece
                square = f"{chr(ord('a') + display_file)}{display_rank + 1}"
                piece = self.board_state.get_piece_virtual(square)

                if piece:
                    piece_code = f"{piece.color.value}{piece.type.value.upper()}"

                    # Try to load PNG image
                    piece_size = int(sq_size * 0.8)  # 80% of square size
                    piece_img = load_piece_svg(piece_code, piece_size)

                    if piece_img:
                        # Keep a reference to prevent garbage collection
                        self.piece_images.append(piece_img)
                        # Use image
                        c.create_image(
                            x0 + sq_size / 2,
                            y0 + sq_size / 2,
                            image=piece_img,
                            tags="piece"
                        )
                    else:
                        # Fallback to Unicode symbol
                        symbol = PIECE_SYMBOLS[piece_code]
                        c.create_text(
                            x0 + sq_size / 2,
                            y0 + sq_size / 2,
                            text=symbol,
                            font=("Segoe UI", int(sq_size * 0.6)),
                            fill=self.theme['fg']
                        )

        # Draw file/rank labels
        for file in range(files):
            display_file = file if self.board_orientation == 'white' else (files - 1 - file)
            label = chr(ord('A') + display_file)

            # Check if this file is in storage area (for perimeter layouts)
            is_storage_file = not self.board_cfg.is_playing_square(file, 0)

            # Use different color/style for storage files
            label_color = "#f39c12" if is_storage_file else self.theme['text_secondary']
            label_font = ("Arial", 10, "bold") if is_storage_file else ("Arial", 10)

            x = board_offset_x + (file + 0.5) * sq_size
            y = board_offset_y + board_height_px + 15
            c.create_text(x, y, text=label, fill=label_color, font=label_font)

        for rank in range(ranks):
            display_rank = rank if self.board_orientation == 'white' else (ranks - 1 - rank)
            label = str(display_rank + 1)

            # Check if this rank is in storage area
            is_storage_rank = not self.board_cfg.is_playing_square(0, rank)

            # Use different color/style for storage ranks
            label_color = "#f39c12" if is_storage_rank else self.theme['text_secondary']
            label_font = ("Arial", 10, "bold") if is_storage_rank else ("Arial", 10)

            x = board_offset_x - 15
            y = board_offset_y + (ranks - 1 - rank + 0.5) * sq_size
            c.create_text(x, y, text=label, fill=label_color, font=label_font)

    def _update_sync_status(self):
        """Update sync status indicator."""
        is_synced = self.board_state.is_synced()
        self.sync_status_label.config(
            text="● Synced" if is_synced else "● Out of Sync",
            bg=self.theme['success'] if is_synced else self.theme['warning']
        )

    def _update_fen_display(self):
        """Update FEN entry with current position."""
        fen = self.board_state.to_fen('virtual')
        self.fen_entry.delete(0, tk.END)
        self.fen_entry.insert(0, fen)

    def _set_starting_position(self):
        """Set board to starting position."""
        self.board_state.reset_starting_position('virtual')
        self._redraw_board()
        self._update_sync_status()
        self._update_fen_display()

    def _clear_board(self):
        """Clear all pieces."""
        self.board_state.clear_virtual()
        self._redraw_board()
        self._update_sync_status()
        self._update_fen_display()

    def _flip_board(self):
        """Flip board orientation."""
        self.board_orientation = 'black' if self.board_orientation == 'white' else 'white'
        self._redraw_board()

    def _toggle_storage_highlight(self):
        """Toggle storage square occupied highlighting."""
        self.highlight_occupied_storage = not self.highlight_occupied_storage

        # Update button text and appearance
        if self.highlight_occupied_storage:
            self.storage_highlight_btn.config(
                text="■ Show Occupied Storage",
                bg=self.theme['accent'],
                fg="white"
            )
        else:
            self.storage_highlight_btn.config(
                text="◻ Show Occupied Storage",
                bg=self.theme['input_bg'],
                fg=self.theme['fg']
            )

        self._redraw_board()

    def _load_fen(self):
        """Load position from FEN."""
        fen = self.fen_entry.get().strip()
        if not fen:
            return

        try:
            self.board_state.load_fen(fen, 'virtual')
            self._redraw_board()
            self._update_sync_status()
            messagebox.showinfo("FEN Loaded", "Position loaded successfully!")
        except Exception as e:
            messagebox.showerror("Invalid FEN", f"Could not load FEN:\n{e}")

    def _copy_fen(self):
        """Copy FEN to clipboard."""
        fen = self.board_state.to_fen('virtual')
        self.clipboard_clear()
        self.clipboard_append(fen)
        messagebox.showinfo("Copied", "FEN copied to clipboard!")

    def _send_to_machine(self):
        """Send virtual position to machine (mark as physical truth)."""
        if self.on_send_to_machine:
            self.on_send_to_machine(self.board_state)
        else:
            # Default: just sync the state
            self.board_state.sync_physical_to_virtual()
            self._update_sync_status()
            messagebox.showinfo("Sent", "Position sent to machine!")

    def _get_from_machine(self):
        """Get current physical position from machine."""
        if self.on_get_from_machine:
            self.on_get_from_machine(self.board_state)
            self._redraw_board()
            self._update_sync_status()
            self._update_fen_display()
        else:
            messagebox.showinfo("Get Position", "Machine position query not implemented yet")

    def _auto_update_position(self):
        """Automatically move pieces to match virtual position."""
        if not self.board_state.is_synced():
            result = messagebox.askyesno(
                "Auto Update",
                "This will automatically move all pieces to match the virtual position.\n\n"
                "The machine will execute the moves. Continue?",
                icon='question'
            )

            if result and self.on_auto_update:
                self.on_auto_update(self.board_state, auto_mode=True)
        else:
            messagebox.showinfo("Already Synced", "Position is already synced!")

    def _manual_update_position(self):
        """Show instructions for manual position update."""
        to_add, to_remove, to_move = self.board_state.get_differences()

        if not (to_add or to_remove or to_move):
            messagebox.showinfo("Already Synced", "Position is already synced!")
            return

        # Build instruction message
        msg = "Please manually adjust the pieces:\n\n"

        if to_remove:
            msg += "REMOVE pieces from:\n"
            for sq in sorted(to_remove):
                msg += f"  • {sq.upper()}\n"
            msg += "\n"

        if to_add:
            msg += "ADD pieces to:\n"
            for sq in sorted(to_add):
                piece = self.board_state.get_piece_virtual(sq)
                msg += f"  • {sq.upper()}: {piece}\n"
            msg += "\n"

        if to_move:
            msg += "CHANGE pieces on:\n"
            for sq in sorted(to_move):
                piece = self.board_state.get_piece_virtual(sq)
                msg += f"  • {sq.upper()}: {piece}\n"

        result = messagebox.askyesno(
            "Manual Update Instructions",
            msg + "\nClick OK when done to mark as synced.",
            icon='info'
        )

        if result:
            self.board_state.sync_physical_to_virtual()
            self._update_sync_status()
            messagebox.showinfo("Synced", "Position marked as synced!")

    def _handle_jog(self, x_dir: int, y_dir: int):
        """Handle jog button press."""
        if self.on_jog:
            distance = self.jog_distance.get()
            self.on_jog(x_dir, y_dir, distance)

    def _handle_home(self):
        """Handle home button press."""
        if self.on_home:
            self.on_home()

    def _handle_move_to_square(self):
        """Handle move to square button."""
        if self.on_move_to_square:
            square = self.square_entry.get().strip()
            if square:
                self.on_move_to_square(square)
                self.square_entry.delete(0, tk.END)

    def _handle_calibrate(self):
        """Handle calibration button."""
        if self.on_calibrate:
            square = self.cal_square_entry.get().strip()
            if square:
                self.on_calibrate(square)

    # Servo control methods
    def _lift_up(self):
        """Raise lift to maximum height."""
        self.servos.lift_up()

    def _lift_down(self):
        """Lower lift to board level."""
        self.servos.lift_down()

    def _lift_mid(self):
        """Move lift to middle position."""
        self.servos.lift_mid()

    def _grip_open(self):
        """Open gripper fully."""
        self.servos.grip_open()

    def _grip_close(self):
        """Close gripper on piece."""
        self.servos.grip_close()

    def _undo_last_edit(self):
        """Undo the last piece placement or removal."""
        if not self.undo_stack:
            return

        # Pop the last edit from the stack
        square, old_piece = self.undo_stack.pop()

        # Restore the previous state
        self.board_state.set_piece_virtual(square, old_piece)

        # Disable undo button if stack is empty
        if not self.undo_stack and hasattr(self, 'undo_btn'):
            self.undo_btn.config(state=tk.DISABLED)

        self._redraw_board()
        self._update_sync_status()
        self._update_fen_display()
