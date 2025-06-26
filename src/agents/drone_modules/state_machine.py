from typing import TYPE_CHECKING

from statemachine import Event, State, StateMachine
from statemachine.contrib.diagram import DotGraphMachine

if TYPE_CHECKING:
    from src.agents.drone import Drone


class DroneBehaviour(StateMachine):
    inactive = State('Inactive', initial=True)
    active = State('Active')
    returning_to_base = State('Returning_to_base')

    # Events
    deploy = inactive.to(active)
    return_to_base = active.to(returning_to_base)
    arrived_at_base = returning_to_base.to(inactive)

    def is_at_base(self):
        drone: 'Drone' = self.model
        return drone.knowledge.base_pos == drone.pos

    def on_enter_inactive(self):
        drone: 'Drone' = self.model
        # Drone is at base, can recharge if needed
        if hasattr(drone, 'battery'):
            drone.battery.recharge()

    def on_enter_active(self):
        drone: 'Drone' = self.model
        # Drone is deployed on the grid, start patrolling
        if hasattr(drone, 'navigation'):
            drone.navigation.random_walk()

    def on_enter_returning_to_base(self):
        drone: 'Drone' = self.model
        # Drone is returning to base
        if hasattr(drone, 'navigation'):
            drone.navigation.move_towards(drone.knowledge.base_pos)

    def on_transition(self, event):
        drone: 'Drone' = self.model
        if hasattr(drone, 'drone_logger'):
            drone.drone_logger.debug(f"Drone is transitioning to {self.current_state}, triggered by {event}")

    def print_state_diagram(self):
        graph = DotGraphMachine(self)
        dot = graph()
        dot.write_png("out/drone_state_machine.png")
