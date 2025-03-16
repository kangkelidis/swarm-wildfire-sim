import unittest
from unittest.mock import MagicMock

from src.agents.drone_modules.battery import BatteryModule


class TestBatteryModule(unittest.TestCase):
    def _make_battery(self, **kwargs):
        """Helper method to create a battery module with custom config values.

        Args:
            **kwargs: Override default config values (e.g., battery_capacity=200)

        Returns:
            BatteryModule: Configured battery module for testing
        """
        # Default config values
        config_values = {
            'battery_capacity': 100.0,
            'battery_movement_cost': 1.0,
            'battery_hovering_cost': 0.5,
            'battery_recharge_rate': 5.0,
            'battery_low_threshold': 20
        }

        # Override with any provided values
        config_values.update(kwargs)

        # Create mock objects
        mock_drone = MagicMock()
        mock_drone.pos = (10, 10)
        mock_drone.knowledge = MagicMock()
        mock_drone.knowledge.base_pos = (0, 0)

        # Create a proper nested config structure
        mock_drone_config = MagicMock()
        mock_drone_config.battery_capacity = config_values['battery_capacity']
        mock_drone_config.battery_movement_cost = config_values['battery_movement_cost']
        mock_drone_config.battery_hovering_cost = config_values['battery_hovering_cost']
        mock_drone_config.battery_recharge_rate = config_values['battery_recharge_rate']
        mock_drone_config.battery_low_threshold = config_values['battery_low_threshold']

        mock_swarm = MagicMock()
        mock_swarm.drone = mock_drone_config

        mock_config = MagicMock()
        mock_config.swarm = mock_swarm

        return BatteryModule(mock_drone, mock_config)

    def test_is_depleted(self):
        """Test if is_depleted returns True when battery level is <= 0"""
        # Create battery with default config
        battery = self._make_battery()

        # Battery starts at full capacity (100)
        self.assertFalse(battery.is_depleted())

        # Set battery level to exactly 0
        battery.battery_level = 0.0
        self.assertTrue(battery.is_depleted())

        # Set battery level to negative value
        battery.battery_level = -5.0
        self.assertTrue(battery.is_depleted())

    def test_current_charge_percentage(self):
        """Test if current_charge_percentage returns correct percentage"""
        # Create battery with default config
        battery = self._make_battery()

        # Battery starts at full capacity (100)
        self.assertEqual(battery.current_charge_percentage(), 100)

        # Set battery to half capacity
        battery.battery_level = 50.0
        self.assertEqual(battery.current_charge_percentage(), 50)

        # Set battery to low level
        battery.battery_level = 10.0
        self.assertEqual(battery.current_charge_percentage(), 10)

        # Set battery to 0
        battery.battery_level = 0.0
        self.assertEqual(battery.current_charge_percentage(), 0)

        # Set battery to negative (should return 0%)
        battery.battery_level = -5.0
        self.assertEqual(battery.current_charge_percentage(), 0)

        # Test with larger capacity
        high_capacity_battery = self._make_battery(battery_capacity=200.0)
        high_capacity_battery.battery_level = 50.0
        self.assertEqual(high_capacity_battery.current_charge_percentage(), 25)  # 50/200 * 100 = 25%

    def test_is_low(self):
        """Test if is_low returns True when battery percentage is below threshold"""
        # Create battery with default config (threshold=20)
        battery = self._make_battery()

        # Battery starts at full capacity (100)
        self.assertFalse(battery.is_low())

        # Set battery to 25%
        battery.battery_level = 25.0
        self.assertFalse(battery.is_low())

        # Set battery to 20% (edge case - exactly at threshold)
        battery.battery_level = 20.0
        self.assertFalse(battery.is_low())

        # Set battery to 19% (just below threshold)
        battery.battery_level = 19.0
        self.assertTrue(battery.is_low())

        # Set battery to 0
        battery.battery_level = 0.0
        self.assertTrue(battery.is_low())

        # Test with custom threshold parameter
        battery.battery_level = 30.0
        self.assertFalse(battery.is_low(threshold=25))
        self.assertTrue(battery.is_low(threshold=35))

        # Test with different config threshold
        high_threshold_battery = self._make_battery(battery_low_threshold=40)
        high_threshold_battery.battery_level = 45.0
        self.assertFalse(high_threshold_battery.is_low())
        high_threshold_battery.battery_level = 35.0
        self.assertTrue(high_threshold_battery.is_low())

    def test_calculate_travel_cost(self):
        """Test if calculate_travel_cost correctly estimates cost without changing battery level"""
        scenarios = [
            {'movement_cost': 1.0, 'hovering_cost': 0.5},
            {'movement_cost': 2.0, 'hovering_cost': 1.0},
            {'movement_cost': 0.5, 'hovering_cost': 0.2},
        ]

        cells_to_move = 5

        for scenario in scenarios:
            with self.subTest(scenario=scenario):
                # Create battery with scenario's values
                battery = self._make_battery(
                    battery_movement_cost=scenario['movement_cost'],
                    battery_hovering_cost=scenario['hovering_cost']
                )

                original_level = battery.battery_level

                # Calculate cost for moving cells
                cost = battery.calculate_travel_cost(cells_to_move)

                # Cost should be cells * movement_cost
                expected_cost = cells_to_move * scenario['movement_cost']
                self.assertEqual(cost, expected_cost)

                # Battery level should remain unchanged by calculation
                self.assertEqual(battery.battery_level, original_level)

                # Test hovering cost
                hover_cost = battery.calculate_travel_cost(0)
                self.assertEqual(hover_cost, scenario['hovering_cost'])

                # Battery level should still be unchanged
                self.assertEqual(battery.battery_level, original_level)

    def test_update(self):
        """Test if update correctly modifies battery level"""
        scenarios = [
            {'movement_cost': 1.0, 'hovering_cost': 0.5},
            {'movement_cost': 2.0, 'hovering_cost': 1.0},
            {'movement_cost': 0.5, 'hovering_cost': 0.2},
        ]

        cells_to_move = 5

        for scenario in scenarios:
            with self.subTest(scenario=scenario):
                # Create battery with scenario's values
                battery = self._make_battery(
                    battery_movement_cost=scenario['movement_cost'],
                    battery_hovering_cost=scenario['hovering_cost']
                )

                # Set battery to full
                battery.battery_level = 100.0

                # Move cells
                battery.update(cells_to_move)
                expected = 100.0 - (cells_to_move * scenario['movement_cost'])
                self.assertEqual(battery.battery_level, expected)

                # Save level after movement
                level_after_movement = battery.battery_level

                # Hover (no cells moved)
                battery.update(0)
                expected = level_after_movement - scenario['hovering_cost']
                self.assertEqual(battery.battery_level, expected)

    def test_is_fully_charged(self):
        """Test if is_fully_charged returns correct status"""
        # Test with different capacities
        capacities = [100.0, 200.0, 50.0]

        for capacity in capacities:
            with self.subTest(capacity=capacity):
                battery = self._make_battery(battery_capacity=capacity)

                # Full capacity
                self.assertTrue(battery.is_fully_charged())

                # Slightly below capacity
                battery.battery_level = capacity - 0.1
                self.assertFalse(battery.is_fully_charged())

                # At exact capacity
                battery.battery_level = capacity
                self.assertTrue(battery.is_fully_charged())

                # Above capacity (should not happen normally but test anyway)
                battery.battery_level = capacity + 5.0
                self.assertTrue(battery.is_fully_charged())

    def test_recharge(self):
        """Test if recharge correctly increases battery level"""
        scenarios = [
            {'recharge_rate': 5.0, 'initial_level': 90.0},
            {'recharge_rate': 10.0, 'initial_level': 80.0},
            {'recharge_rate': 2.5, 'initial_level': 95.0},
        ]

        for scenario in scenarios:
            with self.subTest(scenario=scenario):
                battery = self._make_battery(battery_recharge_rate=scenario['recharge_rate'])
                battery.battery_level = scenario['initial_level']

                # Recharge once
                battery.recharge()
                expected = min(100.0, scenario['initial_level'] + scenario['recharge_rate'])
                self.assertEqual(battery.battery_level, expected)

                # Check that charging event was registered
                self.assertEqual(battery.drone.model.register_charging_event.call_count, 1)

                # If not yet fully charged, recharge again
                if battery.battery_level < 100.0:
                    battery.recharge()
                    expected = min(100.0, expected + scenario['recharge_rate'])
                    self.assertEqual(battery.battery_level, expected)
                    self.assertEqual(battery.drone.model.register_charging_event.call_count, 2)

                # Reset call count for next test
                battery.drone.model.register_charging_event.reset_mock()

                # Test that no additional charging event is registered when already full
                battery.battery_level = 100.0
                battery.recharge()
                self.assertEqual(battery.battery_level, 100.0)
                self.assertEqual(battery.drone.model.register_charging_event.call_count, 0)

    def test_estimate_range(self):
        """Test if estimate_range returns correct cell count"""
        scenarios = [
            {'movement_cost': 1.0, 'levels': [100.0, 75.0, 50.0, 0.0]},
            {'movement_cost': 2.0, 'levels': [100.0, 75.0, 50.0, 0.0]},
            {'movement_cost': 0.5, 'levels': [100.0, 75.0, 50.0, 0.0]},
        ]

        for scenario in scenarios:
            with self.subTest(scenario=scenario):
                battery = self._make_battery(battery_movement_cost=scenario['movement_cost'])

                for level in scenario['levels']:
                    battery.battery_level = level
                    expected_range = level // scenario['movement_cost']
                    self.assertEqual(battery.estimate_range(), expected_range)

    def test_needs_recharging(self):
        """Test if needs_recharging correctly determines when to return to base"""
        # Scenario structure:
        # - movement_cost: cost per cell
        # - low_threshold: low battery threshold percentage
        # - distances: tuples of (base_pos, drone_pos) to test
        # - levels: battery levels to test
        scenarios = [
            {
                'movement_cost': 1.0,
                'low_threshold': 20,
                'distances': [((0, 0), (10, 10)), ((0, 0), (30, 30))],
                'levels': [100.0, 50.0, 30.0, 20.0, 15.0, 10.0]
            },
            {
                'movement_cost': 2.0,
                'low_threshold': 20,
                'distances': [((0, 0), (10, 10)), ((0, 0), (20, 20))],
                'levels': [100.0, 70.0, 50.0, 30.0, 20.0]
            },
            {
                'movement_cost': 1.0,
                'low_threshold': 40,
                'distances': [((0, 0), (10, 10)), ((0, 0), (20, 20))],
                'levels': [100.0, 60.0, 40.0, 30.0, 20.0]
            },
        ]

        for scenario in scenarios:
            with self.subTest(scenario=scenario):
                battery = self._make_battery(
                    battery_movement_cost=scenario['movement_cost'],
                    battery_low_threshold=scenario['low_threshold']
                )

                for base_pos, drone_pos in scenario['distances']:
                    # Set positions for this test case
                    battery.drone.knowledge.base_pos = base_pos
                    battery.drone.pos = drone_pos

                    # Calculate the distance using Chebyshev distance (max of x,y difference)
                    distance = max(abs(drone_pos[0] - base_pos[0]), abs(drone_pos[1] - base_pos[1]))

                    for level in scenario['levels']:
                        battery.battery_level = level

                        # Calculate if recharging is needed
                        # Using formula: distance > range * (1 - threshold/100)
                        range_estimate = level // scenario['movement_cost']
                        safety_factor = 1 - scenario['low_threshold'] / 100
                        expected_needs_recharging = distance > range_estimate * safety_factor

                        with self.subTest(base=base_pos, drone=drone_pos, level=level):
                            # Test against the actual implementation
                            self.assertEqual(battery.needs_recharging(), expected_needs_recharging)


if __name__ == '__main__':
    unittest.main()
