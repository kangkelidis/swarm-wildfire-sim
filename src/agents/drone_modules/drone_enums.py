from enum import StrEnum


class DroneRole(StrEnum):
    """
    Enum for drone roles.
    """
    LEADER = "leader"
    SCOUT = "scout"
    CORDON = "cordon"
    WALKER = "walker"


class DroneColors(StrEnum):
    """
    Enum for drone colors according to their role and state.
    """
    # LEADER = "#FFA500"  # orange
    # SCOUT = "#ff9aaa"   # pink
    # CORDON = "#800080"  # purple
    # WALKER = "#FFFF00"  # yellow

    LEADER = "#FFA500"  # orange
    SCOUT = "#0000FF"   # pink
    CORDON = "#800080"  # purple
    WALKER = "#FFFF00"  # yellow
