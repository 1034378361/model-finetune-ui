"""Configuration manager for water quality parameters and feature stations."""

import json
import logging
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Saved configs directory name
SAVED_CONFIGS_DIR = "saved_configs"

# Default configuration values
DEFAULT_WATER_PARAMS = [
    "turbidity",
    "ss",
    "sd",
    "do",
    "codmn",
    "codcr",
    "chla",
    "tn",
    "tp",
    "chroma",
    "nh3n",
]
DEFAULT_FEATURE_STATIONS = [f"STZ{i}" for i in range(1, 27)]

# Configuration file version
CONFIG_VERSION = 1


class ConfigurationManager:
    """Manages application configuration for water quality parameters and feature stations."""

    def __init__(self, config_path: str | None = None):
        """
        Initialize configuration manager.

        Args:
            config_path: Optional custom path to config file. If None, uses default location.
        """
        self._water_params: list[str] = []
        self._feature_stations: list[str] = []
        self._config_path: Path | None = None

        # Determine config file path
        if config_path:
            self._config_path = Path(config_path)
        else:
            self._config_path = self._get_default_config_path()

        # Load configuration (will use defaults if file doesn't exist)
        self.load_config()

    def _get_default_config_path(self) -> Path:
        """
        Get default configuration file path based on OS.

        Returns:
            Path to configuration file
        """
        if os.name == "nt":  # Windows
            config_dir = Path(os.environ.get("APPDATA", "")) / "model_finetune_ui"
        else:  # Linux/Mac
            config_dir = Path.home() / ".config" / "model_finetune_ui"

        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "config.json"

    def get_water_params(self) -> list[str]:
        """
        Get water quality parameters list.

        Returns:
            List of water quality parameter names
        """
        return self._water_params.copy()

    def set_water_params(self, params: list[str]) -> None:
        """
        Set water quality parameters list.

        Args:
            params: List of water quality parameter names
        """
        self._water_params = params.copy()

    def get_feature_stations(self) -> list[str]:
        """
        Get feature stations list.

        Returns:
            List of feature station names
        """
        return self._feature_stations.copy()

    def set_feature_stations(self, stations: list[str]) -> None:
        """
        Set feature stations list.

        Args:
            stations: List of feature station names
        """
        self._feature_stations = stations.copy()

    def load_config(self) -> bool:
        """
        Load configuration from file.

        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            if not self._config_path or not self._config_path.exists():
                logger.info(
                    f"Config file not found at {self._config_path}, using defaults"
                )
                self.reset_to_defaults()
                return False

            with open(self._config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)

            # Validate version
            version = config_data.get("version", 1)
            if version != CONFIG_VERSION:
                logger.warning(
                    f"Config version mismatch: expected {CONFIG_VERSION}, got {version}"
                )

            # Load water parameters
            self._water_params = config_data.get(
                "water_params", DEFAULT_WATER_PARAMS.copy()
            )

            # Load feature stations
            self._feature_stations = config_data.get(
                "feature_stations", DEFAULT_FEATURE_STATIONS.copy()
            )

            logger.info(f"Configuration loaded from {self._config_path}")
            return True

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse config file: {e}")
            self.reset_to_defaults()
            return False
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self.reset_to_defaults()
            return False

    def save_config(self) -> bool:
        """
        Save configuration to file.

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            if not self._config_path:
                logger.error("Config path not set")
                return False

            # Ensure directory exists
            self._config_path.parent.mkdir(parents=True, exist_ok=True)

            config_data = {
                "version": CONFIG_VERSION,
                "water_params": self._water_params,
                "feature_stations": self._feature_stations,
            }

            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Configuration saved to {self._config_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False

    def reset_to_defaults(self) -> None:
        """Reset configuration to default values."""
        self._water_params = DEFAULT_WATER_PARAMS.copy()
        self._feature_stations = DEFAULT_FEATURE_STATIONS.copy()
        logger.info("Configuration reset to defaults")

    def validate_config(self) -> tuple[bool, list[str]]:
        """
        Validate configuration.

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors: list[str] = []

        # Validate water parameters
        if not self._water_params:
            errors.append("Water parameters list cannot be empty")
        else:
            # Check for duplicates
            if len(self._water_params) != len(set(self._water_params)):
                errors.append("Water parameters contain duplicates")

            # Check for invalid characters
            param_pattern = re.compile(r"^[a-zA-Z0-9_]+$")
            for param in self._water_params:
                if not param_pattern.match(param):
                    errors.append(
                        f'Invalid parameter name "{param}": only letters, numbers, and underscores allowed'
                    )

        # Validate feature stations
        if not self._feature_stations:
            errors.append("Feature stations list cannot be empty")
        else:
            # Check for duplicates
            if len(self._feature_stations) != len(set(self._feature_stations)):
                errors.append("Feature stations contain duplicates")

            # Check for invalid characters
            station_pattern = re.compile(r"^[a-zA-Z0-9_]+$")
            for station in self._feature_stations:
                if not station_pattern.match(station):
                    errors.append(
                        f'Invalid station name "{station}": only letters, numbers, and underscores allowed'
                    )

        is_valid = len(errors) == 0
        return is_valid, errors

    def get_config_json(self) -> str:
        """
        Get configuration as JSON string for download.

        Returns:
            JSON string of configuration
        """
        config_data = {
            "version": CONFIG_VERSION,
            "water_params": self._water_params,
            "feature_stations": self._feature_stations,
        }
        return json.dumps(config_data, indent=2, ensure_ascii=False)

    def import_config_from_string(self, json_string: str) -> bool:
        """
        Import configuration from JSON string.

        Args:
            json_string: JSON string containing configuration

        Returns:
            True if imported successfully, False otherwise
        """
        try:
            config_data = json.loads(json_string)

            # Validate version
            version = config_data.get("version", 1)
            if version != CONFIG_VERSION:
                logger.warning(f"Config version mismatch: {version}")

            # Load parameters
            if "water_params" in config_data:
                self._water_params = config_data["water_params"]
            if "feature_stations" in config_data:
                self._feature_stations = config_data["feature_stations"]

            logger.info("Configuration imported from string")
            return True

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse config JSON: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to import config: {e}")
            return False

    def export_config(self, path: str) -> bool:
        """
        Export configuration to specified path.

        Args:
            path: Path to export configuration file

        Returns:
            True if exported successfully, False otherwise
        """
        try:
            export_path = Path(path)

            # Ensure directory exists
            export_path.parent.mkdir(parents=True, exist_ok=True)

            config_data = {
                "version": CONFIG_VERSION,
                "water_params": self._water_params,
                "feature_stations": self._feature_stations,
            }

            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Configuration exported to {export_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export config: {e}")
            return False

    def import_config(self, path: str) -> bool:
        """
        Import configuration from specified path.

        Args:
            path: Path to import configuration file from

        Returns:
            True if imported successfully, False otherwise
        """
        try:
            import_path = Path(path)

            if not import_path.exists():
                logger.error(f"Import file not found: {import_path}")
                return False

            with open(import_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)

            # Validate version
            version = config_data.get("version", 1)
            if version != CONFIG_VERSION:
                logger.warning(
                    f"Config version mismatch: expected {CONFIG_VERSION}, got {version}"
                )

            # Import water parameters
            imported_params = config_data.get("water_params", [])
            if not imported_params:
                logger.error("Imported config has no water parameters")
                return False

            # Import feature stations
            imported_stations = config_data.get("feature_stations", [])
            if not imported_stations:
                logger.error("Imported config has no feature stations")
                return False

            # Temporarily set values for validation
            old_params = self._water_params
            old_stations = self._feature_stations

            self._water_params = imported_params
            self._feature_stations = imported_stations

            # Validate imported config
            is_valid, errors = self.validate_config()
            if not is_valid:
                # Restore old values
                self._water_params = old_params
                self._feature_stations = old_stations
                logger.error(f"Imported config validation failed: {errors}")
                return False

            logger.info(f"Configuration imported from {import_path}")
            return True

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse import file: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to import config: {e}")
            return False

    # ==================== Multi-Config Management ====================

    def _get_saved_configs_dir(self) -> Path:
        """Get the directory for saved configurations."""
        if self._config_path:
            return self._config_path.parent / SAVED_CONFIGS_DIR
        return self._get_default_config_path().parent / SAVED_CONFIGS_DIR

    def list_saved_configs(self) -> list[dict[str, Any]]:
        """
        List all saved configurations.

        Returns:
            List of config info dicts with keys: name, path, created, water_params_count, feature_stations_count
        """
        configs = []
        saved_dir = self._get_saved_configs_dir()

        if not saved_dir.exists():
            return configs

        for config_file in saved_dir.glob("*.json"):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Get file stats
                stat = config_file.stat()
                created = datetime.fromtimestamp(stat.st_mtime)

                configs.append(
                    {
                        "name": config_file.stem,
                        "path": str(config_file),
                        "created": created.strftime("%Y-%m-%d %H:%M"),
                        "water_params_count": len(data.get("water_params", [])),
                        "feature_stations_count": len(data.get("feature_stations", [])),
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to read config {config_file}: {e}")
                continue

        # Sort by creation time (newest first)
        configs.sort(key=lambda x: x["created"], reverse=True)
        return configs

    def save_config_as(self, name: str) -> bool:
        """
        Save current configuration with a custom name.

        Args:
            name: Name for the saved configuration

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Sanitize name
            safe_name = re.sub(r'[<>:"/\\|?*]', "_", name.strip())
            if not safe_name:
                logger.error("Invalid config name")
                return False

            saved_dir = self._get_saved_configs_dir()
            saved_dir.mkdir(parents=True, exist_ok=True)

            config_path = saved_dir / f"{safe_name}.json"

            config_data = {
                "version": CONFIG_VERSION,
                "water_params": self._water_params,
                "feature_stations": self._feature_stations,
                "saved_at": datetime.now().isoformat(),
            }

            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Configuration saved as '{safe_name}'")
            return True

        except Exception as e:
            logger.error(f"Failed to save config as '{name}': {e}")
            return False

    def load_saved_config(self, name: str) -> bool:
        """
        Load a saved configuration by name.

        Args:
            name: Name of the saved configuration

        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            saved_dir = self._get_saved_configs_dir()
            config_path = saved_dir / f"{name}.json"

            if not config_path.exists():
                logger.error(f"Saved config '{name}' not found")
                return False

            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self._water_params = data.get("water_params", DEFAULT_WATER_PARAMS.copy())
            self._feature_stations = data.get(
                "feature_stations", DEFAULT_FEATURE_STATIONS.copy()
            )

            # Also save to current config
            self.save_config()

            logger.info(f"Loaded saved config '{name}'")
            return True

        except Exception as e:
            logger.error(f"Failed to load saved config '{name}': {e}")
            return False

    def delete_saved_config(self, name: str) -> bool:
        """
        Delete a saved configuration.

        Args:
            name: Name of the saved configuration to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            saved_dir = self._get_saved_configs_dir()
            config_path = saved_dir / f"{name}.json"

            if not config_path.exists():
                logger.error(f"Saved config '{name}' not found")
                return False

            config_path.unlink()
            logger.info(f"Deleted saved config '{name}'")
            return True

        except Exception as e:
            logger.error(f"Failed to delete saved config '{name}': {e}")
            return False

    def rename_saved_config(self, old_name: str, new_name: str) -> bool:
        """
        Rename a saved configuration.

        Args:
            old_name: Current name of the configuration
            new_name: New name for the configuration

        Returns:
            True if renamed successfully, False otherwise
        """
        try:
            saved_dir = self._get_saved_configs_dir()
            old_path = saved_dir / f"{old_name}.json"

            if not old_path.exists():
                logger.error(f"Saved config '{old_name}' not found")
                return False

            # Sanitize new name
            safe_name = re.sub(r'[<>:"/\\|?*]', "_", new_name.strip())
            if not safe_name:
                logger.error("Invalid new config name")
                return False

            new_path = saved_dir / f"{safe_name}.json"

            if new_path.exists():
                logger.error(f"Config '{safe_name}' already exists")
                return False

            old_path.rename(new_path)
            logger.info(f"Renamed config '{old_name}' to '{safe_name}'")
            return True

        except Exception as e:
            logger.error(f"Failed to rename config: {e}")
            return False
