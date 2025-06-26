"""
Drone knowledge module.

This module is responsible for storing the knowledge of a drone agent.
It simulates the drone's knowledge repository during the simulation.
"""

import warnings
from typing import TYPE_CHECKING, Any, NamedTuple, Optional

from matplotlib import pyplot as plt

from src.agents.drone_modules.communication import Message
from src.agents.drone_modules.navigation import chebyshev_distance

if TYPE_CHECKING:
    from src.agents.base import DroneBase
    from src.agents.drone import Drone


class ClosestNeighbour(NamedTuple):
    drone: Optional['Drone'] = None
    distance: Optional[int] = None


class DroneKnowledge:
    """
    Class to store the knowledge of a drone agent. Simulated the drone's knowledge repository.
    Knowledge is dynamic, the drone's knowledge changes. It should not have information relating to the simulation,
    these should be part of the drone class.

    """
    def __init__(self, drone: 'Drone'):
        self.drone = drone
        self.base_pos: tuple[int, int] = None

        self._closest_neighbour = ClosestNeighbour()
        self._closest_leader = ClosestNeighbour()

        # Communication-related knowledge
        self.mailbox: list[Message] = []  # Incoming messages
        self.reported_fires: set[tuple[int, int]] = set()  # Fire positions reported by other drones

    @property
    def links(self):
        return self._links

    @links.setter
    def links(self, value):
        self._links = value

    @property
    def closest_neighbour(self) -> Optional['Drone']:
        return self._closest_neighbour.drone

    def get_distance_to_closest_neighbour(self):
        return self._closest_neighbour.distance

    @closest_neighbour.setter
    def closest_neighbour(self, drone: Optional['Drone']):
        if drone is None:
            self._closest_neighbour = ClosestNeighbour()
            return

        distance = chebyshev_distance(self.drone.pos, drone.pos)
        self._closest_neighbour = ClosestNeighbour(drone, distance)
