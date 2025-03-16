from typing import TYPE_CHECKING, Union

from src.agents.drone_modules.navigation import chebyshev_distance

if TYPE_CHECKING:
    from src.agents.drone import Drone
    from src.utils.config_loader import Config


class BatteryModule:
    def __init__(self, drone: 'Drone', config: 'Config'):
        self.drone = drone
        self.sm = drone.state_machine
        self.config = config

        self.battery_capacity: int = config.swarm.drone.battery_capacity
        self.battery_level: float = self.battery_capacity
        self.movement_cost: float = config.swarm.drone.battery_movement_cost
        self.hovering_cost: float = config.swarm.drone.battery_hovering_cost
        self.recharge_rate: float = config.swarm.drone.battery_recharge_rate
        self.low_battery_threshold: int = config.swarm.drone.battery_low_threshold

    def calculate_travel_cost(self, cells: int = 1) -> float:
        """
        Calculate the battery cost for movement without changing battery level.

        Args:
            cells: Number of cells moved (0 for hovering)

        Returns:
            float: Battery cost for the movement
        """
        if cells == 0:
            return self.hovering_cost
        else:
            return cells * self.movement_cost

    def update(self, cells: int = 1) -> None:
        """
        Update battery level due to drone movement or hovering.

        Args:
            cells: Number of cells moved (0 for hovering)
        """
        self.battery_level -= self.calculate_travel_cost(cells)

    def estimate_range(self) -> int:
        """
        Calculate how many cells the drone can travel with current battery.

        Returns:
            int: Number of cells the drone can travel
        """
        return self.battery_level // self.movement_cost

    def needs_recharging(self) -> bool:
        """
        Determine if drone needs to return to base for recharging.

        Returns:
            bool: True if drone should return to base for recharging
        """
        base = self.drone.knowledge.base_pos
        distance = chebyshev_distance(self.drone.pos, base)
        return distance > self.estimate_range() * (1 - self.low_battery_threshold / 100)

    def recharge(self) -> None:
        """
        Recharge the drone's battery. Will register a charging event
        each time the battery level increases, as long as the battery
        isn't already at full capacity.
        """
        if self.is_fully_charged():
            return

        # If battery isn't full, register a charging event
        self.drone.model.register_charging_event()

        # Add charge
        self.battery_level += self.recharge_rate

        # Cap at maximum
        if self.battery_level >= self.battery_capacity:
            self.battery_level = self.battery_capacity

    def is_fully_charged(self) -> bool:
        """
        Check if battery is at full capacity

        Returns:
            bool: True if battery is fully charged
        """
        return self.battery_level >= self.battery_capacity

    def is_depleted(self) -> bool:
        """
        Check if battery is depleted (level <= 0)

        Returns:
            bool: True if battery is depleted
        """
        return self.battery_level <= 0

    def current_charge_percentage(self) -> int:
        """
        Return battery level as a percentage of total capacity

        Returns:
            int: Battery percentage (0-100)
        """
        if self.battery_level < 0:
            return 0
        if self.battery_capacity == 0:  # Guard against division by zero
            return 0
        percentage = (self.battery_level / self.battery_capacity) * 100
        return round(percentage)

    def is_low(self, threshold: int = None) -> bool:
        """
        Check if battery percentage is below a certain warning threshold

        Args:
            threshold: Warning threshold percentage (default: from config)

        Returns:
            bool: True if battery percentage is below threshold
        """
        if threshold is None:
            threshold = self.low_battery_threshold
        return self.current_charge_percentage() < threshold
