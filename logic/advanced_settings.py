"""
Advanced Settings Loader

Loads and manages advanced configuration settings for experimental features.
"""

import os
import yaml
from dataclasses import dataclass
from typing import Optional

from logic.tool_pusher import ToolConfig, ToolType


@dataclass
class EdgePushSettings:
    """Settings for edge push feature."""
    enabled: bool
    push_speed_mm_min: int
    push_distance_mm: float


@dataclass
class ToolPusherSettings:
    """Settings for tool pusher feature."""
    enabled: bool
    tool_holder_square: str
    tool_width_mm: float
    tool_length_mm: float
    grip_offset_mm: float
    push_offset_mm: float
    push_speed_mm_min: int
    pickup_speed_mm_min: int


@dataclass
class StorageSettings:
    """Settings for storage management."""
    default_strategy: str
    alert_at_percent: int
    auto_clear: bool


@dataclass
class AISettings:
    """Settings for AI features."""
    auto_strategy_selection: bool
    adaptive_learning: bool


@dataclass
class MultiBoardSettings:
    """Settings for multi-board coordination."""
    enabled: bool
    share_storage: bool
    network_enabled: bool
    network_port: int


@dataclass
class ExperimentalSettings:
    """Settings for experimental features."""
    detailed_logging: bool
    simulation_mode: bool
    profiling_enabled: bool


class AdvancedSettings:
    """
    Manages advanced configuration settings.

    Loads settings from config/advanced_settings.yaml
    """

    DEFAULT_CONFIG_PATH = "config/advanced_settings.yaml"

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize advanced settings.

        Args:
            config_path: Path to config file (default: config/advanced_settings.yaml)
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.config = self._load_config()

        # Parse settings
        self.edge_push = self._parse_edge_push()
        self.tool_pusher = self._parse_tool_pusher()
        self.storage = self._parse_storage()
        self.ai = self._parse_ai()
        self.multi_board = self._parse_multi_board()
        self.experimental = self._parse_experimental()

    def _load_config(self) -> dict:
        """Load configuration from YAML file."""
        # Try to find config file
        config_locations = [
            self.config_path,
            os.path.join(os.path.dirname(os.path.dirname(__file__)), self.config_path),
            os.path.join(os.getcwd(), self.config_path),
        ]

        for location in config_locations:
            if os.path.exists(location):
                with open(location, 'r') as f:
                    return yaml.safe_load(f)

        # Return defaults if no config file found
        return self._get_default_config()

    def _get_default_config(self) -> dict:
        """Get default configuration."""
        return {
            'capture_removal': {
                'primary_strategy': 'smart_storage',
                'edge_push': {
                    'enabled': False,
                    'push_speed_mm_min': 300,
                    'push_distance_mm': 30.0
                },
                'tool_pusher': {
                    'enabled': False,
                    'tool_holder_square': 'a9',
                    'tool_width_mm': 50.0,
                    'tool_length_mm': 100.0,
                    'grip_offset_mm': 30.0,
                    'push_offset_mm': 15.0,
                    'push_speed_mm_min': 300,
                    'pickup_speed_mm_min': 1000
                }
            },
            'storage': {
                'default_strategy': 'BY_COLOR',
                'alert_at_percent': 75,
                'auto_clear': True
            },
            'ai': {
                'auto_strategy_selection': False,
                'adaptive_learning': False
            },
            'multi_board': {
                'enabled': False,
                'share_storage': False,
                'network': {
                    'enabled': False,
                    'port': 8080
                }
            },
            'experimental': {
                'detailed_logging': False,
                'simulation_mode': False,
                'profiling_enabled': False
            }
        }

    def _parse_edge_push(self) -> EdgePushSettings:
        """Parse edge push settings."""
        edge_push_config = self.config.get('capture_removal', {}).get('edge_push', {})
        return EdgePushSettings(
            enabled=edge_push_config.get('enabled', False),
            push_speed_mm_min=edge_push_config.get('push_speed_mm_min', 300),
            push_distance_mm=edge_push_config.get('push_distance_mm', 30.0)
        )

    def _parse_tool_pusher(self) -> ToolPusherSettings:
        """Parse tool pusher settings."""
        tool_config = self.config.get('capture_removal', {}).get('tool_pusher', {})
        return ToolPusherSettings(
            enabled=tool_config.get('enabled', False),
            tool_holder_square=tool_config.get('tool_holder_square', 'a9'),
            tool_width_mm=tool_config.get('tool_width_mm', 50.0),
            tool_length_mm=tool_config.get('tool_length_mm', 100.0),
            grip_offset_mm=tool_config.get('grip_offset_mm', 30.0),
            push_offset_mm=tool_config.get('push_offset_mm', 15.0),
            push_speed_mm_min=tool_config.get('push_speed_mm_min', 300),
            pickup_speed_mm_min=tool_config.get('pickup_speed_mm_min', 1000)
        )

    def _parse_storage(self) -> StorageSettings:
        """Parse storage settings."""
        storage_config = self.config.get('storage', {})
        return StorageSettings(
            default_strategy=storage_config.get('default_strategy', 'BY_COLOR'),
            alert_at_percent=storage_config.get('alert_at_percent', 75),
            auto_clear=storage_config.get('auto_clear', True)
        )

    def _parse_ai(self) -> AISettings:
        """Parse AI settings."""
        ai_config = self.config.get('ai', {})
        return AISettings(
            auto_strategy_selection=ai_config.get('auto_strategy_selection', False),
            adaptive_learning=ai_config.get('adaptive_learning', False)
        )

    def _parse_multi_board(self) -> MultiBoardSettings:
        """Parse multi-board settings."""
        multi_config = self.config.get('multi_board', {})
        network_config = multi_config.get('network', {})
        return MultiBoardSettings(
            enabled=multi_config.get('enabled', False),
            share_storage=multi_config.get('share_storage', False),
            network_enabled=network_config.get('enabled', False),
            network_port=network_config.get('port', 8080)
        )

    def _parse_experimental(self) -> ExperimentalSettings:
        """Parse experimental settings."""
        exp_config = self.config.get('experimental', {})
        return ExperimentalSettings(
            detailed_logging=exp_config.get('detailed_logging', False),
            simulation_mode=exp_config.get('simulation_mode', False),
            profiling_enabled=exp_config.get('profiling_enabled', False)
        )

    def get_tool_config(self) -> Optional[ToolConfig]:
        """
        Get tool configuration if tool pusher is enabled.

        Returns:
            ToolConfig or None if disabled
        """
        if not self.tool_pusher.enabled:
            return None

        return ToolConfig(
            tool_type=ToolType.PUSHER,
            holder_square=self.tool_pusher.tool_holder_square,
            width_mm=self.tool_pusher.tool_width_mm,
            length_mm=self.tool_pusher.tool_length_mm,
            grip_offset_mm=self.tool_pusher.grip_offset_mm,
            push_offset_mm=self.tool_pusher.push_offset_mm,
            enabled=True
        )

    def save_config(self, config_path: Optional[str] = None):
        """
        Save current settings to file.

        Args:
            config_path: Path to save to (default: current config path)
        """
        save_path = config_path or self.config_path

        # Ensure directory exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        with open(save_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)

    def set_edge_push_enabled(self, enabled: bool):
        """Enable or disable edge push."""
        self.edge_push.enabled = enabled
        self.config.setdefault('capture_removal', {}).setdefault('edge_push', {})['enabled'] = enabled

    def set_tool_pusher_enabled(self, enabled: bool):
        """Enable or disable tool pusher."""
        self.tool_pusher.enabled = enabled
        self.config.setdefault('capture_removal', {}).setdefault('tool_pusher', {})['enabled'] = enabled

    def is_edge_push_enabled(self) -> bool:
        """Check if edge push is enabled."""
        return self.edge_push.enabled

    def is_tool_pusher_enabled(self) -> bool:
        """Check if tool pusher is enabled."""
        return self.tool_pusher.enabled
