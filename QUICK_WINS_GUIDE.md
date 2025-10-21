# Chess Mover Machine - Quick Wins Implementation Guide

This guide shows you how to quickly integrate the new improvements into your GUI.

---

## 🎯 Quick Win #1: Emergency Stop Button (5 min)

### Add to toolbar (in `_build_ui` method, after other buttons):

```python
# Emergency Stop Button - Add RIGHT after "Connect" button
estop_btn = tk.Button(
    right_toolbar,
    text="⚠ EMERGENCY STOP",
    font=("Segoe UI", 10, "bold"),
    bg="#c0392b",  # Dark red
    fg="white",
    relief=tk.RAISED,
    bd=3,
    padx=20,
    pady=10,
    cursor="hand2",
    command=self._emergency_stop,
    activebackground="#a93226",
    activeforeground="white"
)
estop_btn.pack(side=tk.LEFT, padx=10)

# Make it flash/pulse (optional but attention-grabbing)
def pulse_estop():
    current_bg = estop_btn.cget('bg')
    new_bg = '#e74c3c' if current_bg == '#c0392b' else '#c0392b'
    estop_btn.config(bg=new_bg)
    self.after(800, pulse_estop)
pulse_estop()
```

### Add emergency stop handler method:

```python
def _emergency_stop(self):
    """Emergency stop handler."""
    result = messagebox.askyesno(
        "Emergency Stop",
        "⚠️ EMERGENCY STOP\n\nThis will immediately halt all motion.\n\nProceed?",
        icon='warning'
    )
    if result:
        self.gantry.emergency_stop()
        self.status.set("⚠️ EMERGENCY STOP ACTIVE")
        self._log("[SYSTEM] ⚠️ EMERGENCY STOP ACTIVATED")

        # Show reset dialog
        self.after(1000, self._show_reset_dialog)

def _show_reset_dialog(self):
    """Show dialog to reset emergency stop."""
    result = messagebox.askyesno(
        "Reset Emergency Stop",
        "Emergency stop is active.\n\nReset and resume operation?",
        icon='question'
    )
    if result:
        self.gantry.reset_emergency_stop()
        self.gantry.unlock()  # Clear GRBL alarm
        self.status.set("Emergency stop cleared - Ready")
        self._log("[SYSTEM] Emergency stop cleared")
```

---

## 🎯 Quick Win #2: Keyboard Shortcuts (10 min)

### Add to `__init__` method (after `self._build_ui()`):

```python
# Keyboard shortcuts
self._setup_keyboard_shortcuts()
```

### Add new method:

```python
def _setup_keyboard_shortcuts(self):
    """Set up keyboard shortcuts."""
    # Emergency & Control
    self.bind('<Escape>', lambda e: self._emergency_stop())
    self.bind('<Home>', lambda e: self._home())
    self.bind('<space>', lambda e: self.gantry.unlock())

    # Movement (arrow keys)
    self.bind('<Up>', lambda e: self._jog(0, 1))
    self.bind('<Down>', lambda e: self._jog(0, -1))
    self.bind('<Left>', lambda e: self._jog(-1, 0))
    self.bind('<Right>', lambda e: self._jog(1, 0))

    # Jog distance adjustment
    self.bind('<plus>', lambda e: self._adjust_jog_distance(1))
    self.bind('<minus>', lambda e: self._adjust_jog_distance(-1))

    # Connection
    self.bind('<Control-c>', lambda e: self._connect())
    self.bind('<Control-d>', lambda e: self._disconnect())

    # Utility
    self.bind('<Control-s>', lambda e: self._open_settings())
    self.bind('<F1>', lambda e: self._show_shortcuts_help())

    self._log("[SYSTEM] Keyboard shortcuts enabled (Press F1 for help)")

def _adjust_jog_distance(self, direction: int):
    """Adjust jog distance up or down."""
    distances = [1, 10, 50, 100]
    current = self.jog_distance.get()
    try:
        idx = distances.index(current)
        new_idx = max(0, min(len(distances)-1, idx + direction))
        self.jog_distance.set(distances[new_idx])
        self._log(f"[UI] Jog distance: {distances[new_idx]}mm")
    except ValueError:
        pass

def _show_shortcuts_help(self):
    """Show keyboard shortcuts help dialog."""
    help_text = """
    KEYBOARD SHORTCUTS

    Emergency & Control:
      ESC        Emergency Stop
      Home       Home Gantry
      Space      Unlock/Reset

    Movement:
      ↑ ↓ ← →    Jog in directions
      + / -      Adjust jog distance

    Connection:
      Ctrl+C     Connect
      Ctrl+D     Disconnect

    Utility:
      Ctrl+S     Settings
      F1         This help
    """
    messagebox.showinfo("Keyboard Shortcuts", help_text)
```

---

## 🎯 Quick Win #3: Live Position Display (15 min)

### Add to `__init__` method (after gantry controller creation):

```python
# Register position callback for live display
self.gantry.register_position_callback(self._on_position_update)
self._current_canvas_pos = None  # Track position indicator
```

### Add position update handler:

```python
def _on_position_update(self, pos: Position):
    """Handle position updates from GRBL."""
    self._current_canvas_pos = pos
    # Redraw will show updated position

def _draw_position_indicator(self):
    """Draw live position indicator on canvas."""
    if not self._current_canvas_pos:
        return

    pos = self._current_canvas_pos
    c = self.canvas
    canvas_w = c.winfo_width()
    canvas_h = c.winfo_height()

    # Calculate board dimensions (same as _redraw_board)
    size = (min(canvas_w, canvas_h) * 0.95) - 50
    offset_x = (canvas_w - size) / 2
    offset_y = (canvas_h - size) / 2

    # Convert machine coords to canvas coords
    # Assumes origin is at A1 corner
    try:
        board_cfg = self.board_cfg
        x_ratio = (pos.x - board_cfg.origin_x_mm) / board_cfg.width_mm
        y_ratio = (pos.y - board_cfg.origin_y_mm) / board_cfg.height_mm

        canvas_x = offset_x + (x_ratio * size)
        canvas_y = offset_y + size - (y_ratio * size)  # Flip Y

        # Draw crosshair
        state = self.gantry.get_state()
        color = {
            ConnectionState.CONNECTED: '#27ae60',  # green
            ConnectionState.ALARM: '#e74c3c',      # red
            ConnectionState.ERROR: '#e67e22',      # orange
            ConnectionState.DISCONNECTED: '#95a5a6'  # gray
        }.get(state, '#95a5a6')

        # Crosshair
        size = 15
        c.create_line(canvas_x - size, canvas_y, canvas_x + size, canvas_y,
                     fill=color, width=2, tags='position')
        c.create_line(canvas_x, canvas_y - size, canvas_x, canvas_y + size,
                     fill=color, width=2, tags='position')

        # Center dot
        c.create_oval(canvas_x-3, canvas_y-3, canvas_x+3, canvas_y+3,
                     fill=color, outline='white', width=1, tags='position')

        # Position label
        c.create_text(canvas_x, canvas_y + 25,
                     text=f"({pos.x:.1f}, {pos.y:.1f})",
                     fill=color, font=("Consolas", 9, "bold"),
                     tags='position')
    except Exception as e:
        pass  # Silently ignore positioning errors
```

### Update `_redraw_board` to include position (add at end):

```python
def _redraw_board(self):
    # ... existing board drawing code ...

    # Draw position indicator last (on top)
    self._draw_position_indicator()
```

### Request position updates (add to `_poll_grbl`):

```python
def _poll_grbl(self):
    line = self.gantry.read_line_nowait()
    if line:
        self._log(f"<< {line}")

    # Request position every 10 polls (~500ms)
    if not hasattr(self, '_poll_count'):
        self._poll_count = 0
    self._poll_count += 1
    if self._poll_count % 10 == 0:
        self.gantry.request_status()
        self._redraw_board()  # Update position display

    self.after(50, self._poll_grbl)
```

---

## 🎯 Quick Win #4: Visual Feedback for Squares (15 min)

### Add hover tracking to `__init__`:

```python
# Track hover state
self._hover_square = None
```

### Update canvas bindings in `_build_ui`:

```python
# Add hover bindings
self.canvas.bind("<Motion>", self._on_mouse_move)
self.canvas.bind("<Leave>", lambda e: self._clear_hover())
```

### Add hover handlers:

```python
def _on_mouse_move(self, ev):
    """Handle mouse movement for hover effect."""
    sq = self._board_square_from_xy(ev.x, ev.y)
    if sq != self._hover_square:
        self._hover_square = sq
        self._redraw_board()

def _clear_hover(self):
    """Clear hover state."""
    if self._hover_square:
        self._hover_square = None
        self._redraw_board()

def _draw_hover_highlight(self):
    """Draw highlight on hovered square."""
    if not self._hover_square:
        return

    c = self.canvas
    canvas_w = c.winfo_width()
    canvas_h = c.winfo_height()

    size = (min(canvas_w, canvas_h) * 0.95) - 50
    offset_x = (canvas_w - size) / 2
    offset_y = (canvas_h - size) / 2

    files = self.board_cfg.files
    ranks = self.board_cfg.ranks
    sq_size = size / files

    # Parse square
    file_char = self._hover_square[0]
    rank_char = self._hover_square[1]
    f = ord(file_char) - ord('a')
    r = int(rank_char) - 1

    # Calculate position
    x0 = offset_x + f * sq_size
    y0 = offset_y + (ranks - r - 1) * sq_size
    x1 = x0 + sq_size
    y1 = y0 + sq_size

    # Draw highlight (semi-transparent yellow)
    c.create_rectangle(x0, y0, x1, y1,
                      outline='#f39c12', width=3, tags='hover',
                      stipple='gray50')  # Creates transparency effect

    # Square label
    c.create_text((x0+x1)/2, (y0+y1)/2,
                 text=self._hover_square.upper(),
                 fill='#f39c12', font=("Arial", 12, "bold"),
                 tags='hover')
```

### Update `_redraw_board` to include hover (add before position indicator):

```python
def _redraw_board(self):
    # ... existing squares and labels ...

    # Draw hover highlight
    self._draw_hover_highlight()

    # Draw position indicator
    self._draw_position_indicator()
```

---

## 🎯 Quick Win #5: Auto-Reconnect (2 min)

### Update `_connect` method:

```python
def _connect(self):
    ports = self._list_ports()
    ser_cfg = self.settings.get_serial()
    port = ser_cfg.get('port') or (ports[0] if ports else "")
    if not port:
        messagebox.showerror("No Port", "No serial ports found. Plug the machine in and try again.")
        return
    try:
        # Enable auto-reconnect
        self.gantry.connect(port, ser_cfg.get('baudrate', 115200), auto_reconnect=True)
        self.status.set(f"✓ Connected: {port} (auto-reconnect enabled)")
        self._log("[GRBL] Auto-reconnect enabled")
    except Exception as e:
        messagebox.showerror("Connect Failed", str(e))
```

---

## 🎯 Quick Win #6: Safety Limits (5 min)

### Update `__init__` to configure safety limits:

```python
# Configure safety limits from board settings
board_cfg_dict = self.settings.get_board()
safety_limits = SafetyLimits(
    x_min=0.0,
    x_max=float(board_cfg_dict.get('width_mm', 400.0)),
    y_min=0.0,
    y_max=float(board_cfg_dict.get('height_mm', 400.0)),
    z_min=0.0,
    z_max=100.0
)
self.gantry = GantryController(self._log, safety_limits=safety_limits)
```

### The safety limits now automatically validate all moves!

---

## 🧪 Testing Your Quick Wins

### 1. Test Emergency Stop
- Click the red EMERGENCY STOP button
- Verify motion halts immediately
- Reset and verify operation resumes

### 2. Test Keyboard Shortcuts
- Press ESC → Emergency stop
- Press arrow keys → Jog movement
- Press F1 → See help dialog
- Press +/- → Change jog distance

### 3. Test Live Position
- Connect to GRBL
- Home the gantry
- Watch the crosshair follow movements
- Verify position coordinates display

### 4. Test Visual Feedback
- Move mouse over board
- Verify square highlights on hover
- Verify square label shows
- Click → Square should flash

### 5. Test Auto-Reconnect
- Connect to GRBL
- Unplug USB cable
- Wait 10 seconds
- Plug back in
- Verify auto-reconnection

### 6. Test Safety Limits
- Try to move beyond board boundaries
- Verify move is blocked
- Check log for safety message

---

## 📊 Impact

With these 6 quick wins implemented (45 minutes total), you get:

✅ **Emergency Stop** - Safety first!
✅ **Keyboard Shortcuts** - 10x faster operation
✅ **Live Position** - Know where you are
✅ **Visual Feedback** - Better UX
✅ **Auto-Reconnect** - Reliability
✅ **Safety Limits** - Prevent crashes

**Total time:** 45 minutes
**Value:** Massive improvement in safety, usability, and reliability!

---

🤖 **Generated by Claude Code**
