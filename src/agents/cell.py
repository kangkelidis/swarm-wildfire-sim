from enum import Enum
from typing import TYPE_CHECKING, Tuple

import mesa

if TYPE_CHECKING:
    from src.simulation.simulation_model import SimulationModel


class FuelLevel(Enum):
    """Fuel levels for cell."""
    EMPTY = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class Cell(mesa.Agent):
    """Fixed location on the grid representing a portion of land.

    Holds information about vegetation, terrain, and fire status.
    """
    def __init__(self, model: 'SimulationModel', is_road: bool = False):
        """Cell.

        Args:
            model: The model containing the agent
        """
        self.model: 'SimulationModel'
        super().__init__(model)

        # Use a weighted random selection
        r = model.random.random()
        if r < 0.01:
            self.fuel_level = FuelLevel.EMPTY
        elif r < 0.3:
            self.fuel_level = FuelLevel.LOW
        elif r < 0.70:
            self.fuel_level = FuelLevel.MEDIUM
        else:
            self.fuel_level = FuelLevel.HIGH

        self.on_fire = False
        self.burnt = False
        self.burn_counter = 0
        self.is_road = is_road

    def step(self):
        """Step function for the cell agent.
        """
        self.model.fire_model.calculate_fire_spread(self)
