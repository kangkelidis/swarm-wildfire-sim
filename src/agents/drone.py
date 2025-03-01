from enum import Enum
from typing import TYPE_CHECKING, List, Optional, Set, Tuple

import mesa
import numpy as np

from src.agents.cell import Cell
from src.utils.logging_config import get_logger

if TYPE_CHECKING:
    from src.simulation.simulation_model import SimulationModel

logger = get_logger()


class DroneRole(Enum):
    """Defines the different roles a drone can take."""
    SCOUT = "scout"       # Exploring the environment
    CORDON = "cordon"     # Forming a cordon around fire


class Drone(mesa.Agent):
    """Drone agent for wildfire monitoring and response."""

    def __init__(self, model: 'SimulationModel', pos: Tuple[int, int], base_pos: Tuple[int, int]):
        """Initialize a new drone.

        Args:
            model: The simulation model
            pos: Initial position
            base_pos: Position of the drone base
        """
        super().__init__(model)
        self.model: 'SimulationModel'

        self.pos = pos
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

    def step(self):
        """Main step function for the drone."""
        # Execute behaviour based on role
        if self.role == DroneRole.SCOUT:
            self.scout_behaviour()
        elif self.role == DroneRole.CORDON:
            self.cordon_behaviour()

    def scout_behaviour(self):
        """Implementing scouting behaviour with random walk."""
        # Check for fires in vision range
        if self._detect_fire():
            self.role = DroneRole.CORDON
            return

        # Random walk
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

        for safe_cell in safe_cells:
            # Check if this safe cell is adjacent to any fire cell
            is_edge = False
            safe_neighbours = self.model.grid.get_neighbors(
                safe_cell.pos, moore=True, radius=1
            )

            for neighbour in safe_neighbours:
                if isinstance(neighbour, Cell) and neighbour.on_fire:
                    is_edge = True
                    break

            if is_edge:
                edge_positions.append(safe_cell.pos)

        if edge_positions:
            # Move to the closest edge position
            target_pos = min(edge_positions, key=lambda p: self._distance(p, self.pos))
            self.move_toward(target_pos)

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
