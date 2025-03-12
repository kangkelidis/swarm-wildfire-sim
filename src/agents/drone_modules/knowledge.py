class DroneKnowledge:
    """
    Class to store the knowledge of a drone agent.

    """
    def __init__(self):
        self.base_pos = None
        self.neighbours = []
        self.same_cell_drones = []
        self.closest_neighbour = None
        self.distance_to_closest_neighbour = None
        self.diff_cell_neighbours = []

        self.followers = []
        self.leader = None
        self.peers = []
