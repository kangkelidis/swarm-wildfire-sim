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

        self.cells = self.agents_by_type.get(Cell)
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
            drone.debug = True
            self.drones.do("set_up")

    def step(self):
        """
        Execute one step of the simulation.
        """

        if self.steps % 10 == 0:
            self.topology()

        if self.cells:
            self.cells.shuffle_do("step")

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
        else:
            # Start random fires
            available_cells = [agent for agent in self.cells if not agent.on_fire]
            if available_cells:
                cells_to_ignite = self.random.sample(available_cells, min(num_fires, len(available_cells)))
                for cell in cells_to_ignite:
                    cell.on_fire = True

    def add_base(self):
        """
        Add a new base to the simulation.
        """
        x = self.random.randint(2, self.grid.width - 2)
        y = self.random.choice([2, self.grid.height // 2, self.grid.height - 3])
        base = DroneBase(self, self.num_of_agents, self.config)
        self.grid.place_agent(base, (x, y))
        base.deploy_drones()

        if self.bases:
            self.bases.add(base)
        else:
            self.bases: mesa.agent.AgentSet = self.agents_by_type.get(DroneBase)
            self.drones: mesa.agent.AgentSet = self.agents_by_type.get(Drone)

    # TODO: REMOVE
    def topology(self):
        """

        """
        if not self.drones:
            return

        topology = nx.Graph()

        for drone in self.drones:
            drone: Drone
            graph = drone.knowledge.network.graph
            topology.add_nodes_from(graph.nodes(data=True))
            topology.add_edges_from(graph.edges(data=True))

        # Create position layout for nodes
        # TODO: check different layouts
        pos = nx.spring_layout(topology)

        # Draw nodes with different colors based on role
        # Leader drones
        leaders = [n for n in topology.nodes() if n.role == DroneRole.LEADER]
        nx.draw_networkx_nodes(topology, pos,
                            nodelist=leaders,
                            node_color=DroneColors.LEADER.value,
                            node_size=300)

        # Follower drones
        followers = [n for n in topology.nodes() if n.role == DroneRole.SCOUT]
        nx.draw_networkx_nodes(topology, pos,
                            nodelist=followers,
                            node_color=DroneColors.SCOUT.value,
                            node_size=300)

        # Draw edges with different styles based on relationship
        # # Leader connections (solid bold)
        leader_edges = [(u, v) for (u, v, d) in topology.edges(data=True)
                        if d['relation'] == 'leader' or d['relation'] == 'follower']
        nx.draw_networkx_edges(topology, pos,
                            edgelist=leader_edges,
                            width=2.0,
                            edge_color='black')


        # Follower connections (dotted)
        follower_edges = [(u, v) for (u, v, d) in topology.edges(data=True)
                          if d['relation'] == 'peer']
        nx.draw_networkx_edges(topology, pos,
                            edgelist=follower_edges,
                            width=0.5,
                            edge_color='grey',
                            style='dotted')

        # Add labels
        labels = {node: f"D{node.unique_id}" for node in topology.nodes()}
        plt.title(f"Drone Network")
        nx.draw_networkx_labels(topology, pos, labels)
        plt.savefig('topology.png')
        plt.close()

        logger.success("Topology Drawn")

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
                               node_size=100)

        followers = [n for n in topology.nodes() if n.role == DroneRole.SCOUT]
        nx.draw_networkx_nodes(topology, pos,
                               nodelist=followers,
                               node_color=DroneColors.SCOUT.value,
                               node_size=70)

        # Draw edges
        leader_edges = [(u, v) for (u, v, d) in topology.edges(data=True)
                        if d['relation'] == 'leader' or d['relation'] == 'follower']
        nx.draw_networkx_edges(topology, pos,
                               edgelist=leader_edges,
                               width=1.0,
                               edge_color='grey')

        follower_edges = [(u, v) for (u, v, d) in topology.edges(data=True)
                          if d['relation'] == 'peer']
        nx.draw_networkx_edges(topology, pos,
                               edgelist=follower_edges,
                               width=0.5,
                               edge_color='grey',
                               style='dotted')

        # Add labels
        # labels = {node: f"D{node.unique_id}" for node in topology.nodes()}
        labels = {node: "" for node in topology.nodes()}
        plt.title(f"Drone Network")
        nx.draw_networkx_labels(topology, pos, labels)

        return fig
