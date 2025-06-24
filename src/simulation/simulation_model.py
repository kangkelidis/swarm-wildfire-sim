from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import mesa
import mesa.agent
import networkx as nx

from src.agents import Cell, Drone, DroneBase
from src.agents.drone_modules.drone_enums import DroneColors, DroneRole
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

        self.num_of_agents = self.config.swarm.drone_base.number_of_agents
        self.num_of_bases = self.config.swarm.initial_bases

        # Initialize cost tracking
        self.total_cost = 0.0
        self.drone_deployments = 0
        self.charging_events = 0

        self.cells = self.agents_by_type.get(Cell)
        self.burning_cells = self.agents.select(filter_func=lambda x: x.on_fire, agent_type=Cell)
        self.drones = None
        self.bases = None

        # update from solara model parameters
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

        # Initialise bases
        for _ in range(self.num_of_bases):
            self.add_base()

        # Set debug flag for a random drone
        if self.drones:
            drone = self.random.choice(self.drones)
            drone.debug = False
            self.drones.do("set_up")

    def register_drone_deployment(self, count: int = 1):
        """
        Register the deployment of drones and calculate the associated cost.

        Args:
            count: Number of drones being deployed
        """
        self.drone_deployments += count
        deployment_cost = count * self.config.simulation.deployment_cost
        self.total_cost += deployment_cost
        logger.debug(f"Deployed {count} drones, added cost: {deployment_cost}")

    def register_charging_event(self):
        """
        Register a drone charging event and calculate the associated cost.
        """
        self.charging_events += 1
        charge_cost = self.config.simulation.charge_cost
        self.total_cost += charge_cost
        logger.debug(f"Drone charging event, added cost: {charge_cost}")

    def get_cost_details(self):
        """
        Get a detailed breakdown of all costs.

        Returns:
            dict: Dictionary with cost details
        """
        deployment_cost = self.drone_deployments * self.config.simulation.deployment_cost
        charging_cost = self.charging_events * self.config.simulation.charge_cost

        return {
            'drone_deployments': self.drone_deployments,
            'charging_events': self.charging_events,
            'deployment_cost': deployment_cost,
            'charging_cost': charging_cost,
            'total_cost': self.total_cost
        }

    def step(self):
        """
        Execute one step of the simulation.
        """
        if self.burning_cells:
            self.burning_cells.shuffle_do("step")

        if self.drones:
            self.drones.shuffle_do("step")

    def run(self):
        """
        Run the simulation for a specified number of steps or until completion.
        Does not get called by Solara.
        """
        self.running = True
        max_steps = self.config.simulation.max_steps
        for _ in range(max_steps):
            self.step()
            if not self.running:
                break

    def get_neighbors(self, pos: tuple[int, int], moore: bool = True,
                      include_center: bool = False, radius: int = 1, type: mesa.Agent = None):
        """
        Get neighbors of a cell.

        :param pos: Position of the cell
        :param moore: Include diagonal neighbours
        :param include_center: Include the center cell
        :param radius: Radius of the neighbourhood
        :param type: Type of agent to filter

        :returns: List of neighbouring cells
        """
        agents = self.grid.get_neighbors(pos, moore, include_center, radius)
        if type:
            agents = [agent for agent in agents if isinstance(agent, type)]
        return agents

    def start_fire(self, position: tuple[int, int] = None):
        """
        Start fires in the simulation.

        Args:
            position: Optional (x,y) tuple to start fire at specific location
        """
        if position:
            # Get cell at specific position
            cell_contents = self.grid.get_cell_list_contents([position])
            cells = [agent for agent in cell_contents if isinstance(agent, Cell)]
            if cells:
                cells[0].on_fire = True
                self.burning_cells.add(cells[0])
        else:
            # Start a random fire
            while True:
                random_cell: Cell = self.random.choice(self.cells)
                if not random_cell.on_fire:
                    random_cell.on_fire = True
                    self.burning_cells.add(random_cell)
                    break

    def add_base(self):
        """
        Add a new base to the simulation.
        """
        x = self.random.randint(2, self.grid.width - 2)
        y = self.random.choice([2, self.grid.height // 2, self.grid.height - 3])
        base = DroneBase(self, self.num_of_agents, self.config)
        self.grid.place_agent(base, (x, y))
        base.deploy_drones()
        # Register drone deployment cost
        self.register_drone_deployment(self.num_of_agents)

        if self.bases:
            self.bases.add(base)
        else:
            self.bases: mesa.agent.AgentSet = self.agents_by_type.get(DroneBase)
            self.drones: mesa.agent.AgentSet = self.agents_by_type.get(Drone)

    def display_topology(self):
        """Generate network topology visualization"""
        if not self.drones:
            return None

        # Create a figure
        fig, ax = plt.subplots(figsize=(8, 8))

        topology = nx.Graph()

        for drone in self.drones:
            graph = drone.knowledge.network.graph
            topology.add_nodes_from(graph.nodes(data=True))
            topology.add_edges_from(graph.edges(data=True))

        # Create position layout for nodes
        # pos = nx.circular_layout(topology)
        pos = {node: (node.pos[0], node.pos[1]) for node in topology.nodes()}

        # Draw nodes with different colors based on role
        leaders = [n for n in topology.nodes() if n.role == DroneRole.LEADER]
        nx.draw_networkx_nodes(topology, pos,
                               nodelist=leaders,
                               node_color=DroneColors.LEADER.value,
                               node_size=90)

        followers = [n for n in topology.nodes() if n.role == DroneRole.SCOUT]
        nx.draw_networkx_nodes(topology, pos,
                               nodelist=followers,
                               node_color=DroneColors.SCOUT.value,
                               node_size=50)

        # Draw edges
        follower_edges = [(u, v) for (u, v, d) in topology.edges(data=True)
                          if d['relation'] == 'peer']
        nx.draw_networkx_edges(topology, pos,
                               edgelist=follower_edges,
                               width=0.5,
                               edge_color='grey',
                               style='dotted')

        leader_edges = [(u, v) for (u, v, d) in topology.edges(data=True)
                        if d['relation'] == 'leader' or d['relation'] == 'follower']
        nx.draw_networkx_edges(topology, pos,
                               edgelist=leader_edges,
                               width=0.5,
                               edge_color='black')

        # Add labels
        # labels = {node: f"D{node.unique_id}" for node in topology.nodes()}
        labels = {node: "" for node in topology.nodes()}
        plt.tight_layout()
        nx.draw_networkx_labels(topology, pos, labels)

        return fig
