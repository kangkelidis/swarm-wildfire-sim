from typing import TYPE_CHECKING, List

import mesa

from src.agents.drone import Drone
from src.utils.logging_config import get_logger

if TYPE_CHECKING:
    from src.simulation.simulation_model import SimulationModel

logger = get_logger()


class DroneBase(mesa.Agent):
    """Base station for drone deployment and recharging."""

    def __init__(self, model: 'SimulationModel', pos):
        """Drone base.

        Args:
            model: The simulation model
            pos: Position of the base
        """
        super().__init__(model)
        self.pos = pos
        self.drones: List[Drone] = []

        # Get configuration
        self.num_drones = self.model.config.config.swarm.drone_base.number_of_agents

        # Deploy drones
        self._deploy_drones()

    def _deploy_drones(self):
        """Deploy drones from the base."""
        for i in range(self.num_drones):
            drone = Drone(self.model, self.pos, self.pos)
            self.model.grid.place_agent(drone, self.pos)
            self.drones.append(drone)

            # Move drone to a random position around the base to avoid overlap
            drone.random_move()

    def step(self):
        """Base station step function."""
        pass
