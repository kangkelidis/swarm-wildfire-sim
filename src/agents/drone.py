"""
Drone agent class.
"""

from enum import StrEnum
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
    def __init__(self, model: 'SimulationModel', base_pos: tuple[int, int], config: 'Config'):
        """
        Initialise the drone agent.

        :param model: The simulation model
        :param base_pos: The position of the base station the drone is deployed from
        """
        super().__init__(model)
        self.model: 'SimulationModel'
        self.communication_range = int(config.swarm.drone.communication_range)
        self.desired_distance = int(self.communication_range * 0.9)

        self.debug = False
        self.drone_logger = DroneLogger(logger)

        self.role = self.random.choice([DroneRole.LEADER, DroneRole.SCOUT])

        # Create knowledge repository
        self.knowledge = DroneKnowledge()
        self.knowledge.base_pos = base_pos

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

    def step(self) -> None:
        """
        """
        # Monitor
        self.monitor.gather()
        # Analyse / Plan
        plan = self.decision.process()
        # Execute
        if not plan:
            return
        self.state_machine.send(plan)

    def leader_score(self) -> float:
        """
        Best leader is one with most battery, and most connections and least leaders in neighbourhood.
        """
        leaders = [drone for drone in self.knowledge.neighbours if drone.role == DroneRole.LEADER]
        return self.battery.battery_level + len(self.knowledge.neighbours) - leaders * 2

    def is_at_base(self) -> bool:
        """
        Check if the drone is at the base station.
        """
        return self.knowledge.base_pos == self.pos

    def __repr__(self):
        return f"Drone {self.unique_id}, at {self.pos}"
