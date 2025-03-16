import unittest
from unittest.mock import MagicMock, patch

from src.agents.drone import Drone
from src.simulation.simulation_model import SimulationModel
from src.utils.config_loader import Config, ConfigLoader


class TestDroneCosts(unittest.TestCase):
    """Tests for drone deployment and charging costs calculation."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a mock ConfigLoader with test values
        self.config = Config()
        self.config.simulation.deployment_cost = 10.0
        self.config.simulation.charge_cost = 5.0

        # Mock config loader
        self.config_loader = MagicMock()
        self.config_loader.config = self.config

        # Create a simulation model with mocked config
        with patch('src.simulation.simulation_model.GridEnvironment'), \
             patch('src.simulation.simulation_model.SimpleFireModel'), \
             patch.object(SimulationModel, 'add_base'):
            self.model = SimulationModel(config_loader=self.config_loader)
            # Make sure the total cost starts at 0
            self.model.total_cost = 0.0
            self.model.drone_deployments = 0
            self.model.charging_events = 0

    def test_initial_cost_is_zero(self):
        """Test that the model starts with zero cost."""
        self.assertEqual(self.model.total_cost, 0.0)
        self.assertEqual(self.model.drone_deployments, 0)
        self.assertEqual(self.model.charging_events, 0)

    def test_deployment_cost(self):
        """Test cost calculation for drone deployments."""
        # Simulate deploying 3 drones
        self.model.register_drone_deployment(3)

        # Check that costs have been updated
        expected_cost = 3 * self.config.simulation.deployment_cost
        self.assertEqual(self.model.total_cost, expected_cost)
        self.assertEqual(self.model.drone_deployments, 3)

    def test_charging_cost(self):
        """Test cost calculation for drone charging."""
        # Simulate a drone charging event
        self.model.register_charging_event()

        # Check that costs have been updated
        expected_cost = self.config.simulation.charge_cost
        self.assertEqual(self.model.total_cost, expected_cost)
        self.assertEqual(self.model.charging_events, 1)

    def test_combined_costs(self):
        """Test combined cost calculation for deployments and charging."""
        # Simulate deploying 2 drones
        self.model.register_drone_deployment(2)

        # Simulate 3 charging events
        for _ in range(3):
            self.model.register_charging_event()

        # Check that costs have been updated correctly
        expected_cost = (2 * self.config.simulation.deployment_cost) + \
                        (3 * self.config.simulation.charge_cost)
        self.assertEqual(self.model.total_cost, expected_cost)
        self.assertEqual(self.model.drone_deployments, 2)
        self.assertEqual(self.model.charging_events, 3)

    def test_get_cost_details(self):
        """Test getting a detailed breakdown of costs."""
        # Simulate some deployments and charges
        self.model.register_drone_deployment(5)
        for _ in range(2):
            self.model.register_charging_event()

        # Get cost details
        details = self.model.get_cost_details()

        # Verify the details
        self.assertEqual(details['drone_deployments'], 5)
        self.assertEqual(details['charging_events'], 2)
        self.assertEqual(details['deployment_cost'], 5 * self.config.simulation.deployment_cost)
        self.assertEqual(details['charging_cost'], 2 * self.config.simulation.charge_cost)
        self.assertEqual(details['total_cost'], details['deployment_cost'] + details['charging_cost'])


if __name__ == '__main__':
    unittest.main()
