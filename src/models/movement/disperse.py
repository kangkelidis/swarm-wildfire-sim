from typing import TYPE_CHECKING

import numpy as np

from src.utils.logging_config import get_logger

if TYPE_CHECKING:
    from src.agents.drone import Drone

logger = get_logger()


def disperse(drone: 'Drone') -> np.array:
    """Disperse behaviour for drones.

    Args:
        drone (Drone): The drone to disperse.
    """

    random = drone.model.random

    desired_distance: int = int(drone.desired_distance) * 10

    # drones in communication range
    neighbours: list['Drone'] = drone.get_neighbours()


    movement_vector = np.array([random.uniform(-2, 2), random.uniform(-1, 3)])
    if not neighbours:
        logger.debug(f"Drone {drone.unique_id} has no neighbours")
        return movement_vector

    # If both the left and right leaders are equidistant then the forces will cancel out
    if not drone.left_leader:
        logger.debug(f"Drone {drone.unique_id} has no left leader")
        # select the first in the neighbours list that has no right leader
        # leave empty if not found (placed on the edge)
        leader = next((n for n in neighbours if n.pos[0] <= drone.pos[0] and not n.right_leader and n not in drone.neighbouring_leaders and drone not in n.neighbouring_leaders), None)
        logger.debug(f"Leader to assign: {leader.unique_id if leader else None}")
        if leader:
            drone.left_leader = leader
            leader.right_leader = drone
            drone.neighbouring_leaders.append(leader)
            leader.neighbouring_leaders.append(drone)

    if not drone.right_leader:
        logger.debug(f"Drone {drone.unique_id} has no right leader")
        leader = next((n for n in neighbours if n.pos[0] >= drone.pos[0] and not n.left_leader and n not in drone.neighbouring_leaders and drone not in n.neighbouring_leaders), None)
        logger.debug(f"Leader to assign: {leader.unique_id if leader else None}")
        if leader:
            drone.right_leader = leader
            leader.left_leader = drone
            drone.neighbouring_leaders.append(leader)
            leader.neighbouring_leaders.append(drone)

    if not drone.top_leader:
        logger.debug(f"Drone {drone.unique_id} has no top leader")
        leader = next((n for n in neighbours if n.pos[1] >= drone.pos[1] and not n.bottom_leader and n not in drone.neighbouring_leaders and drone not in n.neighbouring_leaders), None)
        logger.debug(f"Leader to assign: {leader.unique_id if leader else None}")
        if leader:
            drone.top_leader = leader
            leader.bottom_leader = drone
            drone.neighbouring_leaders.append(leader)
            leader.neighbouring_leaders.append(drone)

    if not drone.bottom_leader:
        logger.debug(f"Drone {drone.unique_id} has no bottom leader")
        leader = next((n for n in neighbours if n.pos[1] <= drone.pos[1] and not n.top_leader and n not in drone.neighbouring_leaders and drone not in n.neighbouring_leaders), None)
        logger.debug(f"Leader to assign: {leader.unique_id if leader else None}")
        if leader:
            drone.bottom_leader = leader
            leader.top_leader = drone
            drone.neighbouring_leaders.append(leader)
            leader.neighbouring_leaders.append(drone)

    if drone.left_leader:
        logger.debug(f"Drone {drone.unique_id} has left leader {drone.left_leader.unique_id}")
        movement_vector = apply_force(drone, drone.left_leader, movement_vector, desired_distance, horizontal=True)
    if drone.right_leader:
        logger.debug(f"Drone {drone.unique_id} has right leader {drone.right_leader.unique_id}")
        movement_vector = apply_force(drone, drone.right_leader, movement_vector, desired_distance, horizontal=True)
    if drone.top_leader:
        logger.debug(f"Drone {drone.unique_id} has top leader {drone.top_leader.unique_id}")
        movement_vector = apply_force(drone, drone.top_leader, movement_vector, desired_distance, horizontal=False)
    if drone.bottom_leader:
        logger.debug(f"Drone {drone.unique_id} has bottom leader {drone.bottom_leader.unique_id}")
        movement_vector = apply_force(drone, drone.bottom_leader, movement_vector, desired_distance, horizontal=False)

    return movement_vector


def apply_force(drone: 'Drone', leader: 'Drone', movement_vector: np.array, desired_distance: int, horizontal: bool) -> np.array:
    dx = _get_dx(drone, leader)
    dy = _get_dy(drone, leader)
    # dx must become desired distance
    # dy must become 0
    # the force is the difference between the current distance and the desired distance
    # must be stronger the further away it is
    # direction based on the sign of the difference
    # if the difference is positive, must move to the left (assuming desired distance is higher)
    if horizontal:
        f_x = dx - desired_distance if dx >= 0 else dx + desired_distance
        f_y = dy
    else:
        f_x = dx
        f_y = dy - desired_distance if dy >= 0 else dy + desired_distance

    force = np.array([f_x, f_y])
    movement_vector += force
    logger.debug(f"Drone {drone.unique_id} force: {force}")

    return movement_vector


def _get_dx(this, other):
    return other.pos[0] - this.pos[0]


def _get_dy(this, other):
    return other.pos[1] - this.pos[1]
