import unittest
from unittest.mock import MagicMock, patch

from src.agents import Cell, Drone
from src.simulation.simulation_model import SimulationModel


class TestSimulationModule(unittest.TestCase):
    def setUp(self):
        # Create model
        with patch('src.simulation.simulation_model.GridEnvironment') as mock_grid:
            # Mock the grid's get_neighbors method
            self.mock_neighbors_method = MagicMock()
            mock_grid.return_value.get_neighbors = self.mock_neighbors_method
            mock_grid = mock_grid.return_value
            mock_grid.width = 100
            mock_grid.height = 100

            mock_config = MagicMock()
            mock_config.simulation._width = 100
            mock_config.simulation._height = 100
            mock_config.simulation.seed = 42
            mock_config.get.return_value = 42

            mock_config_loader = MagicMock()
            mock_config_loader.config = mock_config
            # Create simulation model
            self.model = SimulationModel(mock_config_loader)
            self.model.grid = mock_grid

    def test_get_neighbors_without_type_filter(self):
        """Test get_neighbors without type filtering."""
        # Create test data
        test_pos = (10, 10)
        mock_cell1 = MagicMock(spec=Cell)
        mock_cell2 = MagicMock(spec=Cell)
        mock_drone = MagicMock(spec=Drone)
        mock_agents = [mock_cell1, mock_cell2, mock_drone]

        # Configure mock to return test agents
        self.mock_neighbors_method.return_value = mock_agents

        # Call the method
        result = self.model.get_neighbors(test_pos, moore=True, include_center=False, radius=1)

        # Verify results
        self.assertEqual(result, mock_agents)
        self.mock_neighbors_method.assert_called_once_with(test_pos, True, False, 1)

    def test_get_neighbors_with_type_filter(self):
        """Test get_neighbors with type filtering."""
        # Create test data
        test_pos = (10, 10)
        mock_cell1 = MagicMock(spec=Cell)
        mock_cell2 = MagicMock(spec=Cell)
        mock_drone = MagicMock(spec=Drone)
        mock_agents = [mock_cell1, mock_cell2, mock_drone]

        # Configure mock to return test agents
        self.mock_neighbors_method.return_value = mock_agents

        # Call the method with type filter
        result = self.model.get_neighbors(test_pos, moore=True, include_center=False, radius=1, type='Cell')

        # Verify results
        self.assertEqual(len(result), 2)
        self.assertIn(mock_cell1, result)
        self.assertIn(mock_cell2, result)
        self.assertNotIn(mock_drone, result)
        self.mock_neighbors_method.assert_called_once_with(test_pos, True, False, 1)

    def test_get_neighbors_with_custom_params(self):
        """Test get_neighbors with custom parameters."""
        # Create test data
        test_pos = (20, 20)
        mock_agents = [MagicMock() for _ in range(5)]

        # Configure mock to return test agents
        self.mock_neighbors_method.return_value = mock_agents

        # Call the method with custom parameters
        result = self.model.get_neighbors(test_pos, moore=False, include_center=True, radius=2)

        # Verify results
        self.assertEqual(result, mock_agents)
        self.mock_neighbors_method.assert_called_once_with(test_pos, False, True, 2)


if __name__ == '__main__':
    unittest.main()
