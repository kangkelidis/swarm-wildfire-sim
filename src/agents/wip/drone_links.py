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

        self.update_linked_leaders()

        self.drone_logger.debug(f"{self.unique_id}. Links formed: {self.neighbouring_leaders}")

    def step(self) -> None:
        """
        """
        self.counter += 1
        if self.counter < 10:
            self.change_target((self.pos[0], self.pos[1] + 1))
            self.move_towards(self.target_pos)
            return
        # monitor
        self.update_linked_leaders(at_empty=True)
        self.neighbours = self.get_drones_in_range()

        self.disperse()
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
        if self.is_out_of_bounds(target):
            x, y = target
            x = max(0, min(x, self.model.grid.width - 1))
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

    def get_random_direction(self):
        """
        Get a random neighbouring cell in the grid.
        """
        cells = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        return self.random.choice(cells)

    def disperse(self):
        """
        If there are more than two drones in the same cell, move one of them to a random neighbouring
        cell.
        """
        if len(self.same_cell_drones) > 2:
            new_target = self.get_random_direction()
            self.change_target(new_target)

    # TODO: Refactor
    # TODO: When more than two they are stuck and each has both left and right link so none of them can move
    # TODO: There oscillating until they reach the desired distance, fix that
    def formation(self):
        """
        For each linked neighbour, move towards the desired distance in each direction.
        """
        # Handle right leader if it exists
        if self.neighbouring_leaders.right:
            right_leader = self.neighbouring_leaders.right
            dx = self.get_dx(right_leader)
            dy = self.get_dy(right_leader)

            # Check if the leader is actually to the right
            if self.pos[0] > right_leader.pos[0]:
                # Invalid position relationship - drop the link
                self.neighbouring_leaders.drop_link('right')
                return

            # Calculate position adjustment based on distance error
            distance_error = dx - self.desired_distance

            # Positive error means we're too far, move right (toward leader)
            # Negative error means we're too close, move left (away from leader)
            self.change_target((
                self.target_pos[0] + distance_error,
                self.target_pos[1] - dy  # Correct y-axis to maintain alignment
            ))

            self.drone_logger.debug(f"Adjusting position for right leader: error={distance_error}")

        if self.neighbouring_leaders.left:
            left_leader = self.neighbouring_leaders.left
            dx = self.get_dx(left_leader)
            dy = self.get_dy(left_leader)

            # Check if the leader is actually to the left
            if self.pos[0] < left_leader.pos[0]:
                # Invalid position relationship - drop the link
                self.neighbouring_leaders.drop_link('left')
                return

            # Calculate position adjustment based on distance error
            distance_error = dx - self.desired_distance

            # Positive error means we're too far, move left (toward leader)
            # Negative error means we're too close, move right (away from leader)
            self.change_target((
                self.target_pos[0] - distance_error,
                self.target_pos[1] - dy  # Correct y-axis to maintain alignment
            ))

            self.drone_logger.debug(f"Adjusting position for left leader: error={distance_error}")

        if self.neighbouring_leaders.top:
            top_leader = self.neighbouring_leaders.top
            dx = self.get_dx(top_leader)
            dy = self.get_dy(top_leader)

            # Check if the leader is actually above
            if self.pos[1] > top_leader.pos[1]:
                # Invalid position relationship - drop the link
                self.neighbouring_leaders.drop_link('top')
                return

            # Calculate position adjustment based on distance error
            distance_error = dy - self.desired_distance

            # Positive error means we're too far, move up (toward leader)
            # Negative error means we're too close, move down (away from leader)
            self.change_target((
                self.target_pos[0] - dx,  # Correct x-axis to maintain alignment
                self.target_pos[1] + distance_error
            ))

            self.drone_logger.debug(f"Adjusting position for top leader: error={distance_error}")

        if self.neighbouring_leaders.bottom:
            bottom_leader = self.neighbouring_leaders.bottom
            dx = self.get_dx(bottom_leader)
            dy = self.get_dy(bottom_leader)

            # Check if the leader is actually below
            if self.pos[1] < bottom_leader.pos[1]:
                # Invalid position relationship - drop the link
                self.neighbouring_leaders.drop_link('bottom')
                return

            # Calculate position adjustment based on distance error
            distance_error = dy - self.desired_distance

            # Positive error means we're too far, move down (toward leader)
            # Negative error means we're too close, move up (away from leader)
            self.change_target((
                self.target_pos[0] - dx,  # Correct x-axis to maintain alignment
                self.target_pos[1] - distance_error
            ))

            self.drone_logger.debug(f"Adjusting position for bottom leader: error={distance_error}")

    def __repr__(self):
        return f"Drone {self.unique_id}, at {self.pos}"
