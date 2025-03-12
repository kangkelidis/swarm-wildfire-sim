from typing import TYPE_CHECKING

from src.agents.drone_modules.drone_roles import DroneRole

if TYPE_CHECKING:
    from src.agents.drone import Drone


# TODO: do we need this, decisions are made in the state machine
class DecisionModule:
    def __init__(self, drone: 'Drone'):
        self.drone = drone

    def process(self) -> str:
        """
        Process the drone's role and update the drone's state.
        """

        if self.drone.state_machine.current_state.name == 'Recharging':
            return 'recharge'
        if self.drone.battery.needs_recharging():
            return 'need_to_return'

        if self.drone.role == DroneRole.LEADER:
            return self._leader_analysis()
        elif self.drone.role == DroneRole.SCOUT:
            return self._scout_analysis()
        elif self.drone.role == DroneRole.CORDON:
            return self._cordon_analysis()
        elif self.drone.role == DroneRole.WALKER:
            return self._walker_analysis()

    def _leader_analysis(self):
        """
        Analysis for leader drones.
        """
        return 'deploy'

    def _scout_analysis(self):
        """
        Analysis for scout drones.
        """
        return 'deploy'

    def _cordon_analysis(self):
        """
        Analysis for cordon drones.
        """
        pass

    def _walker_analysis(self):
        """
        Analysis for walker drones.
        """
        pass

    def elect_leader(self):
        """
        Best leader is one with most battery, and most connections and least leaders in neighbourhood.
        """
        pass
