import os
import sys
from pathlib import Path

import solara

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import matplotlib.pyplot as plt
from mesa.visualization import SolaraViz, make_space_component

from src.simulation.simulation_model import SimulationModel
from src.utils.config_loader import ConfigLoader
from src.utils.logging_config import get_logger
from src.visualisation.solara.components import RuntimeControls, TopologyGraph
from src.visualisation.solara.custom_elements import agent_portrayal

logger = get_logger()


def main():
    """Main entry point for the Solara app"""

    # Get configuration from environment variables
    config_path = os.environ.get("WILDFIRE_CONFIG")
    output_gif = os.environ.get("WILDFIRE_OUTPUT_GIF")

    # Initialise config and model
    config = ConfigLoader(config_path)
    model = SimulationModel(config)

    # Set up size for space graph
    area_size = config.config.simulation.area_size
    a, b  = (12, 12) if area_size == "large" else (10, 10)
    plt.rcParams["figure.figsize"] = (a, b)

    # Create visualization components
    SpaceGraph = make_space_component(agent_portrayal, draw_grid=False)

    # Define model parameters for UI controls
    model_params = {
        "num_of_bases": {
            "label": "Deployment Bases",
            "type": "SliderInt",
            "value": config.config.swarm.initial_bases,
            "min": 0,
            "max": 10,
            "step": 1,
        },
        "num_of_agents": {
            "label": "Agents (per Base)  ",
            "type": "SliderInt",
            "value": config.config.swarm.drone_base.number_of_agents,
            "min": 1,
            "max": 100,
            "step": 1,
        }
    }

    # Create Solara visualization
    page = SolaraViz(
        model,
        components=[SpaceGraph, TopologyGraph, RuntimeControls],
        model_params=model_params,
        name="Wildfire Simulation",
        play_interval=1,
    )

    # If output-gif was specified, save the visualization
    if output_gif:
        # This would require additional code to save animation frames
        pass

    return page


# Application entry point
page = main()
