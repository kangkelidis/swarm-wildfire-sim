from typing import TYPE_CHECKING

import mesa

from src.agents.cell import Cell

if TYPE_CHECKING:
    from src.simulation.simulation_model import SimulationModel


class HexEnvironment(mesa.space.HexMultiGrid):
    def __init__(self, model: 'SimulationModel', width: int, height: int):
        """ Environment class for wildfire simulation.

        Contains the grid and environmental conditions.
        """
        super().__init__(width=width, height=height, torus=False)
        self.model = model

        # create cells
        for x in range(width):
            for y in range(height):
                cell = Cell(model)
                self.place_agent(cell, (x, y))

    def get_neighbors(self, pos, moore: bool = True, radius: float = 1, include_center: bool = True):
        return super().get_neighbors(pos, radius, include_center)

    def get_neighborhood(self, pos, moore: bool = True, radius: float = 1, include_center: bool = True):
        return super().get_neighborhood(pos, radius, include_center)


class GridEnvironment(mesa.space.MultiGrid):
    def __init__(self, model: 'SimulationModel', width: int, height: int):
        """ Environment class for wildfire simulation.

        A 2D grid where each cell represents a portion of land that can be in un-burnt,
        burning or burnt and has specific vegetation and terrain properties.
        """
        super().__init__(width=width, height=height, torus=False)
        self.model = model

        # create cells
        for x in range(width):
            for y in range(height):
                if y < 5:
                    continue
                if (height // 2 - 1 < y < height // 2 + 1) or (width // 2 - 1 < x < width // 2 + 1):
                    cell = Cell(model, is_road=False)
                    self.place_agent(cell, (x, y))
                    continue
                cell = Cell(model)
                self.place_agent(cell, (x, y))


class SpaceEnvironment(mesa.space.ContinuousSpace):
    def __init__(self, model: 'SimulationModel', width: int, height: int):
        """ Environment class for wildfire simulation.

        """
        super().__init__(x_max=width, y_max=height, torus=False)
        self.model = model

        # create cells
        for x in range(width):
            for y in range(height):
                cell = Cell(model)
                self.place_agent(cell, (x, y))

    def get_neighbors(self, pos, moore: bool = True, radius: float = 1, include_center: bool = True):
        return super().get_neighbors(pos, radius, include_center)

    def get_neighborhood(pos, moore=True, include_center=False, radius=1):
        """Get a pos 1 away from the current position."""
        return [(pos[0] + dx, pos[1] + dy) for dx in range(-1, 2) for dy in range(-1, 2) if (dx != 0 or dy != 0)]
