"""
Decision module for drones. This module is responsible for making decisions based on the drone's role and state.

Responsible for the network formation.
"""

from typing import TYPE_CHECKING

from src.agents.drone_modules.drone_enums import DroneRole
from src.agents.drone_modules.navigation import chebyshev_distance
from src.utils.logging_config import get_logger

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

        self.update_network()

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

    def update_network(self):
        """
        Update the network based on the drone's role.
        """
        if self.drone.role == DroneRole.LEADER:
            self._leader_network()
        elif self.drone.role == DroneRole.SCOUT:
            self._scout_network()
        elif self.drone.role == DroneRole.CORDON:
            self._cordon_network()
        elif self.drone.role == DroneRole.WALKER:
            self._walker_network()

    def _leader_network(self):
        """
        Update the network for leader drones.

        Rules:
        1. Connect with other leaders only if both are in formation
        2. Connect with followers up to max capacity (1/LEADERS_RATIO)
        3. Only connect with followers that aren't already connected to other leaders
        """
        # Calculate available follower slots
        max_followers = int(1 // self.drone.LEADERS_RATIO)
        available_slots = max_followers - len(self.drone.knowledge.network.followers)

        connections = []
        # Find available leaderless followers
        if available_slots > 0:
            leaderless_followers = [drone for drone in self.drone.neighbours
                                    if drone.role != DroneRole.LEADER and
                                    drone.knowledge.network.leader is None][:available_slots]
            connections.extend(leaderless_followers)

        # Connect with other leaders if both in formation
        if self.drone.navigation.is_in_formation():
            leader_peers = [drone for drone in self.drone.neighbours
                            if drone.role == DroneRole.LEADER and
                            drone.navigation.is_in_formation()]
            connections.extend(leader_peers)

        if connections:
            self.drone.communication.send_registration(connections)

    def _scout_network(self):
        """
        Update the network for scout drones.

        Connect with a subset of the drones that share the same leader.
        """
        MAX_PEERS = 5
        # If the scout has no leader, connect with the closest leader
        if self.drone.knowledge.network.leader is None:
            if self.drone.knowledge.closest_leader:
                self.drone.communication.send_registration([self.drone.knowledge.closest_leader])
                return
            return

        peers = [drone for drone in self.drone.knowledge.network.leader.knowledge.network.followers
                 if drone != self.drone]

        # get the MAX_PEERS closest peers
        peers = sorted(peers, key=lambda d: chebyshev_distance(self.drone.pos, d.pos))
        peers = peers[:MAX_PEERS]
        if peers:
            self.drone.communication.send_registration(peers)

    def _cordon_network(self):
        """
        Update the network for cordon drones.
        """
        pass

    def _walker_network(self):
        """
        Update the network for walker drones.
        """
        pass

    def elect_leader(self):
        """
        Best leader is one with most battery, and most connections and least leaders in neighbourhood.
        """
        pass
