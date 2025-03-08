from dataclasses import dataclass
from typing import TYPE_CHECKING

import mesa

from src.utils.logging_config import DroneLogger, get_logger

if TYPE_CHECKING:
    from src.simulation.simulation_model import SimulationModel


logger = get_logger()


class NeighbouringLeaders:
    """
    Class to hold neighbouring leader drones in each direction

    Attributes:
        right: Drone
        left: Drone
        top: Drone
        bottom: Drone

    """
    def __init__(self):
        self.right: Drone = None
        self.left: Drone = None
        self.top: Drone = None
        self.bottom: Drone = None

    def drop_link(self, direction: str) -> None:
        """
        Drop a link in the given direction.

        :param direction: The direction to drop the link in
        :raises ValueError: If an invalid direction is given
        """
        if direction == 'left':
            self.left.neighbouring_leaders.right = None
            self.left = None
        elif direction == 'right':
            self.right.neighbouring_leaders.left = None
            self.right = None
        elif direction == 'top':
            self.top.neighbouring_leaders.bottom = None
            self.top = None
        elif direction == 'bottom':
            self.bottom.neighbouring_leaders.top = None
            self.bottom = None
        else:
            raise ValueError(f"Invalid direction: {direction}")

    def __iter__(self):
        return iter([self.right, self.left, self.top, self.bottom])

    def __len__(self):
        return sum(1 for _ in self)

    def __contains__(self, item):
        return item in [self.right, self.left, self.top, self.bottom]

    def __repr__(self):
        return (f"NeighbouringLeaders(right={self.right}, left={self.left}, "
                f"top={self.top}, bottom={self.bottom})")


class Drone(mesa.Agent):
    """
    Drone agent class.

    Attributes:
        communication_range: int
        desired_distance: int
        neighbours: list[Drone]
        neighbouring_leaders: NeighbouringLeaders
        debug: bool
        logger
    """
    def __init__(self, model: 'SimulationModel', base_pos: tuple[int, int]):
        """
        Initialise the drone agent.

        Args:
            model: The simulation model
        """
        super().__init__(model)
        self.model: 'SimulationModel'
        self.base_pos = base_pos
        self.communication_range = 20
        self.desired_distance = 18
        self.target_pos: tuple[int, int] = None

        # initialise neighbours
        self.neighbours = self.get_drones_in_range()
        self.neighbouring_leaders = NeighbouringLeaders()
        self.same_cell_drones = []

        self.debug = False
        self.drone_logger = DroneLogger(logger)

        self.counter = 0

        self.free = True
        self.weak_link = None
        self.stationary = False
        self.in_crystal = False

    def set_up(self) -> None:
        """
        Post-init setup for the drone agent. To be called after the agent has been added to the
        model and has a position.
        Finds the leaders closest to desired_distance in each direction and forms links with them.
        """
        # update neighbours
        self.neighbours = self.get_drones_in_range()
        self.target_pos = (self.pos[0], self.pos[1])

        if self.debug:
            self.drone_logger.on = True

    def step(self) -> None:
        """
        """
        # monitor
        self.neighbours = self.get_drones_in_range()

        if self.free:
            self.disperse()
            self.random_walk()

        if not self.stationary:
            self.formation()
            self.move_towards(self.target_pos)

    def get_drones_in_range(self) -> list['Drone']:
        """
        Get all drones in communication range. Excludes self.
        Updates the same_cell_drones attribute with drones in the same cell as this drone.

        :return: A list of drones in communication range
        """
        if not self.pos:
            return []
        neighbours = self.model.grid.get_neighbors(
            pos=self.pos, moore=True, include_center=True, radius=self.communication_range
        )
        drones = [drone for drone in neighbours if isinstance(drone, Drone) and drone != self]
        self.same_cell_drones = [drone for drone in drones if drone.pos == self.pos]
        return drones

    def update_linked_leaders(self, at_empty: bool = False) -> None:
        """
        Update the linked leaders for this drone.
        """
        # find the leader in the empty directions
        if at_empty:
            empty_links = []
            for direction in ['left', 'right', 'top', 'bottom']:
                if not getattr(self.neighbouring_leaders, direction):
                    empty_links.append(direction)

            if not empty_links:
                return

            for direction in empty_links:
                leader = self._find_leader_in_direction(direction)
                if leader:
                    self.form_link(leader, direction)
        else:
            # find the closest leader in each direction
            for direction in ['left', 'right', 'top', 'bottom']:
                leader = self._find_leader_in_direction(direction)
                if leader:
                    self.form_link(leader, direction)

    def _find_leader_in_direction(self, direction: str) -> 'Drone':
        """
        Find the leader closest to the desired distance in the given direction.
        Does not take into account the second axis. For example, when looking for the left leader,
        only how close the desired distance is in the x-axis is considered.

        :param direction: The direction to look for a leader in
        :return: The leader drone, or None if no leader is found
        """
        if not self.neighbours:
            return None

        candidates = [n for n in self.neighbours if self._is_valid_candidate(n, direction)]
        if not candidates:
            return None

        return min(candidates, key=lambda n: abs(self.get_dx(n) - self.desired_distance))

    def _is_valid_candidate(self, candidate: 'Drone', direction: str) -> bool:
        """
        Check if a drone is a valid candidate for a leader in the given direction.

        A valid candidate is one that is in the correct direction, does not already have a leader in
        the opposite direction, and is not already linked to this drone.

        :param candidate: The drone to check
        :param direction: The direction to check
        :return: True if the candidate is valid, False otherwise
        :raises ValueError: If an invalid direction is given
        """
        if direction == 'left':
            return (candidate.pos[0] <= self.pos[0] and
                    not candidate.neighbouring_leaders.right and
                    not self.has_link(candidate))
        elif direction == 'right':
            return (candidate.pos[0] >= self.pos[0] and
                    not candidate.neighbouring_leaders.left and
                    not self.has_link(candidate))
        elif direction == 'top':
            return (candidate.pos[1] >= self.pos[1] and
                    not candidate.neighbouring_leaders.bottom and
                    not self.has_link(candidate))
        elif direction == 'bottom':
            return (candidate.pos[1] <= self.pos[1] and
                    not candidate.neighbouring_leaders.top and
                    not self.has_link(candidate))
        else:
            raise ValueError(f"Invalid direction: {direction}")

    def get_dx(self, other: 'Drone') -> int:
        """
        Get the distance in the x-axis between this drone and another drone.
        """
        return int(abs(other.pos[0] - self.pos[0]))

    def get_dy(self, other: 'Drone') -> int:
        """
        Get the distance in the y-axis between this drone and another drone.
        """
        return int(abs(other.pos[1] - self.pos[1]))

    def form_link(self, other: 'Drone', direction: str) -> None:
        """
        Form a link with another drone.

        :param other: The other drone to link to
        :param direction: The direction to link in
        :raises ValueError: If an invalid direction is given
        """
        if not self.in_crystal:
            self.in_crystal = self.get_random_hex_color()
        self.stationary = True
        if direction == 'left':
            self.neighbouring_leaders.left = other
            other.neighbouring_leaders.right = self
        elif direction == 'right':
            self.neighbouring_leaders.right = other
            other.neighbouring_leaders.left = self
        elif direction == 'top':
            self.neighbouring_leaders.top = other
            other.neighbouring_leaders.bottom = self
        elif direction == 'bottom':
            self.neighbouring_leaders.bottom = other
            other.neighbouring_leaders.top = self
        else:
            raise ValueError(f"Invalid direction: {direction}")

    def has_link(self, other: 'Drone') -> bool:
        """
        Check if this drone has a link with another drone.

        :param other: The other drone to check
        :return: True if the drones are linked, False otherwise
        """
        return other in self.neighbouring_leaders and self in other.neighbouring_leaders

    def is_out_of_bounds(self, target: tuple[int, int]) -> bool:
        """
        Check if the target position is out of bounds of the grid.

        Args:
            target: The target position to check
        Returns:
            True if the target is out of bounds, False otherwise
        """
        return self.model.grid.out_of_bounds(target)

    def change_target(self, target: tuple[int, int]) -> None:
        """
        Change the target position of the drone.
        If it is out of bounds the target is clamp to the grid edge.

        Args:
            target: The new target position
        """
        # move away from base
        target = (target[0], max(5, target[1]))

        if self.is_out_of_bounds(target):
            x, y = target
            x = max(0, min(x, self.model.grid.width - 1))
            # move away from base
            y = max(0, min(y, self.model.grid.height - 1))
            self.target_pos = (x, y)
        else:
            self.target_pos = target

    def move_towards(self, target: tuple[int, int]) -> None:
        """
        Move the drone towards the target position. In each step, the drone moves one unit closer to
        the target in each axis.

        Must be in a 2D grid.

        Args:
            target: The target position to move towards
        """
        x, y = self.pos
        dx, dy = target
        if x < dx:
            x += 1
        elif x > dx:
            x -= 1
        if y < dy:
            y += 1
        elif y > dy:
            y -= 1

        self.drone_logger.debug(f"Moving towards {target}, at {x, y}")
        self.model.grid.move_agent(self, (x, y))

    def get_random_direction(self, including_center: bool) -> tuple[int, int]:
        """
        Get a random neighbouring cell in the grid.
        """
        cells = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=including_center)
        return self.random.choice(cells)

    def random_walk(self):
        """
        Move the drone to a random neighbouring cell or stay.
        """
        new_target = self.get_random_direction(including_center=True)
        self.change_target(new_target)

    def disperse(self):
        """
        If there are more than two drones in the same cell, move one of them to a random neighbouring
        cell.
        """
        if len(self.same_cell_drones) > 0:
            new_target = self.get_random_direction(including_center=False)
            self.change_target(new_target)

    def can_form_weak_link(self, other: 'Drone') -> bool:
        """
        Check if this drone can form a 'weak link' with another drone.

        A weak link is formed if the drones chebyshev distance is close to the desired distance,
        and the drones are not already linked.
        """
        e = 2
        return (abs(self.chebyshev_distance(other.pos) - self.desired_distance) < e and
                not self.weak_link and not other.weak_link)

    def form_weak_link(self, other: 'Drone') -> None:
        """
        Form a 'weak link' with another drone.

        The other drone is made stationary until the two drones are linked. This drone moves to
        create a strong link.
        """
        self.free = False
        other.free = False
        self.weak_link = other
        other.weak_link = self
        other.stationary = True

    def formation(self):
        """
        Handle formation behavior for drones with weak links to transform them into strong links.
        """
        # move to create a strong link
        if self.weak_link:
            # find which direction the weak link is in by checking the dx and dy
            dx = self.get_dx(self.weak_link)
            dy = self.get_dy(self.weak_link)

            # left or right, because we need less steps to align in x
            if dx > dy:
                # if I am to the left of the weak link, move to align with it
                if self.pos[0] < self.weak_link.pos[0]:
                    # Calculate target position - desired distance to left of weak link
                    target_x = self.weak_link.pos[0] - self.desired_distance
                    # Match y-coordinate to align vertically
                    target_y = self.weak_link.pos[1]
                    self.change_target((target_x, target_y))

                    # Check if in position to form a strong link
                    if self.pos[0] == target_x and self.pos[1] == target_y:
                        self.form_link(self.weak_link, 'right')
                        self.free = True
                        self.weak_link.free = True
                        self.weak_link.stationary = False
                        self.weak_link = None
                else:
                    # Calculate target position - desired distance to right of weak link
                    target_x = self.weak_link.pos[0] + self.desired_distance
                    # Match y-coordinate to align vertically
                    target_y = self.weak_link.pos[1]
                    self.change_target((target_x, target_y))

                    # Check if in position to form a strong link
                    if self.pos[0] == target_x and self.pos[1] == target_y:
                        self.form_link(self.weak_link, 'left')
                        self.free = True
                        self.weak_link.free = True
                        self.weak_link.stationary = False
                        self.weak_link = None
            # top or bottom
            else:
                # if I am below the weak link
                if self.pos[1] < self.weak_link.pos[1]:
                    # Calculate target position - desired distance below weak link
                    target_y = self.weak_link.pos[1] - self.desired_distance
                    # Match x-coordinate to align horizontally
                    target_x = self.weak_link.pos[0]
                    self.change_target((target_x, target_y))

                    # Check if in position to form a strong link
                    if self.pos[0] == target_x and self.pos[1] == target_y:
                        self.form_link(self.weak_link, 'top')
                        self.free = True
                        self.weak_link.free = True
                        self.weak_link.stationary = False
                        self.weak_link = None
                # if I am above the weak link
                else:
                    # Calculate target position - desired distance above weak link
                    target_y = self.weak_link.pos[1] + self.desired_distance
                    # Match x-coordinate to align horizontally
                    target_x = self.weak_link.pos[0]
                    self.change_target((target_x, target_y))

                    # Check if in position to form a strong link
                    if self.pos[0] == target_x and self.pos[1] == target_y:
                        self.form_link(self.weak_link, 'bottom')
                        self.free = True
                        self.weak_link.free = True
                        self.weak_link.stationary = False
                        self.weak_link = None

            return

        if not self.in_crystal:
            # check all neighbours to see if close to forming a weak link
            for neighbour in self.neighbours:
                if self.can_form_weak_link(neighbour):
                    self.form_weak_link(neighbour)


    def chebyshev_distance(self, target: tuple[int, int]) -> int:
        """
        Calculate the Chebyshev distance between the drone and a target position.

        Known as chessboard distance, the minimum number of moves a king must take to reach the target.
        The distance between two points is the greatest of their differences along any coordinate dimension.

        Args:
            target: The target position
        Returns:
            The Chebyshev distance
        """
        return max(abs(self.pos[0] - target[0]), abs(self.pos[1] - target[1]))

    def __repr__(self):
        return f"Drone {self.unique_id}, at {self.pos}"

    def get_random_hex_color(self):
        """
        Get a random hex color string.
        """
        color = "%06x" % self.random.randint(0, 0xFFFFFF)
        return "#" + color
