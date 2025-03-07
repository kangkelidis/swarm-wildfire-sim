from typing import TYPE_CHECKING

import mesa
import mesa.agent

from src.agents.base import DroneBase
from src.agents.cell import Cell
from src.agents.drone import Drone
from src.models.environment.environment import (GridEnvironment,
                                                HexEnvironment,
                                                SpaceEnvironment)
from src.models.fire.simple import SimpleFireModel
from src.utils.config import Config
from src.utils.logging_config import get_logger

if TYPE_CHECKING:
    pass
# Get logger for this module
logger = get_logger()


class SimulationModel(mesa.Model):
    """
    Main simulation model for swarm monitoring wildfire.

    This model integrates environmental conditions, fire spread mechanics,
    and a swarm of autonomous drones for monitoring the wildfire.
    """
    def __init__(self, config: Config = None, **kwargs):
        """
        Initialise the wildfire simulation model using a config object.

        Args:
            config (Config, optional): Configuration object containing simulation parameters.
                If None, default configuration will be loaded.
        """
        # Load configuration, in case it was not provided
        self.config = config or Config()

        super().__init__(seed=self.config.get("simulation.seed", None))
        # Initialise fire spread model
        self.fire_model = SimpleFireModel(self)

        # Initialise environment (must be called space or grid to work with solara)
        self.grid = GridEnvironment(model=self,
                                    width=self.config.get("simulation._width", 100),
                                    height=self.config.get("simulation._height", 100))

        # # set a random cell on fire
        # cells: list['Cell'] = self.random.choices(self.grid.agents, k=1)
        # for cell in cells:
        #     cell.on_fire = True

        self.N = int(kwargs.get("N", self.config.get("swarm.drone_base.number_of_agents", 1)))
        # Initialise bases
        for _ in range(self.config.get("swarm.initial_bases", 1)):
            base = DroneBase(self, self.N)
            self.grid.place_agent(base, (100, 2))
            base.deploy_drones()

        base = DroneBase(self, self.N)
        self.grid.place_agent(base, (100, 102))
        base.deploy_drones()

        self._init_agentsets()

        # Set debug flag for a random drone
        drone = self.random.choice(self.drones)
        drone.debug = True
        self.drones.do("set_up")

    def _init_agentsets(self):
        self.cells: mesa.agent.AgentSet = self.agents_by_type.get(Cell, [])
        self.drones: mesa.agent.AgentSet = self.agents_by_type.get(Drone, [])
        self.bases: mesa.agent.AgentSet = self.agents_by_type.get(DroneBase, [])

    def step(self):
        """
        Execute one step of the simulation.
        """
        # self.cells.shuffle_do("step")

        self.drones.shuffle_do("step")
        # self.agents.shuffle_do("step")

    def run(self):
        """
        Run the simulation for a specified number of steps or until completion.
        """
        self.running = True
        max_steps = self.config.get("simulation.max_steps", float("inf"))
        for _ in range(max_steps):
            self.step()
            if not self.running:
                break
