from src.agents.base import DroneBase
from src.agents.cell import Cell, FuelLevel
from src.agents.drone import Drone, DroneRole


def cell_portrayal(agent: Cell):
    color = "#FFFFFF"  # Default white
    alpha = "70"

    if agent.burnt:
        color = "#000000"  # Black for burned
    elif agent.on_fire:
        color = "#FF0000"  # Red for fire
    else:
        # Color based on fuel level
        if agent.fuel_level == FuelLevel.LOW:
            color = "#D2B48C" + alpha  # Tan for no fuel
        elif agent.fuel_level == FuelLevel.MEDIUM:
            color = "#ADFF2F" + alpha  # Green-yellow for grass
        elif agent.fuel_level == FuelLevel.HIGH:
            color = "#006400" + alpha  # Dark green for forest

    return {
        "marker": "s",
        "color": color,
        "size": 11,
        "zorder": 1,

    }


def drone_base_portrayal(agent):
    return {
        "marker": "o",
        "color": "blue",
        "size": 200,
        "zorder": 2,
    }


def drone_portrayal(agent):
    if agent.role == DroneRole.CORDON:
        return {
            "marker": "o",
            "color": "purple",
            "size": 150,
            "zorder": 5,
        }
    return {
        "marker": "^",
        "color": "blue",
        "size": 150,
        "zorder": 10,
    }


def agent_portrayal(agent):
    if isinstance(agent, Cell):
        return cell_portrayal(agent)
    elif isinstance(agent, DroneBase):
        return drone_base_portrayal(agent)
    elif isinstance(agent, Drone):
        return drone_portrayal(agent)

    else:
        return {}
