import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Callable, Dict, Any, Optional

class ProfileManagerWindow(tk.Toplevel):
    """Profile management window for creating, editing, and switching between board profiles."""

    def __init__(self, master, settings, on_profile_changed: Callable[[str], None]):
        super().__init__(master)
        self.title("Profile Manager")
        self.geometry("700x600")
        self.resizable(False, False)

        self.settings = settings
        self.on_profile_changed = on_profile_changed

        self._build_ui()
        self._refresh_profile_list()

    def _build_ui(self):
        """Build the profile manager UI."""
        # Header
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=15, pady=15)

        ttk.Label(
            header,
            text="📁 Board Profiles",
            font=("Segoe UI", 14, "bold")
        ).pack(side=tk.LEFT)

        # Active profile display
        active_frame = ttk.Frame(self)
        active_frame.pack(fill=tk.X, padx=15, pady=(0, 10))

        ttk.Label(
            active_frame,
            text="Active Profile:",
            font=("Segoe UI", 10, "bold")
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.active_label = ttk.Label(
            active_frame,
            text=self.settings.get_active_profile_name(),
            font=("Segoe UI", 10),
            foreground="#3498db"
        )
        self.active_label.pack(side=tk.LEFT)

        # Profile list
        list_frame = ttk.LabelFrame(self, text="Saved Profiles")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))

        # Listbox with scrollbar
        scroll_frame = ttk.Frame(list_frame)
        scroll_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        scrollbar = ttk.Scrollbar(scroll_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.profile_listbox = tk.Listbox(
            scroll_frame,
            font=("Segoe UI", 10),
            height=12,
            yscrollcommand=scrollbar.set,
            selectmode=tk.SINGLE
        )
        self.profile_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.profile_listbox.yview)

        # Bind double-click to activate profile
        self.profile_listbox.bind("<Double-Button-1>", lambda e: self._activate_profile())

        # Profile actions
        actions_frame = ttk.Frame(list_frame)
        actions_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        ttk.Button(
            actions_frame,
            text="✓ Activate",
            command=self._activate_profile
        ).grid(row=0, column=0, padx=3, sticky="ew")

        ttk.Button(
            actions_frame,
            text="✏ Edit",
            command=self._edit_profile
        ).grid(row=0, column=1, padx=3, sticky="ew")

        ttk.Button(
            actions_frame,
            text="📋 Duplicate",
            command=self._duplicate_profile
        ).grid(row=0, column=2, padx=3, sticky="ew")

        ttk.Button(
            actions_frame,
            text="✏ Rename",
            command=self._rename_profile
        ).grid(row=1, column=0, padx=3, pady=(5,0), sticky="ew")

        ttk.Button(
            actions_frame,
            text="🗑 Delete",
            command=self._delete_profile
        ).grid(row=1, column=1, padx=3, pady=(5,0), sticky="ew")

        ttk.Button(
            actions_frame,
            text="➕ New Profile",
            command=self._create_new_profile
        ).grid(row=1, column=2, padx=3, pady=(5,0), sticky="ew")

        # Configure column weights
        for i in range(3):
            actions_frame.columnconfigure(i, weight=1)

        # Bottom buttons
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(fill=tk.X, padx=15, pady=(0, 15))

        ttk.Button(
            bottom_frame,
            text="Close",
            command=self.destroy
        ).pack(side=tk.RIGHT)

    def _refresh_profile_list(self):
        """Refresh the profile listbox."""
        self.profile_listbox.delete(0, tk.END)

        profile_names = self.settings.get_profile_names()
        active_name = self.settings.get_active_profile_name()

        for name in profile_names:
            display_text = f"{name}"
            if name == active_name:
                display_text += " ★ (Active)"
            self.profile_listbox.insert(tk.END, display_text)

        # Update active label
        self.active_label.config(text=active_name)

    def _get_selected_profile_name(self) -> Optional[str]:
        """Get the currently selected profile name (without the active marker)."""
        selection = self.profile_listbox.curselection()
        if not selection:
            return None

        text = self.profile_listbox.get(selection[0])
        # Remove " ★ (Active)" if present
        name = text.replace(" ★ (Active)", "").strip()
        return name

    def _activate_profile(self):
        """Activate the selected profile."""
        name = self._get_selected_profile_name()
        if not name:
            messagebox.showwarning("No Selection", "Please select a profile to activate.")
            return

        # Set as active
        self.settings.set_active_profile_name(name)
        self.settings.save()

        # Refresh UI
        self._refresh_profile_list()

        # Notify parent
        self.on_profile_changed(name)

        messagebox.showinfo("Profile Activated", f"'{name}' is now active.\n\nThe board has been reloaded with this profile's settings.")

    def _edit_profile(self):
        """Edit the selected profile."""
        name = self._get_selected_profile_name()
        if not name:
            messagebox.showwarning("No Selection", "Please select a profile to edit.")
            return

        profile = self.settings.get_profile_by_name(name)
        if not profile:
            return

        # Open profile editor
        ProfileEditorWindow(self, self.settings, name, lambda: self._refresh_profile_list())

    def _duplicate_profile(self):
        """Duplicate the selected profile."""
        name = self._get_selected_profile_name()
        if not name:
            messagebox.showwarning("No Selection", "Please select a profile to duplicate.")
            return

        profile = self.settings.get_profile_by_name(name)
        if not profile:
            return

        # Ask for new name
        new_name = simpledialog.askstring(
            "Duplicate Profile",
            f"Enter name for duplicate of '{name}':",
            initialvalue=f"{name} (Copy)"
        )

        if not new_name:
            return

        new_name = new_name.strip()

        # Create duplicate
        success = self.settings.create_profile(
            new_name,
            profile['board'].copy(),
            profile.get('pieces', {}).copy()
        )

        if success:
            self.settings.save()
            self._refresh_profile_list()
            messagebox.showinfo("Profile Duplicated", f"Profile '{new_name}' created successfully!")
        else:
            messagebox.showerror("Duplicate Failed", f"A profile named '{new_name}' already exists.")

    def _rename_profile(self):
        """Rename the selected profile."""
        old_name = self._get_selected_profile_name()
        if not old_name:
            messagebox.showwarning("No Selection", "Please select a profile to rename.")
            return

        # Ask for new name
        new_name = simpledialog.askstring(
            "Rename Profile",
            f"Enter new name for '{old_name}':",
            initialvalue=old_name
        )

        if not new_name:
            return

        new_name = new_name.strip()

        if new_name == old_name:
            return

        # Rename
        success = self.settings.rename_profile(old_name, new_name)

        if success:
            self.settings.save()
            self._refresh_profile_list()
            messagebox.showinfo("Profile Renamed", f"Profile renamed to '{new_name}'")
        else:
            messagebox.showerror("Rename Failed", f"A profile named '{new_name}' already exists.")

    def _delete_profile(self):
        """Delete the selected profile."""
        name = self._get_selected_profile_name()
        if not name:
            messagebox.showwarning("No Selection", "Please select a profile to delete.")
            return

        # Confirm deletion
        result = messagebox.askyesno(
            "Delete Profile",
            f"Are you sure you want to delete '{name}'?\n\nThis cannot be undone.",
            icon='warning'
        )

        if not result:
            return

        # Try to delete
        success = self.settings.delete_profile(name)

        if success:
            self.settings.save()
            self._refresh_profile_list()
            messagebox.showinfo("Profile Deleted", f"Profile '{name}' has been deleted.")
        else:
            messagebox.showerror("Delete Failed", f"Cannot delete active profile.\n\nSwitch to another profile first.")

    def _create_new_profile(self):
        """Create a new profile from scratch."""
        # Ask for profile name
        name = simpledialog.askstring(
            "New Profile",
            "Enter name for new profile:"
        )

        if not name:
            return

        name = name.strip()

        # Use default board config
        from logic.profiles import DEFAULTS
        default_board = DEFAULTS['profiles']['saved'][0]['board'].copy()

        # Create profile
        success = self.settings.create_profile(name, default_board)

        if success:
            self.settings.save()
            self._refresh_profile_list()
            messagebox.showinfo("Profile Created", f"Profile '{name}' created!\n\nYou can now edit it to customize settings.")
        else:
            messagebox.showerror("Creation Failed", f"A profile named '{name}' already exists.")


class ProfileEditorWindow(tk.Toplevel):
    """Editor for a single profile's board and piece settings."""

    def __init__(self, master, settings, profile_name: str, on_save_callback: Callable[[], None]):
        super().__init__(master)
        self.title(f"Edit Profile: {profile_name}")
        self.geometry("550x700")
        self.resizable(False, False)

        self.settings = settings
        self.profile_name = profile_name
        self.on_save_callback = on_save_callback

        profile = settings.get_profile_by_name(profile_name)
        if not profile:
            messagebox.showerror("Error", f"Profile '{profile_name}' not found.")
            self.destroy()
            return

        self.board_cfg = profile['board']
        self.pieces_cfg = profile.get('pieces', {})

        self._build_ui()

    def _build_ui(self):
        """Build the profile editor UI."""
        # Header
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=15, pady=15)

        ttk.Label(
            header,
            text=f"📝 Editing: {self.profile_name}",
            font=("Segoe UI", 12, "bold")
        ).pack()

        # Notebook for tabs
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))

        # Board settings tab
        board_tab = ttk.Frame(notebook)
        notebook.add(board_tab, text="Board Settings")
        self._build_board_tab(board_tab)

        # Piece settings tab
        pieces_tab = ttk.Frame(notebook)
        notebook.add(pieces_tab, text="Piece Settings")
        self._build_pieces_tab(pieces_tab)

        # Bottom buttons
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(fill=tk.X, padx=15, pady=(0, 15))

        ttk.Button(
            bottom_frame,
            text="Cancel",
            command=self.destroy
        ).pack(side=tk.RIGHT, padx=(5, 0))

        ttk.Button(
            bottom_frame,
            text="Save Changes",
            command=self._save_changes
        ).pack(side=tk.RIGHT)

    def _build_board_tab(self, parent):
        """Build the board settings tab."""
        # Board config frame
        frame = ttk.LabelFrame(parent, text="Board Configuration")
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.board_entries = {}

        fields = [
            ("files", "Files (columns)", self.board_cfg.get('files', 8)),
            ("ranks", "Ranks (rows)", self.board_cfg.get('ranks', 8)),
            ("width_mm", "Board Width (mm)", self.board_cfg.get('width_mm', 400.0)),
            ("height_mm", "Board Height (mm)", self.board_cfg.get('height_mm', 400.0)),
            ("origin_x_mm", "Origin X - A1 center (mm)", self.board_cfg.get('origin_x_mm', 0.0)),
            ("origin_y_mm", "Origin Y - A1 center (mm)", self.board_cfg.get('origin_y_mm', 0.0)),
            ("feedrate_mm_min", "Default Feedrate (mm/min)", self.board_cfg.get('feedrate_mm_min', 2000)),
        ]

        for i, (key, label, value) in enumerate(fields):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky="w", padx=10, pady=5)
            entry = ttk.Entry(frame, width=20)
            entry.grid(row=i, column=1, sticky="ew", padx=10, pady=5)
            entry.insert(0, str(value))
            self.board_entries[key] = entry

        frame.columnconfigure(1, weight=1)

    def _build_pieces_tab(self, parent):
        """Build the piece settings tab (for future gripper integration)."""
        # Info label
        info = ttk.Label(
            parent,
            text="Configure piece dimensions for gripper control.\n"
                 "These settings will be used when the gripper is installed.",
            font=("Segoe UI", 9),
            justify=tk.LEFT,
            wraplength=500
        )
        info.pack(padx=10, pady=10)

        # Pieces config frame
        frame = ttk.LabelFrame(parent, text="Piece Dimensions")
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Create scrollable frame
        canvas = tk.Canvas(frame, height=400)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Piece entries
        self.piece_entries = {}

        pieces = ['king', 'queen', 'bishop', 'knight', 'rook', 'pawn']

        for piece in pieces:
            piece_cfg = self.pieces_cfg.get(piece, {
                'height_mm': 0,
                'base_diameter_mm': 0,
                'grip_angle': 90
            })

            piece_frame = ttk.LabelFrame(scrollable_frame, text=piece.capitalize())
            piece_frame.pack(fill=tk.X, padx=5, pady=5)

            self.piece_entries[piece] = {}

            # Height
            ttk.Label(piece_frame, text="Height (mm):").grid(row=0, column=0, sticky="w", padx=5, pady=3)
            height_entry = ttk.Entry(piece_frame, width=10)
            height_entry.grid(row=0, column=1, sticky="w", padx=5, pady=3)
            height_entry.insert(0, str(piece_cfg.get('height_mm', 0)))
            self.piece_entries[piece]['height_mm'] = height_entry

            # Base diameter
            ttk.Label(piece_frame, text="Base Diameter (mm):").grid(row=1, column=0, sticky="w", padx=5, pady=3)
            diameter_entry = ttk.Entry(piece_frame, width=10)
            diameter_entry.grid(row=1, column=1, sticky="w", padx=5, pady=3)
            diameter_entry.insert(0, str(piece_cfg.get('base_diameter_mm', 0)))
            self.piece_entries[piece]['base_diameter_mm'] = diameter_entry

            # Grip angle
            ttk.Label(piece_frame, text="Grip Angle (°):").grid(row=2, column=0, sticky="w", padx=5, pady=3)
            angle_entry = ttk.Entry(piece_frame, width=10)
            angle_entry.grid(row=2, column=1, sticky="w", padx=5, pady=3)
            angle_entry.insert(0, str(piece_cfg.get('grip_angle', 90)))
            self.piece_entries[piece]['grip_angle'] = angle_entry

    def _save_changes(self):
        """Save profile changes."""
        try:
            # Collect board settings
            new_board_cfg = {}
            for key, entry in self.board_entries.items():
                value = entry.get().strip()
                if key in ['files', 'ranks', 'feedrate_mm_min']:
                    new_board_cfg[key] = int(value)
                else:
                    new_board_cfg[key] = float(value)

            # Collect piece settings
            new_pieces_cfg = {}
            for piece, entries in self.piece_entries.items():
                new_pieces_cfg[piece] = {
                    'height_mm': float(entries['height_mm'].get().strip() or 0),
                    'base_diameter_mm': float(entries['base_diameter_mm'].get().strip() or 0),
                    'grip_angle': int(entries['grip_angle'].get().strip() or 90)
                }

            # Update profile
            self.settings.update_profile_board(self.profile_name, new_board_cfg)
            self.settings.update_profile_pieces(self.profile_name, new_pieces_cfg)
            self.settings.save()

            # Callback to refresh parent
            if self.on_save_callback:
                self.on_save_callback()

            messagebox.showinfo("Changes Saved", f"Profile '{self.profile_name}' updated successfully!")
            self.destroy()

        except ValueError as e:
            messagebox.showerror("Invalid Input", f"Please check your inputs:\n\n{e}")
