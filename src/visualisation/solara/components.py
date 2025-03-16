from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import solara
from mesa.visualization.utils import update_counter

if TYPE_CHECKING:
    from src.simulation.simulation_model import SimulationModel


@solara.component
def RuntimeControls(model):
    """Component for runtime simulation controls."""

    fire_count = solara.use_state(1)

    def start_random_fire():
        """Start a random fire in the simulation."""
        model.start_fire(num_fires=fire_count)

    def add_base():
        """Add a new base to the simulation."""
        model.add_base()

    with solara.Sidebar(), solara.Column():
        with solara.Card("Runtime Controls", style={"width": "fit-content"}):
            with solara.Column():
                with solara.Row():
                    solara.Button(
                        "Start Random Fire",
                        color="error",
                        outlined=True,
                        on_click=start_random_fire)

                    solara.Button(
                        "Add Base",
                        color="success",
                        outlined=True,
                        on_click=add_base)


@solara.component
def TopologyGraph(model):
    """Component to display the network topology graph directly using Matplotlib"""
    figure = solara.use_reactive(None)
    update_counter.get()

    def update_graph():
        """Update the graph visualization"""
        fig = model.display_topology()
        figure.value = fig

    # Update on component mount and each frame
    solara.use_effect(update_graph, [model.steps])

    with solara.Card("Network Topology"):
        if figure.value:
            solara.FigureMatplotlib(figure.value)
        else:
            solara.Info("No network topology available")


@solara.component
def CostComponent(model: 'SimulationModel'):
    update_counter.get()
    with solara.Sidebar(), solara.Column():
        with solara.Card("Metrics"):
            solara.Text(f"Cost: {model.total_cost:.2f}")
