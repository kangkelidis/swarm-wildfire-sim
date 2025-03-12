
import solara


@solara.component
def RuntimeControls(model):
    """Component for runtime simulation controls."""

    fire_count, set_fire_count = solara.use_state(1)

    def start_random_fire():
        """Start a random fire in the simulation."""
        model.start_fire(num_fires=fire_count)

    def add_base():
        """Add a new base to the simulation."""
        model.add_base()

    with solara.Card("Runtime Controls", style={"width": "fit-content"}):
        with solara.Column():
            with solara.Row():
                solara.Button(
                    "Start Random Fire",
                    color="error",
                    outlined=True,
                    on_click=start_random_fire
                )

                solara.Button(
                    "Add Base",
                    color="success",
                    outlined=True,
                    on_click=add_base
                )
