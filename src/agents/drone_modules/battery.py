from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.agents.drone import Drone
    from src.utils.config_loader import Config


class BatteryModule:
    def __init__(self, drone: 'Drone', config: 'Config'):
        self.drone = drone
        self.sm = drone.state_machine
        self.config = config
        self.battery_level: float = config.swarm.drone.battery_capacity
        self.cost = config.swarm.drone.battery_consumption_per_cell
        self.recharge_rate = config.swarm.drone.battery_recharge_rate

    def update(self, cells: int = 1):
        if cells == 0:
            # Hovering
            self.battery_level -= self.cost // 3
        else:
            self.battery_level -= cells * self.cost

    def estimate_range(self):
        return self.battery_level // self.cost

    def needs_recharging(self):
        base = self.drone.knowledge.base_pos
        distance = self.drone.navigation.chebyshev_distance(base)
        return distance > self.estimate_range() * 0.8

    def recharge(self):
        self.drone.drone_logger.debug(f"Recharging drone {self.drone.unique_id}, battery level: {self.battery_level}")
        self.battery_level += self.recharge_rate
        if self.battery_level >= self.config.swarm.drone.battery_capacity:
            self.battery_level = self.config.swarm.drone.battery_capacity

    def is_fully_recharged(self):
        return self.battery_level == self.config.swarm.drone.battery_capacity
