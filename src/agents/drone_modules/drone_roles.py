from enum import StrEnum


class DroneRole(StrEnum):
    """
    Enum for drone roles.
    """
    LEADER = "leader"
    SCOUT = "scout"
    CORDON = "cordon"
    WALKER = "walker"
