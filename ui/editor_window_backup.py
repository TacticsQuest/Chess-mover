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
from logic.board_map import BoardConfig
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
    Load an SVG piece image and return as PhotoImage.
    Tries multiple methods: Wand (ImageMagick), cairosvg, svglib.
    Falls back to Unicode if all methods fail.
    Caches images by (piece_code, size) for performance.
    """
    cache_key = (piece_code, size)

    # Return cached image if available
    if cache_key in _piece_image_cache:
        return _piece_image_cache[cache_key]

    # Construct path to SVG file
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    svg_path = os.path.join(project_root, 'assets', 'pieces', f'{piece_code}.svg')

    if not os.path.exists(svg_path):
        print(f"SVG file not found: {svg_path}")
        return None

    try:
        img = None

        # Method 1: Try Wand (ImageMagick) - works best on Windows
        if img is None:
            try:
                from wand.image import Image as WandImage
                with WandImage(filename=svg_path, width=size, height=size) as wand_img:
                    # Convert to PNG blob
                    wand_img.format = 'png'
                    png_blob = wand_img.make_blob()
                    # Load with PIL
                    img = Image.open(io.BytesIO(png_blob))
                print(f"✓ Loaded {piece_code} with Wand/ImageMagick")
            except ImportError:
                pass  # Wand not installed
            except Exception as e:
                print(f"Wand method failed for {piece_code}: {e}")

        # Method 2: Try cairosvg (requires Cairo DLL on Windows)
        if img is None:
            try:
                import cairosvg
                png_data = cairosvg.svg2png(url=svg_path, output_width=size, output_height=size)
                img = Image.open(io.BytesIO(png_data))
                print(f"✓ Loaded {piece_code} with cairosvg")
            except (ImportError, OSError):
                pass  # Cairo not available
            except Exception as e:
                print(f"Cairo method failed for {piece_code}: {e}")

        # Method 3: Try svglib (also requires Cairo)
        if img is None:
            try:
                from svglib.svglib import svg2rlg
                from reportlab.graphics import renderPM
                drawing = svg2rlg(svg_path)
                scale = size / max(drawing.width, drawing.height)
                drawing.width = size
                drawing.height = size
                drawing.scale(scale, scale)
                img = renderPM.drawToPIL(drawing)
                print(f"✓ Loaded {piece_code} with svglib")
            except (ImportError, OSError):
                pass  # svglib/Cairo not available
            except Exception as e:
                print(f"svglib method failed for {piece_code}: {e}")

        # If all methods failed, return None to fall back to Unicode
        if img is None:
            print(f"✗ All SVG loading methods failed for {piece_code}, falling back to Unicode")
            return None

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

        # Undo stack for board edits
        self.undo_stack = []  # List of (square, piece_or_none) tuples

        # Keep references to piece images to prevent garbage collection
        self.piece_images = []

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

        # Main container
        container = tk.Frame(self, bg=self.theme['bg'])
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left panel - Piece palette
        left_panel = tk.Frame(container, bg=self.theme['panel_bg'], width=150)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False)

        tk.Label(
            left_panel,
            text="Piece Palette",
            font=("Segoe UI", 11, "bold"),
            bg=self.theme['panel_bg'],
            fg=self.theme['accent']
        ).pack(pady=10)

        # White pieces
        tk.Label(
            left_panel,
            text="White Pieces",
            font=("Segoe UI", 9),
            bg=self.theme['panel_bg'],
            fg=self.theme['text_secondary']
        ).pack(pady=(10, 5))

        white_pieces = [
            ('wK', '♔'), ('wQ', '♕'), ('wR', '♖'),
            ('wB', '♗'), ('wN', '♘'), ('wP', '♙')
        ]

        for piece_code, symbol in white_pieces:
            self._create_piece_button(left_panel, piece_code, symbol)

        # Black pieces
        tk.Label(
            left_panel,
            text="Black Pieces",
            font=("Segoe UI", 9),
            bg=self.theme['panel_bg'],
            fg=self.theme['text_secondary']
        ).pack(pady=(20, 5))

        black_pieces = [
            ('bK', '♚'), ('bQ', '♛'), ('bR', '♜'),
            ('bB', '♝'), ('bN', '♞'), ('bP', '♟')
        ]

        for piece_code, symbol in black_pieces:
            self._create_piece_button(left_panel, piece_code, symbol)

        # Delete button
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
            font=("Segoe UI", 10),
            bg=self.theme['danger'],
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=lambda: self._select_piece('delete')
        )
        delete_btn.pack(pady=5, padx=10, fill=tk.X)

        # Center panel - Chess board
        center_panel = tk.Frame(container, bg=self.theme['canvas_bg'])
        center_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Board canvas
        self.canvas = tk.Canvas(
            center_panel,
            bg=self.theme['canvas_bg'],
            highlightthickness=0,
            width=600,
            height=600
        )
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        self.canvas.bind("<Button-1>", self._on_square_click)
        self.canvas.bind("<Configure>", lambda e: self._redraw_board())

        # Right panel - Controls
        right_panel = tk.Frame(container, bg=self.theme['panel_bg'], width=300)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        right_panel.pack_propagate(False)

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

        # === MACHINE CONTROL (ADVANCED) SECTION ===
        tk.Label(
            right_panel,
            text="Machine Control (Advanced)",
            font=("Segoe UI", 10, "bold"),
            bg=self.theme['panel_bg'],
            fg=self.theme['fg']
        ).pack(pady=(20, 5))

        jog_content = tk.Frame(right_panel, bg=self.theme['panel_bg'])
        jog_content.pack(fill=tk.X, padx=10, pady=5)

        # Manual Jog subsection
        tk.Label(
            jog_content,
            text="Manual Jog",
            font=("Segoe UI", 9, "bold"),
            bg=self.theme['panel_bg'],
            fg=self.theme['fg']
        ).pack(anchor="w", pady=(0, 5))

        # Jog distance selector
        jog_label = tk.Label(
            jog_content,
            text="Distance:",
            font=("Segoe UI", 9),
            bg=self.theme['panel_bg'],
            fg=self.theme['text_secondary']
        )
        jog_label.pack(anchor="w", pady=(0, 5))

        jog_dist_frame = tk.Frame(jog_content, bg=self.theme['panel_bg'])
        jog_dist_frame.pack(fill=tk.X, pady=(0, 10))

        self.jog_distance = tk.IntVar(value=10)
        for dist in [1, 10, 50, 100]:
            rb = tk.Radiobutton(
                jog_dist_frame,
                text=f"{dist}mm",
                variable=self.jog_distance,
                value=dist,
                font=("Segoe UI", 8),
                bg=self.theme['panel_bg'],
                fg=self.theme['fg'],
                selectcolor=self.theme['input_bg'],
                activebackground=self.theme['panel_bg'],
                activeforeground=self.theme['accent'],
                cursor="hand2"
            )
            rb.pack(side=tk.LEFT, padx=(0, 10))

        # Arrow buttons (compact)
        arrow_container = tk.Frame(jog_content, bg=self.theme['panel_bg'])
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

        # Move to square
        tk.Label(
            jog_content,
            text="Move to Square:",
            font=("Segoe UI", 9),
            bg=self.theme['panel_bg'],
            fg=self.theme['text_secondary']
        ).pack(anchor="w", pady=(15, 5))

        move_frame = tk.Frame(jog_content, bg=self.theme['panel_bg'])
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
        self.square_entry.pack(side=tk.LEFT, ipady=6, ipadx=8)
        self.square_entry.bind("<Return>", lambda e: self._handle_move_to_square())
        self._create_tooltip(self.square_entry, "Enter square (e.g., E4) to move machine to that position")

        move_go_btn = tk.Button(
            move_frame,
            text="Go",
            font=("Segoe UI", 9, "bold"),
            bg=self.theme['accent'],
            fg="white",
            relief=tk.FLAT,
            bd=0,
            padx=15,
            pady=6,
            cursor="hand2",
            command=self._handle_move_to_square
        )
        move_go_btn.pack(side=tk.LEFT, padx=(8, 0))
        self._create_tooltip(move_go_btn, "Move machine to the specified square")

        # Calibration
        tk.Label(
            jog_content,
            text="Calibration:",
            font=("Segoe UI", 9),
            bg=self.theme['panel_bg'],
            fg=self.theme['text_secondary']
        ).pack(anchor="w", pady=(15, 5))

        cal_frame = tk.Frame(jog_content, bg=self.theme['panel_bg'])
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
        self.cal_square_entry.pack(side=tk.LEFT, ipady=6, ipadx=8)
        self.cal_square_entry.insert(0, "A1")
        self.cal_square_entry.bind("<Return>", lambda e: self._handle_calibrate())
        self._create_tooltip(self.cal_square_entry, "Enter the square the machine is currently positioned over")

        cal_set_btn = tk.Button(
            cal_frame,
            text="Set",
            font=("Segoe UI", 9, "bold"),
            bg=self.theme['accent'],
            fg="white",
            relief=tk.FLAT,
            bd=0,
            padx=15,
            pady=6,
            cursor="hand2",
            command=self._handle_calibrate
        )
        cal_set_btn.pack(side=tk.LEFT, padx=(8, 0))
        self._create_tooltip(cal_set_btn, "Calibrate board origin based on current position")

        # Servo controls (compact)
        tk.Label(
            right_panel,
            text="Servos",
            font=("Segoe UI", 10, "bold"),
            bg=self.theme['panel_bg'],
            fg=self.theme['fg']
        ).pack(pady=(20, 5))

        servo_content = tk.Frame(right_panel, bg=self.theme['panel_bg'])
        servo_content.pack(fill=tk.X, padx=10, pady=5)

        # Lift controls
        lift_frame = tk.Frame(servo_content, bg=self.theme['input_bg'], relief=tk.FLAT, bd=1)
        lift_frame.pack(fill=tk.X, pady=(0, 5))

        tk.Label(
            lift_frame,
            text="↕ Lift",
            font=("Segoe UI", 9, "bold"),
            bg=self.theme['input_bg'],
            fg=self.theme['fg']
        ).pack(pady=5)

        lift_btn_frame = tk.Frame(lift_frame, bg=self.theme['input_bg'])
        lift_btn_frame.pack(pady=5)

        lift_up_btn = tk.Button(
            lift_btn_frame,
            text="▲ UP",
            width=6,
            font=("Segoe UI", 8),
            bg="#3498db",
            fg="white",
            relief=tk.RAISED,
            cursor="hand2",
            command=self._lift_up
        )
        lift_up_btn.pack(side=tk.LEFT, padx=2)
        self._create_tooltip(lift_up_btn, "Raise lift to maximum height (travel position)")

        lift_mid_btn = tk.Button(
            lift_btn_frame,
            text="■ MID",
            width=5,
            font=("Segoe UI", 8),
            bg="#95a5a6",
            fg="white",
            relief=tk.RAISED,
            cursor="hand2",
            command=self._lift_mid
        )
        lift_mid_btn.pack(side=tk.LEFT, padx=2)
        self._create_tooltip(lift_mid_btn, "Move lift to middle position")

        lift_down_btn = tk.Button(
            lift_btn_frame,
            text="▼ DOWN",
            width=6,
            font=("Segoe UI", 8),
            bg="#e74c3c",
            fg="white",
            relief=tk.RAISED,
            cursor="hand2",
            command=self._lift_down
        )
        lift_down_btn.pack(side=tk.LEFT, padx=2)
        self._create_tooltip(lift_down_btn, "Lower lift to board level (pickup position)")

        # Gripper controls
        grip_frame = tk.Frame(servo_content, bg=self.theme['input_bg'], relief=tk.FLAT, bd=1)
        grip_frame.pack(fill=tk.X)

        tk.Label(
            grip_frame,
            text="✋ Gripper",
            font=("Segoe UI", 9, "bold"),
            bg=self.theme['input_bg'],
            fg=self.theme['fg']
        ).pack(pady=5)

        grip_btn_frame = tk.Frame(grip_frame, bg=self.theme['input_bg'])
        grip_btn_frame.pack(pady=5)

        grip_open_btn = tk.Button(
            grip_btn_frame,
            text="◀ OPEN ▶",
            width=10,
            font=("Segoe UI", 8),
            bg="#27ae60",
            fg="white",
            relief=tk.RAISED,
            cursor="hand2",
            command=self._grip_open
        )
        grip_open_btn.pack(side=tk.LEFT, padx=2)
        self._create_tooltip(grip_open_btn, "Open gripper to release piece")

        grip_close_btn = tk.Button(
            grip_btn_frame,
            text="▶ CLOSE ◀",
            width=10,
            font=("Segoe UI", 8),
            bg="#e67e22",
            fg="white",
            relief=tk.RAISED,
            cursor="hand2",
            command=self._grip_close
        )
        grip_close_btn.pack(side=tk.LEFT, padx=2)
        self._create_tooltip(grip_close_btn, "Close gripper to grab piece")

        self._redraw_board()
        self._update_fen_display()

    def _create_tooltip(self, widget, text):
        """Create a tooltip for a widget."""
        return ToolTip(widget, text)

    def _create_piece_button(self, parent, piece_code: str, symbol: str):
        """Create a piece selection button."""
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

    def _select_piece(self, piece_code: str):
        """Select a piece for placement."""
        self.selected_piece = piece_code
        # Visual feedback could be added here

    def _on_square_click(self, event):
        """Handle click on board square."""
        if not self.selected_piece:
            return

        square = self._get_square_from_coords(event.x, event.y)
        if not square:
            return

        # Save current state for undo
        old_piece = self.board_state.get_piece_virtual(square)
        self.undo_stack.append((square, old_piece))

        # Limit undo stack to 50 moves
        if len(self.undo_stack) > 50:
            self.undo_stack.pop(0)

        if self.selected_piece == 'delete':
            # Remove piece
            self.board_state.set_piece_virtual(square, None)
        else:
            # Place piece
            color = PieceColor.WHITE if self.selected_piece[0] == 'w' else PieceColor.BLACK
            piece_type = PieceType(self.selected_piece[1].lower())
            piece = Piece(type=piece_type, color=color)
            self.board_state.set_piece_virtual(square, piece)

        # Enable undo button
        if hasattr(self, 'undo_btn'):
            self.undo_btn.config(state=tk.NORMAL)

        self._redraw_board()
        self._update_sync_status()
        self._update_fen_display()

    def _get_square_from_coords(self, x: int, y: int) -> Optional[str]:
        """Convert canvas coordinates to square notation."""
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()

        size = (min(canvas_w, canvas_h) * 0.95) - 50
        offset_x = (canvas_w - size) / 2
        offset_y = (canvas_h - size) / 2

        sq_size = size / 8

        board_x = x - offset_x
        board_y = y - offset_y

        if board_x < 0 or board_y < 0 or board_x >= size or board_y >= size:
            return None

        file_idx = int(board_x // sq_size)
        rank_idx = int((size - board_y) // sq_size)

        if self.board_orientation == 'black':
            file_idx = 7 - file_idx
            rank_idx = 7 - rank_idx

        if file_idx < 0 or file_idx >= 8 or rank_idx < 0 or rank_idx >= 8:
            return None

        return f"{chr(ord('a') + file_idx)}{rank_idx + 1}"

    def _redraw_board(self):
        """Redraw the chess board with current position."""
        c = self.canvas
        c.delete("all")

        # Clear image references for garbage collection of old images
        self.piece_images.clear()

        canvas_w = c.winfo_width()
        canvas_h = c.winfo_height()

        size = (min(canvas_w, canvas_h) * 0.95) - 50
        offset_x = (canvas_w - size) / 2
        offset_y = (canvas_h - size) / 2

        sq_size = size / 8

        # Draw squares
        for rank in range(8):
            for file in range(8):
                display_file = file if self.board_orientation == 'white' else 7 - file
                display_rank = rank if self.board_orientation == 'white' else 7 - rank

                x0 = offset_x + file * sq_size
                y0 = offset_y + (7 - rank) * sq_size
                x1 = x0 + sq_size
                y1 = y0 + sq_size

                color = self.theme['board_light'] if (rank + file) % 2 == 0 else self.theme['board_dark']
                c.create_rectangle(x0, y0, x1, y1, fill=color, outline='')

                # Draw piece
                square = f"{chr(ord('a') + display_file)}{display_rank + 1}"
                piece = self.board_state.get_piece_virtual(square)

                if piece:
                    piece_code = f"{piece.color.value}{piece.type.value.upper()}"

                    # Try to load SVG image
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
        for file in range(8):
            display_file = file if self.board_orientation == 'white' else 7 - file
            label = chr(ord('A') + display_file)
            x = offset_x + (file + 0.5) * sq_size
            y = offset_y + size + 15
            c.create_text(x, y, text=label, fill=self.theme['text_secondary'], font=("Arial", 10))

        for rank in range(8):
            display_rank = rank if self.board_orientation == 'white' else 7 - rank
            label = str(display_rank + 1)
            x = offset_x - 15
            y = offset_y + (7 - rank + 0.5) * sq_size
            c.create_text(x, y, text=label, fill=self.theme['text_secondary'], font=("Arial", 10))

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
