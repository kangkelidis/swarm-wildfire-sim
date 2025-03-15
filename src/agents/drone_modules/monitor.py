"""
Monitor module for drones. This module is responsible for monitoring the environment and updating the drone's knowledge.
Updates the drone's knowledge about the environment. Monitors communications with other drones.
Simulates the drone's sensors.
"""

from typing import TYPE_CHECKING

from src.agents.drone_modules.communication import Message, MessageType
from src.agents.drone_modules.drone_enums import DroneRole
from src.agents.drone_modules.navigation import chebyshev_distance

if TYPE_CHECKING:
    from src.agents.drone import Drone


class SensorModule:
    def __init__(self, drone: 'Drone'):
        self.drone = drone

    def _update_drones_in_range_lists(self):
        """
        Updates the drones_in_range, same_cell_drones, and neighbours lists.

        Drones_in_range: All drones in communication range, including those in the same cell.
        Same_cell_drones: Drones in the same cell, excluding self.
        Neighbours: Drones in communication range, different cell, excluding self.
        """
        if not self.drone.pos:
            return []

        agents_in_range = self.drone.model.get_neighbors(
            pos=self.drone.pos, moore=True, include_center=True, radius=self.drone.communication_range
        )
        self.drone.drones_in_range = [
            agent for agent in agents_in_range if type(agent) is type(self.drone) and agent != self.drone]
        self.drone.same_cell_drones = [
            other_drone for other_drone in self.drone.drones_in_range if other_drone.pos == self.drone.pos
        ]
        self.drone.neighbours = [
            other for other in self.drone.drones_in_range if other.pos != self.drone.pos]

    def _get_closest_neighbour(self):
        if not self.drone.neighbours:
            self.drone.knowledge.closest_neighbour = None
            self.drone.knowledge.closest_leader = None
            return

        neighbours = self.drone.neighbours
        closest_neighbour: 'Drone' = min(neighbours, key=lambda n: chebyshev_distance(self.drone.pos, n.pos))

        # Will also update the closest leader if the closest neighbour is a leader
        if closest_neighbour.role == DroneRole.LEADER:
            self.drone.knowledge.closest_neighbour = closest_neighbour
            return

        # Update both closest neighbour and closest leader
        leaders = [n for n in neighbours if n.role == DroneRole.LEADER]

        if leaders:
            closest_leader: 'Drone' = min(leaders, key=lambda n: chebyshev_distance(self.drone.pos, n.pos))

        self.drone.knowledge.closest_neighbour = closest_neighbour
        self.drone.knowledge.closest_leader = closest_leader if leaders else None

    def _receive_messages(self):
        """Process all messages in the mailbox at start of turn."""
        # Get and clear mailbox
        messages = self.drone.knowledge.mailbox
        self.drone.knowledge.mailbox = []

        # Process messages
        for message in messages:
            self._process_message(message)

    def _process_message(self, message: Message):
        """Process an individual message and update drone knowledge."""
        if message.type == MessageType.FIRE_ALERT:
            # Update fire knowledge
            fire_pos = message.content
            self.drone.knowledge.reported_fires.add(fire_pos)

        elif message.type == MessageType.REGISTRATION:
            self.drone.knowledge.network.add(message.sender)
            message.sender.knowledge.network.add(self.drone)

    def gather_info(self):
        """Update all """

        # TODO: edge case, drone send message at last round and moves out of range.
        self._update_drones_in_range_lists()
        self._get_closest_neighbour()

        self._receive_messages()
