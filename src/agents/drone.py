"""
Drone agent class.

Holds information about the drone agent, include information about the simulation.
Drones' simulated attributes are stored in the DroneKnowledge class.
"""

from typing import TYPE_CHECKING

import mesa

from src.agents.drone_modules import (BatteryModule, CommunicationModule,
                                      DecisionModule, DroneBehaviour,
                                      DroneKnowledge, DroneRole,
                                      NavigationModule, SensorModule)
from src.utils.logging_config import DroneLogger, get_logger

if TYPE_CHECKING:
    from src.simulation.simulation_model import SimulationModel
    from src.utils.config_loader import Config


logger = get_logger()


class Drone(mesa.Agent):
    """
    Drone agent class.

    Attributes:

    """
    DESIRED_DISTANCE_MULTIPLIER = 0.9
    LEADERS_RATIO = 0.1

    def __init__(self, model: 'SimulationModel', base_pos: tuple[int, int], config: 'Config'):
        """
        Initialise the drone agent.

        :param model: The simulation model
        :param base_pos: The position of the base station the drone is deployed from
        """
        super().__init__(model)
        self.model: 'SimulationModel'
        self.communication_range = int(config.swarm.drone.communication_range)
        # The distance leader drones should maintain between each other
        self.desired_distance = int(self.communication_range * Drone.DESIRED_DISTANCE_MULTIPLIER)

        self.debug = False
        # Logger that logs debug messages only for drones with debug set to True
        self.drone_logger = DroneLogger(logger)

        self.role = self._init_role()

        # Create knowledge repository, simulating the drone's knowledge of the environment
        self.knowledge = DroneKnowledge(self)
        self.knowledge.base_pos = base_pos
        self.drones_in_range: list['Drone'] = []  # Excluding self, including those in the same cell
        self.same_cell_drones: list['Drone'] = []  # Excluding self
        self.neighbours: list['Drone'] = []  # Drones in communication range, different cell, excluding self

        self.state_machine = DroneBehaviour(model=self)

        # Initialize MAPE-K components
        self.monitor = SensorModule(self)
        self.decision = DecisionModule(self)
        self.battery = BatteryModule(self, config)
        self.communication = CommunicationModule(self)
        self.navigation = NavigationModule(self)

    def set_up(self) -> None:
        """
        Post-init setup for the drone agent. To be called after the agent has been added to the
        model and has a position.
        """
        if self.debug:
            self.drone_logger.on = True
            self.state_machine.print_state_diagram()
            self.role = DroneRole.LEADER

    def step(self) -> None:
        """
        """
        # Monitor
        self.monitor.gather_info()
        # Analyse / Plan
        plan = self.decision.process()
        # Execute
        if not plan:
            return
        self.state_machine.send(plan)

        if self.model.steps % 10 == 0 and self.debug:
            self.knowledge.network.draw()

    def leader_score(self) -> float:
        """
        Best leader is one with most battery, and most connections and least leaders in neighbourhood.
        """
        leaders = [drone for drone in self.knowledge.neighbours if drone.role == DroneRole.LEADER]
        return self.battery.battery_level + len(self.knowledge.neighbours) - leaders * 2

    def _init_role(self) -> DroneRole:
        """
        Initialise the role of the drone at the start of the simulation.
        Choose between leader and scout at random in respect to
        the ratio of leaders desired in the swarm.
        """
        # Returns a single element list, so we get the first element
        return self.random.choices([DroneRole.LEADER, DroneRole.SCOUT],
                                   weights=[Drone.LEADERS_RATIO, 1 - Drone.LEADERS_RATIO])[0]

    def __repr__(self):
        return f"Drone {self.unique_id}, at {self.pos}, role: {self.role}, battery: {self.battery.battery_level}"

    def __str__(self):
        return f"D-{self.unique_id}"
