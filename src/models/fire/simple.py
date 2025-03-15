from typing import TYPE_CHECKING

import numpy as np

from src.agents.cell import Cell, FuelLevel
from src.utils.logging_config import get_logger

if TYPE_CHECKING:
    from src.simulation.simulation_model import SimulationModel

logger = get_logger()


class SimpleFireModel:
    """Simple fire spread model."""

    def __init__(self, model: 'SimulationModel'):
        self.model = model

        # Get grid dimensions
        self.width = model.config.simulation._width
        self.height = model.config.simulation._height

        # Base probabilities for fire spread based on fuel level
        # 678
        self.base_probabilities = {
            FuelLevel.EMPTY: 1,
            FuelLevel.LOW: 0.45,
            FuelLevel.MEDIUM: 0.55,
            FuelLevel.HIGH: 0.65,
        }

        # Burn time depends on fuel level
        self.burn_times = {
            FuelLevel.EMPTY: 0,
            FuelLevel.LOW: 1,
            FuelLevel.MEDIUM: 3,
            FuelLevel.HIGH: 4,
        }

    def calculate_fire_spread(self, cell: Cell):
        """Calculate fire spread for a cell.

        Args:
            cell: The cell to evaluate
        """

        if not cell.on_fire:
            return

        cell.burn_counter += 1
        if cell.burn_counter >= self.burn_times[cell.fuel_level]:
            cell.on_fire = False
            cell.burnt = True
            return

        neighbours = self.model.grid.get_neighbors(pos=cell.pos, moore=True, radius=1)
        neighbours: list[Cell] = [n for n in neighbours if isinstance(n, Cell) and not n.burnt and not n.on_fire]
        for neighbour in neighbours:
            if self.model.random.random() < self.base_probabilities[neighbour.fuel_level]:
                neighbour.on_fire = True
