import unittest
from unittest.mock import MagicMock

from src.agents import Cell
from src.agents.drone_modules.monitor import SensorModule


class TestSensorModule(unittest.TestCase):
    def setUp(self):
        self.mock_drone = MagicMock()
        self.mock_drone.pos = (5, 5)
        self.mock_drone.vision_range = 3

        self.monitor = SensorModule(self.mock_drone)

        # Create mock cells around the drone
        # Some are on_fire, some are not
        self.mock_cells = []
        for x in range(4, 7):  # positions from (4,4) to (6,6)
            for y in range(4, 7):
                cell = MagicMock(spec=Cell)
                cell.pos = (x, y)
                cell.on_fire = (x == 5 and y == 6) or (x == 6 and y == 5)
                self.mock_cells.append(cell)

        self.mock_drone.model.get_neighbors.return_value = self.mock_cells

    def test_detect_fire(self):
        """
        Ensure detect_fire() returns only cells on fire within vision.
        For this test, (5,6) and (6,5) are on fire and within range.
        """
        fire_cells = self.monitor.detect_fire()
        # We expect exactly these two cells to be detected
        expected_positions = {(5, 6), (6, 5)}
        self.assertIsNotNone(fire_cells)
        result_positions = {cell.pos for cell in fire_cells}

        self.assertEqual(result_positions, expected_positions)
        self.assertTrue(all(c.on_fire for c in fire_cells))

    def test_detect_fire_no_cells_in_range(self):
        """
        If no cells are on fire inside vision range, detect_fire() should return empty.
        """
        for cell in self.mock_cells:
            cell.on_fire = False

        fire_cells = self.monitor.detect_fire()
        self.assertIsNotNone(fire_cells)
        self.assertEqual(len(fire_cells), 0)


if __name__ == '__main__':
    unittest.main()
