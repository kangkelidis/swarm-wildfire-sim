import argparse
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import matplotlib.pyplot as plt
from mesa.visualization import SolaraViz, make_space_component

from src.simulation.simulation_model import SimulationModel
from src.utils.config import Config
from src.utils.logging_config import get_logger
from src.visualisation.solara.custom_elements import agent_portrayal

logger = get_logger()

plt.rcParams["figure.figsize"] = (10, 10)


def main():
    """Main entry point for the Solara app"""

    # Get configuration from environment variables
    config_path = os.environ.get("WILDFIRE_CONFIG")
    output_gif = os.environ.get("WILDFIRE_OUTPUT_GIF")

    # Initialise config and model
    config = Config(config_path)
    model = SimulationModel(config)

    # Create visualization components
    SpaceGraph = make_space_component(agent_portrayal, draw_grid=False)

    # Create additional visualization components as needed

    # Define model parameters for UI controls (if needed)
    model_params = {
        "N": {
            "label": "Number of agents per base",
            "type": "InputText",
            "value": config.config.swarm.drone_base.number_of_agents},
    }

    # Create Solara visualization
    page = SolaraViz(
        model,
        components=[SpaceGraph],
        model_params=model_params,
        name="Wildfire Simulation",
    )

    # If output-gif was specified, save the visualization
    if output_gif:
        # This would require additional code to save animation frames
        pass

    return page


# Application entry point
page = main()
