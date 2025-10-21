import os
import yaml
from typing import Any, Dict, List, Optional

SETTINGS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "settings.yaml")

DEFAULTS: Dict[str, Any] = {
    'profiles': {
        'active': 'Default Board',
        'saved': [
            {
                'name': 'Default Board',
                'board': {
                    'files': 8,
                    'ranks': 8,
                    'width_mm': 400.0,
                    'height_mm': 400.0,
                    'origin_x_mm': 0.0,
                    'origin_y_mm': 0.0,
                    'feedrate_mm_min': 2000
                },
                'pieces': {
                    'king': {'height_mm': 95, 'base_diameter_mm': 38, 'grip_angle': 90},
                    'queen': {'height_mm': 85, 'base_diameter_mm': 35, 'grip_angle': 85},
                    'bishop': {'height_mm': 70, 'base_diameter_mm': 32, 'grip_angle': 80},
                    'knight': {'height_mm': 60, 'base_diameter_mm': 32, 'grip_angle': 80},
                    'rook': {'height_mm': 55, 'base_diameter_mm': 32, 'grip_angle': 75},
                    'pawn': {'height_mm': 50, 'base_diameter_mm': 28, 'grip_angle': 70}
                }
            }
        ]
    }
}

class Settings:
    def __init__(self):
        self.data: Dict[str, Any] = {}
        self.load()

    def load(self):
        global DEFAULTS
        if not os.path.exists(SETTINGS_PATH):
            os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
            with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
                yaml.safe_dump(DEFAULTS, f)
        with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
            self.data = yaml.safe_load(f) or {}

        # Ensure profiles structure exists
        if 'profiles' not in self.data:
            self.data['profiles'] = DEFAULTS['profiles']
            self.save()

    def save(self):
        with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
            yaml.safe_dump(self.data, f, sort_keys=False)

    # Legacy convenience getters/setters (now use active profile)
    def get_serial(self):
        return self.data.get('serial', {})

    def set_serial(self, d):
        self.data['serial'] = d

    def get_board(self):
        """Get board config from active profile."""
        profile = self.get_active_profile()
        if profile:
            return profile.get('board', {})
        return {}

    def set_board(self, d):
        """Update board config in active profile."""
        profile_name = self.get_active_profile_name()
        self.update_profile_board(profile_name, d)

    def get_safety(self):
        return self.data.get('safety', {
            'max_speed_mm_min': 5000,
            'min_speed_mm_min': 100,
            'enable_speed_limit': True
        })

    def set_safety(self, d):
        self.data['safety'] = d

    def get_machine(self):
        """Get machine workspace limits (hard-coded physical limits)."""
        return self.data.get('machine', {
            'x_min': 0.0,
            'x_max': 450.0,
            'y_min': 0.0,
            'y_max': 450.0,
            'z_min': 0.0,
            'z_max': 100.0
        })

    def set_machine(self, d):
        self.data['machine'] = d

    # Profile management methods
    def get_profiles(self):
        """Get all profiles data."""
        return self.data.get('profiles', DEFAULTS['profiles'])

    def set_profiles(self, d):
        """Set all profiles data."""
        self.data['profiles'] = d

    def get_profile_names(self) -> List[str]:
        """Get list of all profile names."""
        profiles = self.get_profiles()
        saved = profiles.get('saved', [])
        return [p['name'] for p in saved]

    def get_active_profile_name(self) -> str:
        """Get name of active profile."""
        profiles = self.get_profiles()
        return profiles.get('active', 'Default Board')

    def set_active_profile_name(self, name: str) -> bool:
        """
        Set active profile by name.

        Args:
            name: Profile name to activate

        Returns:
            True if profile exists and was activated, False otherwise
        """
        # Check if profile exists
        if not self.get_profile_by_name(name):
            return False

        if 'profiles' not in self.data:
            self.data['profiles'] = DEFAULTS['profiles']
        self.data['profiles']['active'] = name
        return True

    def get_active_profile(self) -> Optional[Dict[str, Any]]:
        """Get the active profile data."""
        active_name = self.get_active_profile_name()
        return self.get_profile_by_name(active_name)

    def get_profile_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific profile by name."""
        profiles = self.get_profiles()
        saved = profiles.get('saved', [])
        for profile in saved:
            if profile['name'] == name:
                return profile
        return None

    def create_profile(self, name: str, board_cfg: Dict[str, Any], pieces_cfg: Optional[Dict[str, Any]] = None) -> bool:
        """
        Create a new profile.

        Args:
            name: Profile name
            board_cfg: Board configuration dict
            pieces_cfg: Optional piece settings dict

        Returns:
            True if created, False if name already exists
        """
        # Check if profile already exists
        if self.get_profile_by_name(name):
            return False

        # Create new profile
        new_profile = {
            'name': name,
            'board': board_cfg,
            'pieces': pieces_cfg or DEFAULTS['profiles']['saved'][0]['pieces']
        }

        # Add to saved profiles
        if 'profiles' not in self.data:
            self.data['profiles'] = DEFAULTS['profiles']

        if 'saved' not in self.data['profiles']:
            self.data['profiles']['saved'] = []

        self.data['profiles']['saved'].append(new_profile)
        return True

    def update_profile_board(self, name: str, board_cfg: Dict[str, Any]) -> bool:
        """
        Update board configuration for a specific profile.

        Args:
            name: Profile name
            board_cfg: New board configuration

        Returns:
            True if updated, False if profile not found
        """
        profile = self.get_profile_by_name(name)
        if not profile:
            return False

        # Find and update the profile
        profiles = self.get_profiles()
        saved = profiles.get('saved', [])
        for i, p in enumerate(saved):
            if p['name'] == name:
                self.data['profiles']['saved'][i]['board'] = board_cfg
                return True

        return False

    def update_profile_pieces(self, name: str, pieces_cfg: Dict[str, Any]) -> bool:
        """
        Update piece settings for a specific profile.

        Args:
            name: Profile name
            pieces_cfg: New piece configuration

        Returns:
            True if updated, False if profile not found
        """
        profile = self.get_profile_by_name(name)
        if not profile:
            return False

        # Find and update the profile
        profiles = self.get_profiles()
        saved = profiles.get('saved', [])
        for i, p in enumerate(saved):
            if p['name'] == name:
                self.data['profiles']['saved'][i]['pieces'] = pieces_cfg
                return True

        return False

    def delete_profile(self, name: str) -> bool:
        """
        Delete a profile by name.

        Args:
            name: Profile name to delete

        Returns:
            True if deleted, False if not found or is active profile
        """
        # Don't allow deleting active profile
        if name == self.get_active_profile_name():
            return False

        profiles = self.get_profiles()
        saved = profiles.get('saved', [])

        # Find and remove
        for i, p in enumerate(saved):
            if p['name'] == name:
                self.data['profiles']['saved'].pop(i)
                return True

        return False

    def rename_profile(self, old_name: str, new_name: str) -> bool:
        """
        Rename a profile.

        Args:
            old_name: Current profile name
            new_name: New profile name

        Returns:
            True if renamed, False if profile not found or new name exists
        """
        # Check if new name already exists
        if self.get_profile_by_name(new_name):
            return False

        # Find and rename
        profiles = self.get_profiles()
        saved = profiles.get('saved', [])
        for i, p in enumerate(saved):
            if p['name'] == old_name:
                self.data['profiles']['saved'][i]['name'] = new_name

                # Update active profile name if needed
                if self.get_active_profile_name() == old_name:
                    self.set_active_profile_name(new_name)

                return True

        return False

    def get_piece_settings(self, profile_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get piece settings for a profile.

        Args:
            profile_name: Profile name (defaults to active profile)

        Returns:
            Piece settings dict
        """
        if profile_name is None:
            profile_name = self.get_active_profile_name()

        profile = self.get_profile_by_name(profile_name)
        if profile:
            return profile.get('pieces', DEFAULTS['profiles']['saved'][0]['pieces'])

        return DEFAULTS['profiles']['saved'][0]['pieces']
