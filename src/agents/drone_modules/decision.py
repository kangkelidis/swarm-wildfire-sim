"""
Decision module for drones. This module is responsible for making decisions based on the drone's state and utility calculations.
"""

from typing import TYPE_CHECKING

from src.utils.logging_config import get_logger

if TYPE_CHECKING:
    from src.agents.drone import Drone


class DecisionModule:
    def __init__(self, drone: 'Drone'):
        self.drone = drone
        self.utility_threshold = 0.5  # τ threshold for decision making

    def process(self) -> str:
        """
        Process the drone's decisions based on current state and utility calculations.
        """

        # Always check if battery needs recharging first
        if self.drone.battery.needs_recharging():
            return 'need_to_return'

        current_state = self.drone.state_machine.current_state.name

        if current_state == 'active':
            # Drone is active on grid - evaluate if should continue or return
            marginal_utility = self.estimate_marginal_utility()
            if marginal_utility < self.utility_threshold:
                return 'return_to_base'
            return 'continue_mission'

        elif current_state == 'inactive':
            # Drone is at base - evaluate deployment opportunities
            deployment_utility = self.evaluate_deployment_opportunity()
            if deployment_utility > self.utility_threshold:
                return 'deploy'
            return 'stay_at_base'

        elif current_state == 'returning_to_base':
            return 'continue_return'

        return 'no_action'

    def estimate_marginal_utility(self) -> float:
        """
        Estimate the marginal utility of continuing current mission.
        Returns a value between 0 and 1.
        """
        # Simple utility calculation based on:
        # - Remaining battery
        # - Distance to known fires
        # - Coverage area effectiveness

        battery_factor = self.drone.battery.get_charge_level() / 100.0

        # If there are known fires nearby, utility is higher
        fire_factor = 0.0
        if self.drone.knowledge.reported_fires:
            closest_fire_distance = min([
                abs(self.drone.pos[0] - fire_pos[0]) + abs(self.drone.pos[1] - fire_pos[1])
                for fire_pos in self.drone.knowledge.reported_fires
            ])
            # Higher utility for closer fires
            fire_factor = max(0, 1.0 - (closest_fire_distance / 20.0))

        # Combine factors
        utility = (battery_factor * 0.6) + (fire_factor * 0.4)
        return min(1.0, max(0.0, utility))

    def evaluate_deployment_opportunity(self) -> float:
        """
        Evaluate the utility of deploying from base.
        Returns a value between 0 and 1.
        """
        # Simple deployment utility based on:
        # - Battery level (should be high to deploy)
        # - Known fire locations requiring coverage
        # - Number of other active drones

        battery_factor = self.drone.battery.get_charge_level() / 100.0

        # Higher utility if fires are detected and need coverage
        fire_factor = 0.3  # Base exploration value
        if self.drone.knowledge.reported_fires:
            fire_factor = 0.8  # Higher if fires need attention

        # Consider how many other drones are already active
        # (This would require knowledge of other drones' states)
        activity_factor = 0.7  # Simplified - assume some deployment is usually beneficial

        utility = (battery_factor * 0.5) + (fire_factor * 0.3) + (activity_factor * 0.2)
        return min(1.0, max(0.0, utility))
