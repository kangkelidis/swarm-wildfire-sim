"""
Drone knowledge module.

This module is responsible for storing the knowledge of a drone agent.
It simulates the drone's knowledge repository during the simulation.
"""

import warnings
from typing import TYPE_CHECKING, Any, NamedTuple, Optional

import networkx as nx
from matplotlib import pyplot as plt

from src.agents.drone_modules.communication import Message
from src.agents.drone_modules.drone_enums import DroneRole
from src.agents.drone_modules.navigation import chebyshev_distance

if TYPE_CHECKING:
    from src.agents.base import DroneBase
    from src.agents.drone import Drone


class ClosestNeighbour(NamedTuple):
    drone: Optional['Drone'] = None
    distance: Optional[int] = None


class Network:
    # All they agents the drone can communicate with, a subset of the drones_in_range

    def __init__(self, drone: 'Drone'):
        self.drone = drone
        self.graph = nx.Graph()
        self.graph.add_node(drone)

        # The drones that follow this leader drone
        self.followers: set['Drone'] = set()
        # Other drones this drone can communicate with that are at the same hierarchical level
        self.peers: set['Drone'] = set()
        # The leader drone this drone follows
        self.leader: Optional['Drone'] = None
        self.base: Optional['DroneBase'] = None

    def add(self, drone: 'Drone'):
        self.graph.add_node(drone)

        if self.is_peer(drone):
            self.peers.add(drone)
            self.graph.add_edge(self.drone, drone, relation='peer')
        elif self.drone.role == DroneRole.LEADER:
            # This drone is a leader, so the other drone is a follower
            self.followers.add(drone)
            self.graph.add_edge(self.drone, drone, relation='follower')
        else:
            # This drone is a follower, so the other drone is a leader
            self.leader = drone
            self.graph.add_edge(self.drone, drone, relation='leader')

    def remove(self, drone: 'Drone'):
        try:
            if drone in self.graph:
                self.graph.remove_node(drone)
        except nx.NetworkXError:
            warnings.warn(f"Drone {drone} not found in graph.")

        if drone in self.peers:
            self.peers.remove(drone)
        elif drone in self.followers:
            self.followers.remove(drone)
        elif self.leader == drone:
            self.leader = None
        else:
            warnings.warn(f"Drone {drone} not found in network.")

    def add_base(self, base: 'DroneBase'):
        self.base = base

    def is_peer(self, drone: 'Drone'):
        both_leaders = self.drone.role == DroneRole.LEADER and drone.role == DroneRole.LEADER
        both_followers = self.drone.role != DroneRole.LEADER and drone.role != DroneRole.LEADER
        return both_leaders or both_followers

    def get_links(self) -> set['Drone']:
        return self.followers.union(self.peers)

    def __repr__(self):
        return f"Network(followers={self.followers}, peers={self.peers}, leader={self.leader}, base={self.base})"

    # TODO: change or remove
    def draw(self):
        """Draw the network graph with custom colors and styles."""
        # Create position layout for nodes
        pos = nx.spring_layout(self.graph)

        # Draw nodes with different colors based on role
        # Current drone
        nx.draw_networkx_nodes(self.graph, pos,
                               nodelist=[self.drone],
                               node_color='green',
                               node_size=500)

        # Leader drones
        leaders = [n for n in self.graph.nodes() if n != self.drone and n.role == DroneRole.LEADER]
        nx.draw_networkx_nodes(self.graph, pos,
                               nodelist=leaders,
                               node_color='orange',
                               node_size=300)

        # Follower drones
        followers = [n for n in self.graph.nodes() if n != self.drone and n.role != DroneRole.LEADER]
        nx.draw_networkx_nodes(self.graph, pos,
                               nodelist=followers,
                               node_color='blue',
                               node_size=300)

        # Draw edges with different styles based on relationship
        # Leader connections (solid bold)
        leader_edges = [(u, v) for (u, v, d) in self.graph.edges(data=True) if d['relation'] == 'leader']
        nx.draw_networkx_edges(self.graph, pos,
                               edgelist=leader_edges,
                               width=2.0,
                               edge_color='black')

        # Peer connections (solid normal)
        peer_edges = [(u, v) for (u, v, d) in self.graph.edges(data=True) if d['relation'] == 'peer']
        nx.draw_networkx_edges(self.graph, pos,
                               edgelist=peer_edges,
                               width=1.0,
                               edge_color='black')

        # Follower connections (dotted)
        follower_edges = [(u, v) for (u, v, d) in self.graph.edges(data=True) if d['relation'] == 'follower']
        nx.draw_networkx_edges(self.graph, pos,
                               edgelist=follower_edges,
                               width=0.5,
                               edge_color='grey',
                               style='dotted')

        # Add labels
        labels = {node: f"D{node.unique_id}" for node in self.graph.nodes()}
        nx.draw_networkx_labels(self.graph, pos, labels)

        plt.title(f"Drone {self.drone.unique_id} Network")
        plt.axis('off')
        plt.savefig('out/debug_drone_network_graph.png')
        plt.close()


class DroneKnowledge:
    """
    Class to store the knowledge of a drone agent. Simulated the drone's knowledge repository.
    Knowledge is dynamic, the drone's knowledge changes. It should not have information relating to the simulation,
    these should be part of the drone class.

    """
    def __init__(self, drone: 'Drone'):
        self.drone = drone
        self.base_pos: tuple[int, int] = None

        self._closest_neighbour = ClosestNeighbour()
        self._closest_leader = ClosestNeighbour()

        self.network = Network(self.drone)

        # Communication-related knowledge
        self.mailbox: list[Message] = []  # Incoming messages
        self.reported_fires: set[tuple[int, int]] = set()  # Fire positions reported by other drones

    @property
    def links(self):
        return self._links

    @links.setter
    def links(self, value):
        self._links = value

    @property
    def closest_neighbour(self) -> Optional['Drone']:
        return self._closest_neighbour.drone

    def get_distance_to_closest_neighbour(self):
        return self._closest_neighbour.distance

    @closest_neighbour.setter
    def closest_neighbour(self, drone: Optional['Drone']):
        if drone is None:
            self._closest_neighbour = ClosestNeighbour()
            return

        distance = chebyshev_distance(self.drone.pos, drone.pos)
        self._closest_neighbour = ClosestNeighbour(drone, distance)
        # Update the closest leader too
        if drone.role == DroneRole.LEADER:
            self.closest_leader = drone

    @property
    def closest_leader(self) -> Optional['Drone']:
        return self._closest_leader.drone

    def get_distance_to_closest_leader(self) -> Optional[int]:
        return self._closest_leader.distance

    @closest_leader.setter
    def closest_leader(self, drone: Optional['Drone']):
        if drone is None:
            self._closest_leader = ClosestNeighbour()
            return

        distance = chebyshev_distance(self.drone.pos, drone.pos)
        self._closest_leader = ClosestNeighbour(drone, distance)
