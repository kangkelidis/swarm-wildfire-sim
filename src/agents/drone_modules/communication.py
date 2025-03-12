from typing import TYPE_CHECKING

from src.agents.drone_modules.drone_roles import DroneRole

if TYPE_CHECKING:
    from src.agents.drone import Drone


class CommunicationModule:
    def __init__(self, drone: 'Drone'):
        self.drone = drone

    def broadcast(self, message):
        pass

    def receive(self):
        pass

    def register_follower(self, follower: 'Drone'):
        """
        Register a follower drone to this drone.
        """
        if self.drone.role != DroneRole.LEADER:
            self.drone.drone_logger.warning(f"Drone {self.drone.unique_id} is not a leader, cannot register follower.")
            return

        self.drone.knowledge.followers.append(follower)
        follower.knowledge.leader = self.drone

