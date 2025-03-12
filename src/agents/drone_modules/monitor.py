from typing import TYPE_CHECKING

from src.agents.drone_modules.drone_roles import DroneRole

if TYPE_CHECKING:
    from src.agents.drone import Drone


class SensorModule:
    def __init__(self, drone: 'Drone'):
        self.drone = drone

    def _get_drones_in_range(self) -> list['Drone']:
        """
        Get all drones in communication range. Excludes self.
        Updates the same_cell_drones attribute with drones in the same cell as this drone.

        :returns: A list of drones in communication range
        """
        if not self.drone.pos:
            return []
        neighbours = self.drone.model.get_neighbors(
            pos=self.drone.pos, moore=True, include_center=True, radius=self.drone.communication_range
        )
        drones = [other for other in neighbours if type(other) is type(self.drone) and other != self.drone]
        self.drone.knowledge.same_cell_drones = [other_drone for other_drone in drones if other_drone.pos == self.drone.pos]
        self.drone.knowledge.neighbours = drones
        self.drone.knowledge.diff_cell_neighbours = [other for other in drones if other.pos != self.drone.pos]

    def _get_closest_neighbour(self):
        # Find the closest neighbor
        if not self.drone.knowledge.diff_cell_neighbours:
            return
        leaders = [n for n in self.drone.knowledge.diff_cell_neighbours if n.role == DroneRole.LEADER]
        if not leaders:
            return
        closest_neighbour = min(leaders, key=lambda n: self.drone.navigation.chebyshev_distance(n.pos))
        current_distance = self.drone.navigation.chebyshev_distance(closest_neighbour.pos)
        self.drone.knowledge.closest_neighbour = closest_neighbour
        self.drone.knowledge.distance_to_closest_neighbour = current_distance

    def gather(self):
        """Update all """
        if self.drone.role == DroneRole.LEADER:
            self._get_drones_in_range()
            self._get_closest_neighbour()
