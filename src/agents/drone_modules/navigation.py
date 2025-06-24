from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.agents.drone import Drone


class NavigationModule:
    def __init__(self, drone: 'Drone'):
        self.drone = drone
        self.target_pos: tuple[int, int] = None

    def return_to_base(self):
        pass

    def get_dx(self, other: 'Drone') -> int:
        """
        Get the absolute distance in the x-axis between this drone and another drone.
        """
        return int(abs(other.pos[0] - self.drone.pos[0]))

    def get_dy(self, other: 'Drone') -> int:
        """
        Get the absolute distance in the y-axis between this drone and another drone.
        """
        return int(abs(other.pos[1] - self.drone.pos[1]))

    def change_target(self, target: tuple[int, int]) -> None:
        """
        Change the target position of the drone.
        If it is out of bounds the target move towards the center of the grid.

        Args:
            target: The new target position
        """
        # move away from base and edges
        x, y = target
        if x <= 5:
            x += 2
        if x >= self.drone.model.grid.width - 5:
            x -= 2
        if y <= 5:
            y += 2
        if y >= self.drone.model.grid.height - 5:
            y -= 2
        self.target_pos = (x, y)

    def move_towards(self, target: tuple[int, int]) -> None:
        """
        Move the drone towards the target position. In each step, the drone moves one unit closer to
        the target in each axis.

        Must be in a 2D grid.

        Args:
            target: The target position to move towards
        """
        x, y = self.drone.pos
        dx, dy = target
        if x < dx:
            x += 1
        elif x > dx:
            x -= 1
        if y < dy:
            y += 1
        elif y > dy:
            y -= 1

        new_pos = (x, y)

        # Update battery level based on distance moved
        distance = chebyshev_distance(self.drone.pos, target)
        self.drone.battery.update(distance)

        self.drone.model.grid.move_agent(self.drone, new_pos)

    def get_random_direction(self, including_center: bool) -> tuple[int, int]:
        """
        Get a random neighbouring cell in the grid.
        """
        cells = self.drone.model.grid.get_neighborhood(self.drone.pos, moore=True, include_center=including_center)
        return self.drone.random.choice(cells)

    def random_walk(self):
        """
        Move the drone to a random neighbouring cell or stay.
        """
        new_target = self.get_random_direction(including_center=True)
        self.change_target(new_target)
        self.move_towards(self.target_pos)

    def disperse(self):
        """
        If there are more than two drones in the same cell, move one of them to a random neighbouring
        cell.
        """
        new_target = self.get_random_direction(including_center=False)
        self.change_target(new_target)
        self.move_towards(self.target_pos)

    def formation(self):
        """
        Handle formation behaviour for drones.
        Find the closest neighbour, check the chebyshev distance and if it less than the desired
        distance, move away to increase the distance by one, reduce by one otherwise.
        """
        if not self.drone.neighbours:
            self.random_walk()
            return

        closest_neighbour = self.drone.knowledge.closest_leader
        if not closest_neighbour:
            self.random_walk()
            return

        current_distance = self.drone.knowledge.get_distance_to_closest_leader()

        # Calculate direction (move away if too close, move closer if too far)
        x, y = self.drone.pos
        neighbor_x, neighbor_y = closest_neighbour.pos

        if current_distance < self.drone.desired_distance:
            # increase chebyshev distance by one
            if x < neighbor_x:
                x -= 1
            elif x > neighbor_x:
                x += 1
            if y < neighbor_y:
                y -= 1
            elif y > neighbor_y:
                y += 1
            self.change_target((x, y))
        elif current_distance > self.drone.desired_distance:
            # decrease chebyshev distance by one
            if x < neighbor_x:
                x += 1
            elif x > neighbor_x:
                x -= 1
            if y < neighbor_y:
                y += 1
            elif y > neighbor_y:
                y -= 1
            self.change_target((x, y))

        self.move_towards(self.target_pos)

    def is_in_formation(self):
        """
        Check if the drone is in formation with the closest leader.

        If there is not closest leader, the drone is in formation.
        """
        distance = self.drone.knowledge.get_distance_to_closest_leader()
        return distance == self.drone.desired_distance or distance is None


def chebyshev_distance(pos_a: tuple[int, int], pos_b: tuple[int, int]) -> int:
    """
    Calculate the Chebyshev distance between two points.

    Known as chessboard distance, the minimum number of moves a king must take to reach the target.
    The distance between two points is the greatest of their differences along any coordinate dimension.

    :param a: The first point
    :param b: The second point
    :return: The Chebyshev distance
    """
    return max(abs(pos_a[0] - pos_b[0]), abs(pos_a[1] - pos_b[1]))
