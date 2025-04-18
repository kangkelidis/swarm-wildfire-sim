from typing import TYPE_CHECKING, List

import mesa

from src.agents.drone import Drone
from src.utils.logging_config import get_logger

if TYPE_CHECKING:
    from src.simulation.simulation_model import SimulationModel

logger = get_logger()


class DroneBase(mesa.Agent):
    """Base station for drone deployment and recharging."""

    def __init__(self, model: 'SimulationModel', N):
        """Drone base.

        Args:
            model: The simulation model
            pos: Position of the base
        """
        super().__init__(model)
        self.drones: List[Drone] = []

        # Get configuration
        self.num_drones = N

    def deploy_drones(self):
        """Deploy drones from the base."""
        for i in range(self.num_drones):
            drone = Drone(self.model, self.pos)
            self.model.grid.place_agent(drone, self.pos)
            self.drones.append(drone)

    def step(self):
        """Base station step function."""
        pass
