from enum import Enum
from typing import TYPE_CHECKING, Tuple

import mesa

if TYPE_CHECKING:
    from src.simulation.simulation_model import SimulationModel


class FuelLevel(Enum):
    """Fuel levels for cell."""
    LOW = 0
    MEDIUM = 1
    HIGH = 2


class Cell(mesa.Agent):
    """Fixed location on the grid representing a portion of land.

    Holds information about vegetation, terrain, and fire status.
    """
    def __init__(self, model: 'SimulationModel'):
        """Cell.

        Args:
            model: The model containing the agent
        """
        self.model: 'SimulationModel'
        super().__init__(model)

        self.fuel_level = model.random.choice(list(FuelLevel))
        self.on_fire = False
        self.burnt = False
        self.burn_counter = 0

    def step(self):
        """Step function for the cell agent.
        """
        self.model.fire_model.calculate_fire_spread(self)
