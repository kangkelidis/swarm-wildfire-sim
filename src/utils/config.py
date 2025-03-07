import os
from pathlib import Path
from typing import Any, Literal, Optional

import yaml
from pydantic import BaseModel, Field

from src.utils.logging_config import get_logger

# Get logger for this module
logger = get_logger()


# Custom exceptions
class ConfigError(Exception):
    """Base class for configuration errors"""
    pass


class ConfigFileNotFoundError(ConfigError):
    """Raised when a configuration file cannot be found"""
    pass


class ConfigParsingError(ConfigError):
    """Raised when there's an error parsing the configuration"""
    pass


# Pydantic configuration models
class SimulationConfig(BaseModel):
    """Simulation configuration parameters"""
    area_size: Literal['small', 'large'] = 'small'

    def model_post_init(self, __context: Any) -> None:
        self._width: int = 150 if self.area_size == 'small' else 200
        self._height: int = 150 if self.area_size == 'small' else 200

    max_steps: int = Field(default=100, gt=1)
    seed: int = 42
    save_data: bool = True
    save_location: str = "~/results"


class FireConfig(BaseModel):
    """Fire behaviour configuration"""
    initial_fires: int = Field(default=1, ge=0)
    model: Literal['simple', 'rothermel'] = 'simple'


class DroneConfig(BaseModel):
    """Configuration for individual drone agents"""
    battery_capacity: int = Field(gt=0, default=100)
    communication_range: float = Field(ge=0, default=10)
    vision_range: float = Field(ge=0, default=5)


class DroneBaseConfig(BaseModel):
    """Configuration for drone deployment bases"""
    number_of_agents: int = Field(gt=0, default=10)


class SwarmConfig(BaseModel):
    """Swarm configuration parameters"""
    initial_bases: int = Field(default=1, ge=0)
    drone_base: DroneBaseConfig = DroneBaseConfig()
    drone: DroneConfig = DroneConfig()


class CompleteConfig(BaseModel):
    """Complete configuration combining all sections and default values"""
    simulation: SimulationConfig = SimulationConfig()
    fire: FireConfig = FireConfig()
    swarm: SwarmConfig = SwarmConfig()

# TODO: use Singleton patter, dependency injection and perhaps context manager

class Config:
    """Configuration loader for simulation"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.

        Args:
            config_path: Optional path to configuration file.
                         If not provided, will search for default config.
        """
        # If no config path provided, look for default config
        if not config_path:
            config_path = self._find_default_config()

        self.config_path = config_path
        self.config = self._load_config()

    def _find_default_config(self) -> Optional[str]:
        """Look for default configuration file in standard locations"""
        default_locations = [
            Path("configs/default_config.yml"),  # Relative to cwd
            Path(__file__).parent.parent.parent / "configs" / "default_config.yml"  # Project root
        ]

        for location in default_locations:
            if location.exists():
                logger.info(f"Using default config at {location}")
                return str(location)

        logger.info("No default config file found")
        return None

    def _load_config(self) -> CompleteConfig:
        """Load and parse configuration from file or use defaults"""
        # Start with default config
        config = CompleteConfig()

        # If no config path was found, keep default config
        if not self.config_path:
            logger.info("No config file found, using default configuration")
            return config

        # Check if file exists
        if not os.path.exists(self.config_path):
            msg = f"Config file not found at {self.config_path}"
            logger.error(msg)
            raise ConfigFileNotFoundError(msg)

        try:
            # Load and parse YAML
            with open(self.config_path, 'r') as file:
                yaml_data = yaml.safe_load(file) or {}

            if not yaml_data:
                logger.warning("Empty configuration file, using default configuration")
                return config

            # Create new config with loaded values
            loaded_config = CompleteConfig(**yaml_data)
            logger.success(f"Configuration loaded successfully from {self.config_path}")
            return loaded_config

        except yaml.YAMLError as e:
            msg = f"YAML parsing error in configuration file: {str(e)}"
            logger.error(msg)
            raise ConfigParsingError(msg) from e
        except Exception as e:
            msg = f"Error loading configuration: {str(e)}"
            logger.error(msg)
            raise ConfigError(msg) from e

    def get(self, path: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.

        Args:
            path: Path to the configuration value (e.g., 'simulation.max_steps')
            default: Default value to return if the path doesn't exist

        Returns:
            The configuration value or the default
        """
        current = self.config
        for part in path.split('.'):
            if hasattr(current, part):
                current = getattr(current, part)
            else:
                return default
        return current
