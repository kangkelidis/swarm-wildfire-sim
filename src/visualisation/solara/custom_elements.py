from src.agents import Cell, Drone, DroneBase, FuelLevel


def cell_portrayal(agent: Cell):
    color = "#FFFFFF"  # Default white
    alpha = "20"

    if agent.burnt:
        color = "#000000"  # Black for burned
    elif agent.on_fire:
        color = "#FF0000"  # Red for fire
    elif agent.is_road:
        color = "#808080"
    else:
        # Color based on fuel level
        if agent.fuel_level == FuelLevel.LOW:
            color = "#D2B48C" + alpha  # Tan for no fuel
        elif agent.fuel_level == FuelLevel.MEDIUM:
            color = "#ADFF2F" + alpha  # Green-yellow for grass
        elif agent.fuel_level == FuelLevel.HIGH:
            color = "#006400" + alpha  # Dark green for forest
    # color = "#FFFFFF"  # Default white
    return {
        "marker": "s",
        "color": color,
        "size": 11,
        "zorder": 1,
    }


def drone_base_portrayal(agent):
    return {
        "marker": "H",
        "color": "grey",
        "size": 200,
        "zorder": 2,
    }


def drone_portrayal(drone: Drone):
    marker = "o"
    color = "black"
    size = 10
    zorder = 10


    if drone.debug:
        marker = "^"
        size = 100

    return {
        "marker": marker,
        "color": color,
        "size": size,
        "zorder": zorder,
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
