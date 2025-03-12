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
from src.utils.config_loader import Config, ConfigLoader
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
    def __init__(self, config_loader: ConfigLoader = None, **kwargs):
        """
        Initialise the wildfire simulation model using a config object.

        Args:
            config (Config, optional): Configuration object containing simulation parameters.
                If None, default configuration will be loaded.
        """
        # Load configuration, in case it was not provided
        config_loader = config_loader or ConfigLoader()
        self.config: 'Config' = config_loader.config

        super().__init__(seed=self.config.get("simulation.seed", None))
        # Initialise fire spread model
        self.fire_model = SimpleFireModel(self)

        # Initialise environment (must be called space or grid to work with solara)
        self.grid = GridEnvironment(model=self,
                                    width=self.config.simulation._width,
                                    height=self.config.simulation._height)

        self.number_of_agents = self.config.swarm.drone_base.number_of_agents
        self.num_of_bases = self.config.swarm.initial_bases

        # Initialise bases
        for _ in range(self.num_of_bases):
            x = self.random.randint(2, self.grid.width - 2)
            y = self.random.choice([2, self.grid.height // 2, self.grid.height - 3])
            base = DroneBase(self, self.number_of_agents, self.config)
            self.grid.place_agent(base, (x, y))
            base.deploy_drones()

        self._init_agentsets()

        # Set debug flag for a random drone
        if self.drones:
            drone = self.random.choice(self.drones)
            drone.debug = True
            self.drones.do("set_up")

    def _init_agentsets(self):
        self.cells: mesa.agent.AgentSet = self.agents_by_type.get(Cell, None)
        self.drones: mesa.agent.AgentSet = self.agents_by_type.get(Drone, None)
        self.bases: mesa.agent.AgentSet = self.agents_by_type.get(DroneBase, None)

    def step(self):
        """
        Execute one step of the simulation.
        """
        self.cells.shuffle_do("step")

        if self.drones:
            self.drones.shuffle_do("step")
        # self.agents.shuffle_do("step")

    def run(self):
        """
        Run the simulation for a specified number of steps or until completion.
        """
        self.running = True
        max_steps = self.config.simulation.max_steps
        for _ in range(max_steps):
            self.step()
            if not self.running:
                break

    def get_neighbors(self, pos, moore=True, include_center=False, radius=1):
        """
        Get neighbors of a cell.

        :param pos: Position of the cell
        :param moore: Include diagonal neighbours
        :param include_center: Include the center cell
        :param radius: Radius of the neighbourhood

        :returns: List of neighbouring cells
        """
        return self.grid.get_neighbors(pos, moore, include_center, radius)

    def start_fire(self, num_fires=1, position=None):
        """
        Start fires in the simulation.

        Args:
            num_fires: Number of random fires to start
            position: Optional (x,y) tuple to start fire at specific location
        """
        if position:
            # Get cell at specific position
            cell_contents = self.grid.get_cell_list_contents([position])
            cells = [agent for agent in cell_contents if isinstance(agent, Cell)]
            if cells:
                cells[0].on_fire = True
                logger.info(f"Started fire at position {position}")
        else:
            # Start random fires
            available_cells = [agent for agent in self.cells if not agent.on_fire]
            if available_cells:
                cells_to_ignite = self.random.sample(available_cells, min(num_fires, len(available_cells)))
                for cell in cells_to_ignite:
                    cell.on_fire = True
                    logger.info(f"Started fire at position {cell.pos}")

    def add_base(self):
        """
        Add a new base to the simulation.
        """
        x = self.random.randint(2, self.grid.width - 2)
        y = self.random.randint(2, self.grid.height - 2)
        base = DroneBase(self, self.number_of_agents, self.config)
        self.grid.place_agent(base, (x, y))
        base.deploy_drones()

        # case where simulation started without bases
        if self.bases is None:
            self.bases: mesa.agent.AgentSet = self.agents_by_type.get(DroneBase, None)
            self.drones: mesa.agent.AgentSet = self.agents_by_type.get(Drone, None)

        self.bases.add(base)
        logger.info(f"Added base at position {base.pos}")
