"""Unit tests for ConfigurationManager."""

import json
import tempfile
from pathlib import Path

import pytest

from src.model_finetune_ui.utils.config_manager import (
    ConfigurationManager,
    DEFAULT_WATER_PARAMS,
    DEFAULT_FEATURE_STATIONS,
)


class TestConfigurationManager:
    """ConfigurationManager unit tests."""

    def test_init_with_defaults(self, temp_dir):
        """Test initialization loads default values."""
        config_path = temp_dir / "test_config.json"
        manager = ConfigurationManager(config_path=str(config_path))

        assert manager.get_water_params() == DEFAULT_WATER_PARAMS
        assert manager.get_feature_stations() == DEFAULT_FEATURE_STATIONS

    def test_set_and_get_water_params(self, temp_dir):
        """Test setting and getting water parameters."""
        config_path = temp_dir / "test_config.json"
        manager = ConfigurationManager(config_path=str(config_path))

        new_params = ["param1", "param2", "param3"]
        manager.set_water_params(new_params)

        assert manager.get_water_params() == new_params

    def test_set_and_get_feature_stations(self, temp_dir):
        """Test setting and getting feature stations."""
        config_path = temp_dir / "test_config.json"
        manager = ConfigurationManager(config_path=str(config_path))

        new_stations = ["station1", "station2"]
        manager.set_feature_stations(new_stations)

        assert manager.get_feature_stations() == new_stations

    def test_add_water_param(self, temp_dir):
        """Test adding a new water parameter."""
        config_path = temp_dir / "test_config.json"
        manager = ConfigurationManager(config_path=str(config_path))

        # Get current params and add new one
        current = manager.get_water_params()
        new_param = "new_param"
        current.append(new_param)
        manager.set_water_params(current)

        # Verify
        updated = manager.get_water_params()
        assert new_param in updated
        assert len(updated) == len(DEFAULT_WATER_PARAMS) + 1

    def test_add_feature_station(self, temp_dir):
        """Test adding a new feature station."""
        config_path = temp_dir / "test_config.json"
        manager = ConfigurationManager(config_path=str(config_path))

        # Get current stations and add new one
        current = manager.get_feature_stations()
        new_station = "STZ99"
        current.append(new_station)
        manager.set_feature_stations(current)

        # Verify
        updated = manager.get_feature_stations()
        assert new_station in updated
        assert len(updated) == len(DEFAULT_FEATURE_STATIONS) + 1

    def test_remove_water_param(self, temp_dir):
        """Test removing a water parameter."""
        config_path = temp_dir / "test_config.json"
        manager = ConfigurationManager(config_path=str(config_path))

        # Get current params and remove one
        current = manager.get_water_params()
        to_remove = current[0]
        current.remove(to_remove)
        manager.set_water_params(current)

        # Verify
        updated = manager.get_water_params()
        assert to_remove not in updated
        assert len(updated) == len(DEFAULT_WATER_PARAMS) - 1

    def test_remove_feature_station(self, temp_dir):
        """Test removing a feature station."""
        config_path = temp_dir / "test_config.json"
        manager = ConfigurationManager(config_path=str(config_path))

        # Get current stations and remove one
        current = manager.get_feature_stations()
        to_remove = current[0]
        current.remove(to_remove)
        manager.set_feature_stations(current)

        # Verify
        updated = manager.get_feature_stations()
        assert to_remove not in updated
        assert len(updated) == len(DEFAULT_FEATURE_STATIONS) - 1

    def test_reorder_water_params(self, temp_dir):
        """Test reordering water parameters."""
        config_path = temp_dir / "test_config.json"
        manager = ConfigurationManager(config_path=str(config_path))

        # Reverse the order
        current = manager.get_water_params()
        reversed_params = list(reversed(current))
        manager.set_water_params(reversed_params)

        # Verify
        updated = manager.get_water_params()
        assert updated == reversed_params
        assert updated[0] == current[-1]

    def test_save_and_load_config(self, temp_dir):
        """Test saving and loading configuration."""
        config_path = temp_dir / "test_config.json"
        manager = ConfigurationManager(config_path=str(config_path))

        # Modify and save
        new_params = ["a", "b", "c"]
        new_stations = ["x", "y", "z"]
        manager.set_water_params(new_params)
        manager.set_feature_stations(new_stations)
        assert manager.save_config() is True

        # Create new instance and verify loaded
        manager2 = ConfigurationManager(config_path=str(config_path))
        assert manager2.get_water_params() == new_params
        assert manager2.get_feature_stations() == new_stations

    def test_get_config_json(self, temp_dir):
        """Test exporting config as JSON string."""
        config_path = temp_dir / "test_config.json"
        manager = ConfigurationManager(config_path=str(config_path))

        json_str = manager.get_config_json()
        data = json.loads(json_str)

        assert "water_params" in data
        assert "feature_stations" in data
        assert data["water_params"] == DEFAULT_WATER_PARAMS

    def test_import_config_from_string(self, temp_dir):
        """Test importing config from JSON string."""
        config_path = temp_dir / "test_config.json"
        manager = ConfigurationManager(config_path=str(config_path))

        import_data = {
            "version": 1,
            "water_params": ["imported1", "imported2"],
            "feature_stations": ["imp_station1"],
        }
        json_str = json.dumps(import_data)

        assert manager.import_config_from_string(json_str) is True
        assert manager.get_water_params() == ["imported1", "imported2"]
        assert manager.get_feature_stations() == ["imp_station1"]

    def test_get_returns_copy(self, temp_dir):
        """Test that get methods return copies, not references."""
        config_path = temp_dir / "test_config.json"
        manager = ConfigurationManager(config_path=str(config_path))

        # Modify returned list
        params = manager.get_water_params()
        params.append("should_not_affect_original")

        # Original should be unchanged
        assert "should_not_affect_original" not in manager.get_water_params()
