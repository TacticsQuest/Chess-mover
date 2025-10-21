"""
Script to apply modern styling to the Chess Mover Machine GUI
Run this to update all styling with theme support
"""

import re

def modernize_gui():
    """Apply modern styling to board_window.py"""

    file_path = "ui/board_window.py"

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Fix the servo panel to use theme colors
    # Replace hardcoded #f0f0f0 with self.theme['panel_bg']
    content = re.sub(
        r'servo_frame = ttk\.LabelFrame\(right,',
        r'servo_frame = tk.Frame(right_panel, bg=self.theme["panel_bg"])',
        content
    )

    # Fix lift section background
    content = re.sub(
        r'lift_section = tk\.Frame\(servo_frame, bg="#f0f0f0"',
        r'lift_section = tk.Frame(servo_frame, bg=self.theme["panel_bg"]',
        content
    )

    # Fix grip section background
    content = re.sub(
        r'grip_section = tk\.Frame\(servo_frame, bg="#f0f0f0"',
        r'grip_section = tk.Frame(servo_frame, bg=self.theme["panel_bg"]',
        content
    )

    # Update board drawing to use theme colors
    content = re.sub(
        r'light = "#ddd"\s+dark = "#666"',
        r'light = self.theme["board_light"]\n        dark = self.theme["board_dark"]',
        content
    )

    # Update board border/outline
    content = re.sub(
        r'outline="#333"',
        r'outline=self.theme["board_border"]',
        content
    )

    # Update coordinate labels
    content = re.sub(
        r'fill="#bbb"',
        r'fill=self.theme["text_secondary"]',
        content
    )

    # Fix command log
    content = re.sub(
        r'ttk\.Label\(right, text="Command Log"\)',
        r'tk.Label(right_panel, text="📋 Command Log", font=("Segoe UI", 11, "bold"), bg=self.theme["bg"], fg=self.theme["fg"], anchor="w", padx=15, pady=10)',
        content
    )

    # Fix text log widget
    content = re.sub(
        r'self\.txt_log = tk\.Text\(right, height=15\)\s+self\.txt_log\.pack\(fill=tk\.BOTH, expand=True, padx=6, pady=6\)',
        r'''self.txt_log = tk.Text(
            right_panel,
            height=12,
            bg=self.theme["input_bg"],
            fg=self.theme["input_fg"],
            font=("Consolas", 9),
            relief=tk.FLAT,
            bd=0,
            padx=10,
            pady=10,
            insertbackground=self.theme["accent"]
        )
        self.txt_log.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))''',
        content
    )

    # Fix status bar
    content = re.sub(
        r'stbar = ttk\.Label\(self, textvariable=self\.status, anchor="w"\)',
        r'''status_bar = tk.Frame(self, bg=self.theme["panel_bg"], height=30)
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
        )''',
        content
    )

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("✓ GUI modernization complete!")
    print("  - Theme colors applied")
    print("  - Modern styling updated")
    print("  - Board rendering updated")
    print("  - Command log styled")
    print("  - Status bar modernized")

if __name__ == "__main__":
    modernize_gui()
