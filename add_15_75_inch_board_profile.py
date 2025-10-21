"""
Add a profile for a 15.75 inch chessboard to the Chess Mover Machine settings.

15.75 inches = 400.05mm
Square size = 15.75 / 8 = 1.96875 inches = 50mm per square
"""

from logic.profiles import Settings

# Board dimensions
BOARD_SIZE_INCHES = 15.75
BOARD_SIZE_MM = BOARD_SIZE_INCHES * 25.4  # 400.05mm
SQUARE_SIZE_MM = BOARD_SIZE_MM / 8  # 50.00625mm per square

# Create the profile
profile_name = "15.75 inch Board"

board_config = {
    'files': 8,
    'ranks': 8,
    'width_mm': round(BOARD_SIZE_MM, 2),   # 400.05mm
    'height_mm': round(BOARD_SIZE_MM, 2),  # 400.05mm
    'origin_x_mm': 0.0,  # Will be calibrated later
    'origin_y_mm': 0.0,  # Will be calibrated later
    'feedrate_mm_min': 2000
}

# Piece settings (standard tournament pieces for 2" squares)
pieces_config = {
    'king': {'height_mm': 95, 'base_diameter_mm': 38, 'grip_angle': 90},
    'queen': {'height_mm': 85, 'base_diameter_mm': 35, 'grip_angle': 85},
    'bishop': {'height_mm': 70, 'base_diameter_mm': 32, 'grip_angle': 80},
    'knight': {'height_mm': 60, 'base_diameter_mm': 32, 'grip_angle': 80},
    'rook': {'height_mm': 55, 'base_diameter_mm': 32, 'grip_angle': 75},
    'pawn': {'height_mm': 50, 'base_diameter_mm': 28, 'grip_angle': 70}
}

# Load settings
settings = Settings()

# Check if profile already exists
existing = settings.get_profile_by_name(profile_name)

if existing:
    print(f"Profile '{profile_name}' already exists!")
    print("Current configuration:")
    print(f"  Board size: {existing['board']['width_mm']}mm x {existing['board']['height_mm']}mm")
    print(f"  Square size: {existing['board']['width_mm'] / 8:.2f}mm")
    print()

    # Update it
    response = input("Do you want to update it? (y/n): ").strip().lower()
    if response == 'y':
        settings.update_profile_board(profile_name, board_config)
        settings.update_profile_pieces(profile_name, pieces_config)
        settings.save()
        print(f"\n[OK] Profile '{profile_name}' updated!")
    else:
        print("\nNo changes made.")
else:
    # Create new profile
    success = settings.create_profile(profile_name, board_config, pieces_config)

    if success:
        settings.save()
        print(f"[OK] Profile '{profile_name}' created successfully!")
        print()
        print("Board Configuration:")
        print(f"  Board size: {board_config['width_mm']}mm x {board_config['height_mm']}mm")
        print(f"             ({BOARD_SIZE_INCHES}\" x {BOARD_SIZE_INCHES}\")")
        print(f"  Square size: {SQUARE_SIZE_MM:.2f}mm ({BOARD_SIZE_INCHES / 8:.5f}\")")
        print(f"  Total squares: 8x8 = 64")
        print()
        print("Next steps:")
        print("1. Launch the Chess Mover application")
        print(f"2. Select '{profile_name}' from the profile dropdown")
        print("3. Calibrate the board origin (use machine controls to position at A1)")
        print("4. Test movement to verify accuracy")
    else:
        print(f"[FAIL] Failed to create profile '{profile_name}'")

print()
print("All available profiles:")
for name in settings.get_profile_names():
    active_marker = " (ACTIVE)" if name == settings.get_active_profile_name() else ""
    print(f"  - {name}{active_marker}")
