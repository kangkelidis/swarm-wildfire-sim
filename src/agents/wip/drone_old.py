from enum import Enum
from typing import TYPE_CHECKING, List, Optional, Set, Tuple

import mesa
import numpy as np

from src.agents.cell import Cell
from src.models.movement.boid import BoidController
from src.models.movement.disperse import disperse
from src.utils.logging_config import get_logger

if TYPE_CHECKING:
    from src.simulation.simulation_model import SimulationModel

logger = get_logger()


class DroneRole(Enum):
    """Defines the different roles a drone can take."""
    SCOUT = "scout"       # Exploring the environment
    CORDON = "cordon"     # Forming a cordon around fire front
    LEADER = "leader"     # Leading a group of drones


class Drone(mesa.Agent):
    """Drone agent for wildfire monitoring."""

    def __init__(self, model: 'SimulationModel', base_pos: Tuple[int, int]):
        """

        Args:
            model: The simulation model
            base_pos: Position of the drone base
        """
        super().__init__(model)
        self.model: 'SimulationModel'

        self.base_pos = base_pos
        self.role = DroneRole.SCOUT

        # Get configuration
        self.battery_capacity = self.model.config.config.swarm.drone.battery_capacity
        self.battery_level = self.battery_capacity
        self.vision_range = int(self.model.config.config.swarm.drone.vision_range)
        self.communication_range = int(self.model.config.config.swarm.drone.communication_range)

        # For cordon formation
        self.cordon_neighbours: Set[int] = set()  # IDs of neighbouring cordon drones
        self.target_pos: Optional[Tuple[int, int]] = None


        # Boid controller for movement
        boid_config = {
            "optimal_distance": self.communication_range * 0.8,  # 80% of communication range
            "influence_radius": self.communication_range,
            "separation_weight": 1.8,  # Prioritize maintaining distance
            "cohesion_weight": 0.8,    # Reduce tendency to cluster too closely
            "purpose_weight": 1.5,     # Balance task-specific behavior
        }
        self.boid = BoidController(self, boid_config)

        self.consumption_per_cell = self.model.config.get("swarm.drone.consumption_per_cell", 1)
        self.operational_range = 0.8 * (self.battery_capacity / self.consumption_per_cell)
        self.desired_distance = self.communication_range * 0.9

        # Define 8 desired positions around the drone (angles in radians)
        # angles = [0, np.pi/4, np.pi/2, 3*np.pi/4, np.pi, 5*np.pi/4, 3*np.pi/2, 7*np.pi/4]
        self.places = [0]
        self.angle_tolerance = np.pi / 8  # 22.5 degrees

        self.network = {place: {'angle': 0, 'distance': np.inf, 'neighbor': None} for place in self.places}

        self.movement_vector = np.array([0, 0])
        self.neighbouring_leaders: list['Drone'] = []

        # neighbouring leaders
        self.left_leader: Drone = None
        self.right_leader: Drone = None
        self.top_leader: Drone = None
        self.bottom_leader: Drone = None

    def step(self):
        """Main step function for the drone."""
        # Execute behaviour based on role
        # self.disperse_behaviour()
        # if self.role == DroneRole.SCOUT:
        #     self.scout_behaviour()
        # elif self.role == DroneRole.CORDON:
        #     self.cordon_behaviour()
        movement = disperse(self)
        self.move_toward((self.pos[0] + int(movement[0]), self.pos[1] + int(movement[1])))

    def scout_behaviour(self):
        """Implementing scouting behaviour with random walk."""
        # Check for fires in vision range
        if self._detect_fire():
            self.role = DroneRole.CORDON
            return

        self.random_move()

    def cordon_behaviour(self):
        """Implementing cordoning behaviour to maintain position near fire front."""
        # Find fire cells and non-fire cells within vision range
        fire_cells, safe_cells = self._get_fire_and_safe_cells()

        if not fire_cells:
            # No more fire visible, go back to scouting
            self.role = DroneRole.SCOUT
            return

        # Find position at the edge of the fire (one cell away from fire)
        self.position_at_fire_edge(fire_cells, safe_cells)

    def _detect_fire(self) -> bool:
        """Check if there is a fire within the drone's vision range.

        Returns:
            True if fire is detected, False otherwise
        """
        neighbours = self.model.grid.get_neighbors(
            self.pos, moore=True, radius=self.vision_range
        )

        # Check for fires
        for neighbour in neighbours:
            if isinstance(neighbour, Cell) and neighbour.on_fire:
                return True

        return False

    def _get_fire_and_safe_cells(self) -> Tuple[List[Cell], List[Cell]]:
        """Get lists of fire cells and safe cells within vision range.

        Returns:
            Tuple of (fire_cells, safe_cells)
        """
        neighbours = self.model.grid.get_neighbors(
            self.pos, moore=True, radius=self.vision_range
        )

        fire_cells = []
        safe_cells = []

        for neighbour in neighbours:
            if isinstance(neighbour, Cell):
                if neighbour.on_fire:
                    fire_cells.append(neighbour)
                elif not neighbour.burnt:
                    safe_cells.append(neighbour)

        return fire_cells, safe_cells

    def position_at_fire_edge(self, fire_cells: List[Cell], safe_cells: List[Cell]) -> None:
        """Find the optimal position at the edge of the fire.

        Args:
            fire_cells: List of cells that are on fire
            safe_cells: List of cells that are safe
        """
        # Simple algorithm: find a safe cell that's adjacent to a fire cell
        edge_positions = []

        # for safe_cell in safe_cells:
        #     # Check if this safe cell is adjacent to any fire cell
        #     is_edge = False
        #     safe_neighbours = self.model.grid.get_neighbors(
        #         safe_cell.pos, moore=True, radius=1
        #     )

        #     for neighbour in safe_neighbours:
        #         if isinstance(neighbour, Cell) and neighbour.on_fire:
        #             is_edge = True
        #             break

        #     if is_edge:
                # edge_positions.append(safe_cell.pos)

        # Move to the furthest safe cell
        if safe_cells:
            target_pos = max(safe_cells, key=lambda p: self._distance(p.pos, self.pos)).pos
            self.model.grid.move_agent(self, target_pos)

        # if edge_positions:
        #     # Move to the closest edge position
        #     # target_pos = max(edge_positions, key=lambda p: self._distance(p, self.pos))
        #     # self.move_toward(target_pos)
        # else:
        #     logger.debug("No edge positions found for cordon drone")

    def random_move(self) -> None:
        """Move randomly to an adjacent cell."""
        possible_steps = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=False
        )

        if possible_steps:
            new_position = self.model.random.choice(possible_steps)
            self.model.grid.move_agent(self, new_position)

    def move_toward(self, target_pos: Tuple[int, int]) -> None:
        """Move one step towards the target position.

        Args:
            target_pos: Position to move towards
        """
        # Get possible moves (adjacent cells)
        possible_steps = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=False
        )

        if not possible_steps:
            return  # No valid moves

        # Find the step that gets us closest to the target
        new_pos = min(possible_steps, key=lambda pos: self._distance(pos, target_pos))
        self.model.grid.move_agent(self, new_pos)

    def _distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> float:
        """Calculate Euclidean distance between two positions.

        Args:
            pos1: First position
            pos2: Second position

        Returns:
            Euclidean distance
        """
        return ((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2) ** 0.5

    def disperse_behaviour(self) -> None:
        """Leader drones disperse to maintain optimal coverage of the area."""
        # Calculate operational parameters

        neighbors = self.get_neighbours()
        if not neighbors:
            return

        for neighbor in neighbors:
            dx = self.pos[0] - neighbor.pos[0]
            dy = self.pos[1] - neighbor.pos[1]
            distance = int(self._distance(self.pos, neighbor.pos))

            angle = np.arctan2(dy, dx)
            if angle < 0:
                angle += 2 * np.pi

            # if it is under the angle tolerance
            if abs(angle - self.places[0]) < self.angle_tolerance:
                if abs(self.desired_distance - distance) < self.network[0]['distance']:
                    self.network[0] = {'angle': angle, 'distance': abs(self.desired_distance - distance), 'neighbor': neighbor}

        for place, info in self.network.items():
            if info['neighbor'] is not None:
                # adjust the x and y vectors to match the desired distance and angle,
                # the info hold the current angle and distance
                # the desired angle is the place
                print(f'--me:{self.unique_id}, neighbor: {info["neighbor"].unique_id}, {info["neighbor"].pos}, dx: {dx}, dy: {dy}, distance: {info['distance']}')

                heading = 1 if dx != 0 else self.model.random.choice([1, -1])
                y_noise = self.model.random.choice([0, 1])
                target_x = self.desired_distance - abs(dx)
                target_x = target_x if dx > 0 else -target_x

                target_y = self.desired_distance - abs(dy)
                target_y = target_y if dy > 0 else -target_y

                target_y = self.communication_range * 0.9 if self.pos[1] < self.communication_range else target_y
                self.movement_vector = np.array([target_x * heading, target_y])

        if abs(distance - self.desired_distance) < 1:
            self.movement_vector = np.array([0, 0])

        # Move the drone
        self.move_toward((self.pos[0] + int(self.movement_vector[0]), self.pos[1] + int(self.movement_vector[1])))
        print(f'---+moved me:{self.unique_id}, {self.pos}, {self.movement_vector}')

    def get_neighbours(self) -> List['Drone']:
        """Get all drones within communication range."""
        if not self.pos:
            return []
        neighbors = self.model.grid.get_neighbors(
            self.pos, moore=True, radius=self.communication_range, include_center=True
        )
        return [n for n in neighbors if isinstance(n, Drone) and n != self]

