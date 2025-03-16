import os
import tempfile
import unittest
from unittest.mock import patch

import yaml

from src.utils.config_loader import (ConfigError, ConfigFileNotFoundError,
                                     ConfigLoader, ConfigParsingError)


class TestConfig(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def test_find_default_config(self):
        """Test the method that finds the default config"""
        with patch('pathlib.Path.exists') as mock_exists:
            # First test when default exists
            mock_exists.return_value = True
            config = ConfigLoader()
            self.assertIsNotNone(config._find_default_config())

            # Then test when no default exists
            mock_exists.return_value = False
            config = ConfigLoader()
            self.assertIsNone(config._find_default_config())

    def test_nonexistent_file_raises_error(self):
        """Test that specifying a non-existent file raises an error"""
        # Try to load from a file that doesn't exist
        with self.assertRaises(ConfigFileNotFoundError):
            ConfigLoader("/path/to/nonexistent/file.yml")

    def test_config_loading(self):
        """Test loading configuration from YAML file"""
        # Create a temporary config file
        config_data = {
            "simulation": {
                "area_size": "large",
                "max_steps": 200,
                "seed": 123
            },
            "fire": {
                "initial_fires": 2,
                "model": "rothermel"
            },
            "swarm": {
                "initial_bases": 3,
                "drone_base": {
                    "number_of_agents": 15,
                },
                "drone": {
                    "battery_capacity": 150,
                    "communication_range": 15,
                    "vision_range": 8
                }
            },
        }

        yaml_path = os.path.join(self.temp_dir, "test_config.yml")
        with open(yaml_path, "w") as f:
            yaml.dump(config_data, f)

        # Load the config
        config = ConfigLoader(yaml_path)

        # Check if values are loaded correctly
        self.assertEqual(config.config.simulation.area_size, 'large')
        self.assertEqual(config.config.simulation.max_steps, 200)
        self.assertEqual(config.config.simulation.seed, 123)

        self.assertEqual(config.config.fire.initial_fires, 2)
        self.assertEqual(config.config.fire.model, 'rothermel')

        self.assertEqual(config.config.swarm.initial_bases, 3)
        self.assertEqual(config.config.swarm.drone_base.number_of_agents, 15)

        # Check drone configuration
        self.assertEqual(config.config.swarm.drone.battery_capacity, 150)
        self.assertEqual(config.config.swarm.drone.communication_range, 15)
        self.assertEqual(config.config.swarm.drone.vision_range, 8)

    def test_partial_config(self):
        """Test loading a config file with only some sections defined"""
        # Create a config with just the fire section
        config_data = {
            "fire": {
                "initial_fires": 5,
                "model": "rothermel"
            }
        }

        yaml_path = os.path.join(self.temp_dir, "partial_config.yml")
        with open(yaml_path, "w") as f:
            yaml.dump(config_data, f)

        # Load the config
        config = ConfigLoader(yaml_path)

        # Check that fire section was updated but others use defaults
        self.assertEqual(config.config.fire.initial_fires, 5)
        self.assertEqual(config.config.fire.model, 'rothermel')
        self.assertEqual(config.config.simulation.area_size, 'small')  # Default value
        self.assertEqual(config.config.swarm.initial_bases, 1)  # Default value

    def test_invalid_string_values(self):
        """Test handling of invalid string values in the config"""
        config_data = {
            "simulation": {
                "area_size": "invalid",
            },
        }

        yaml_path = os.path.join(self.temp_dir, "invalid_strings.yml")
        with open(yaml_path, "w") as f:
            yaml.dump(config_data, f)

        with self.assertRaises(ConfigError):
            ConfigLoader(yaml_path)

    def test_invalid_yaml(self):
        """Test handling of invalid YAML syntax"""
        # Create a file with invalid YAML
        yaml_path = os.path.join(self.temp_dir, "invalid.yml")
        with open(yaml_path, "w") as f:
            f.write("simulation: {area_size: 'small', max_steps: invalid")

        # Check that proper exception is raised
        with self.assertRaises(ConfigParsingError):
            ConfigLoader(yaml_path)

    def test_empty_yaml(self):
        """Test loading an empty YAML file"""
        # Create an empty file
        yaml_path = os.path.join(self.temp_dir, "empty.yml")
        with open(yaml_path, "w") as _:
            pass  # Empty file

        # Load the config
        config = ConfigLoader(yaml_path)

        # Should use default values
        self.assertEqual(config.config.simulation.area_size, 'small')
        self.assertEqual(config.config.fire.model, 'simple')

    def test_general_exception_handling(self):
        """Test that general exceptions are properly caught and wrapped"""
        # Create a valid file first to avoid file not found error
        yaml_path = os.path.join(self.temp_dir, "test_config.yml")
        with open(yaml_path, "w") as f:
            f.write("simulation: {area_size: 'small'}")

        # Mock open to raise an exception
        with patch('builtins.open', side_effect=Exception("Test exception")):
            # Check that proper exception is raised
            with self.assertRaises(ConfigError):
                ConfigLoader(yaml_path)

    def test_drone_configuration(self):
        """Test the drone configuration settings"""
        config_data = {
            "swarm": {
                "drone": {
                    "battery_capacity": 250,
                    "communication_range": 20,
                    "vision_range": 12
                }
            }
        }

        yaml_path = os.path.join(self.temp_dir, "drone_config.yml")
        with open(yaml_path, "w") as f:
            yaml.dump(config_data, f)

        # Load the config
        config = ConfigLoader(yaml_path)

        # Check the drone settings
        self.assertEqual(config.config.swarm.drone.battery_capacity, 250)
        self.assertEqual(config.config.swarm.drone.communication_range, 20)
        self.assertEqual(config.config.swarm.drone.vision_range, 12)

    def test_numeric_value_validation(self):
        """Test validation of numeric values in configuration"""
        # Test negative max_steps (should be > 1)
        config_data = {
            "simulation": {
                "max_steps": 0  # Invalid, should be > 1
            }
        }

        yaml_path = os.path.join(self.temp_dir, "numeric_validation.yml")
        with open(yaml_path, "w") as f:
            yaml.dump(config_data, f)

        with self.assertRaises(ConfigError):
            ConfigLoader(yaml_path)

        # Test invalid type
        config_data = {
            "simulation": {
                "max_steps": "not a number"  # Invalid type
            }
        }

        with open(yaml_path, "w") as f:
            yaml.dump(config_data, f)

        with self.assertRaises(ConfigError):
            ConfigLoader(yaml_path)

        # Test negative drone battery capacity
        config_data = {
            "swarm": {
                "drone": {
                    "battery_capacity": -50  # Invalid, should be > 0
                }
            }
        }

        with open(yaml_path, "w") as f:
            yaml.dump(config_data, f)

        with self.assertRaises(ConfigError):
            ConfigLoader(yaml_path)

    def test_config_accessor_methods(self):
        """Test the API methods for accessing configuration values"""
        config_loader = ConfigLoader()
        config = config_loader.config

        # Test attribute access style
        self.assertEqual(config.simulation.area_size, 'small')

        # Test the get method
        self.assertEqual(config.get('simulation.area_size'), 'small')
        self.assertEqual(config.get('fire.model'), 'simple')

        # Test getting default for non-existent path
        self.assertEqual(config.get('non.existent.path', 'default_value'), 'default_value')

    def test_yaml_structure_with_comments(self):
        """Test loading a YAML file that contains comments"""
        # Create a config with comments
        yaml_content = """
        # Simulation settings
        simulation:
          area_size: large  # Size of the simulation area
          max_steps: 500    # Maximum simulation steps

        # Fire model configuration
        fire:
          initial_fires: 3
          model: rothermel
        """

        yaml_path = os.path.join(self.temp_dir, "commented_config.yml")
        with open(yaml_path, "w") as f:
            f.write(yaml_content)

        # Load the config
        config = ConfigLoader(yaml_path)

        # Verify settings were properly loaded
        self.assertEqual(config.config.simulation.area_size, 'large')
        self.assertEqual(config.config.simulation.max_steps, 500)
        self.assertEqual(config.config.fire.initial_fires, 3)
        self.assertEqual(config.config.fire.model, 'rothermel')

    def test_unknown_field_rejection(self):
        """Test that unknown fields in the config are ignored"""
        config_data = {
            "simulation": {
                "unknown_field": "value"  # Field that doesn't exist in model
            }
        }

        yaml_path = os.path.join(self.temp_dir, "unknown_field.yml")
        with open(yaml_path, "w") as f:
            yaml.dump(config_data, f)

        c = ConfigLoader(yaml_path)
        self.assertNotIn("unknown_field", vars(c.config.simulation))


if __name__ == "__main__":
    unittest.main()
