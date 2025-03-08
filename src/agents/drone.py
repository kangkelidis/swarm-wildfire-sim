"""
Drone agent class.
"""

from typing import TYPE_CHECKING

import mesa

from src.utils.logging_config import DroneLogger, get_logger

if TYPE_CHECKING:
    from src.simulation.simulation_model import SimulationModel


logger = get_logger()


class Drone(mesa.Agent):
    """
    Drone agent class.

    Attributes:

    """
    def __init__(self, model: 'SimulationModel', base_pos: tuple[int, int]):
        """
        Initialise the drone agent.

        Args:
            model: The simulation model
            base_pos: The position of the base station the drone is deployed from
        """
        super().__init__(model)
        self.model: 'SimulationModel'
        self.base_pos = base_pos
        self.communication_range = int(model.config.config.swarm.drone.communication_range)
        self.desired_distance = int(self.communication_range * 0.9)
        self.target_pos: tuple[int, int] = None

        # initialise neighbours
        self.neighbours = self.get_drones_in_range()
        self.same_cell_drones = []

        self.debug = False
        self.drone_logger = DroneLogger(logger)

        self.color = 'blue'

    def set_up(self) -> None:
        """
        Post-init setup for the drone agent. To be called after the agent has been added to the
        model and has a position.
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

        self.disperse()

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

    def get_dx(self, other: 'Drone') -> int:
        """
        Get the absolute distance in the x-axis between this drone and another drone.
        """
        return int(abs(other.pos[0] - self.pos[0]))

    def get_dy(self, other: 'Drone') -> int:
        """
        Get the absolute distance in the y-axis between this drone and another drone.
        """
        return int(abs(other.pos[1] - self.pos[1]))

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
        if x >= self.model.grid.width - 5:
            x -= 2
        if y <= 5:
            y += 2
        if y >= self.model.grid.height - 5:
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

    def disperse(self):
        """
        If there are more than two drones in the same cell, move one of them to a random neighbouring
        cell.
        """
        if len(self.same_cell_drones) > 0:
            self.color = "blue"
            new_target = self.get_random_direction(including_center=False)
            self.change_target(new_target)
        else:
            self.formation()
            # self.strict_formation()

    def random_walk(self):
        """
        Move the drone to a random neighbouring cell or stay.
        """
        new_target = self.get_random_direction(including_center=True)
        self.change_target(new_target)

    def nudge_to_align(self, closest_neighbour):
        """
        Nudge the drone to align with the axis if one of the axis is not aligned.
        """
        x, y = self.pos
        neighbor_x, neighbor_y = closest_neighbour.pos
        dx = self.get_dx(closest_neighbour)
        dy = self.get_dy(closest_neighbour)

        if dx == self.desired_distance:
            if dy != 0:
                y = neighbor_y
                self.color = "yellow"
                self.change_target((x, y))
        elif dy == self.desired_distance:
            if dx != 0:
                x = neighbor_x
                self.color = "yellow"
                self.change_target((x, y))
        else:
            self.color = "purple"

    def strict_formation(self):
        if not self.neighbours:
            self.random_walk()
            self.color = "red"
            return

        # Find the closest neighbor
        closest_neighbour = min(self.neighbours, key=lambda n: self.chebyshev_distance(n.pos))
        current_distance = self.chebyshev_distance(closest_neighbour.pos)
        dx = self.get_dx(closest_neighbour)
        dy = self.get_dy(closest_neighbour)
        axis_to_align = 'x' if dx < dy else 'y'

        # Stay in place if already at desired distance and aligned
        if current_distance == self.desired_distance and (dx == 0 or dy == 0):
            self.color = "purple"
            return

        self.color = "blue"
        # Calculate direction (move away if too close, move closer if too far)
        x, y = self.pos
        neighbor_x, neighbor_y = closest_neighbour.pos

        if current_distance < self.desired_distance:
            # align on an axis and increase chebyshev distance on the other
            if axis_to_align == 'x':
                if x < neighbor_x:
                    x += 1
                elif x > neighbor_x:
                    x -= 1
                if y < neighbor_y:
                    y -= 1
                elif y > neighbor_y:
                    y += 1
                self.change_target((x, y))
            else:
                if x < neighbor_x:
                    x -= 1
                elif x > neighbor_x:
                    x += 1
                if y < neighbor_y:
                    y += 1
                elif y > neighbor_y:
                    y -= 1
                self.change_target((x, y))
        elif current_distance > self.desired_distance:
            if axis_to_align == 'x':
                if x < neighbor_x:
                    x += 1
                elif x > neighbor_x:
                    x -= 1
                if y < neighbor_y:
                    y += 1
                elif y > neighbor_y:
                    y -= 1
                self.change_target((x, y))
            else:
                if x < neighbor_x:
                    x += 1
                elif x > neighbor_x:
                    x -= 1
                if y < neighbor_y:
                    y += 1
                elif y > neighbor_y:
                    y -= 1
                self.change_target((x, y))

    def formation(self):
        """
        Handle formation behaviour for drones.
        Find the closest neighbour, check the chebyshev distance and if it less than the desired
        distance, move away to increase the distance by one, reduce by one otherwise.
        """
        if not self.neighbours:
            self.random_walk()
            self.color = "red"
            return

        # Find the closest neighbor
        closest_neighbour = min(self.neighbours, key=lambda n: self.chebyshev_distance(n.pos))
        current_distance = self.chebyshev_distance(closest_neighbour.pos)

        # Stay in place if already at desired distance
        if current_distance == self.desired_distance:
            self.color = "purple"
            # self.nudge_to_align(closest_neighbour)
            return

        self.color = "blue"
        # Calculate direction (move away if too close, move closer if too far)
        x, y = self.pos
        neighbor_x, neighbor_y = closest_neighbour.pos

        if current_distance < self.desired_distance:
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
        elif current_distance > self.desired_distance:
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
