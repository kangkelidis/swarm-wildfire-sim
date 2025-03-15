"""
Communication module for drones. This module is responsible for handling communication between drones.
"""

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

from src.agents.drone_modules.drone_enums import DroneRole
from src.utils.logging_config import get_logger

if TYPE_CHECKING:
    from src.agents.drone import Drone

logger = get_logger()


class MessageType(Enum):
    """Types of messages that drones can exchange."""
    FIRE_ALERT = "fire_alert"
    REGISTRATION = "registration"


@dataclass
class Message:
    """Message structure for drone communication."""
    type: MessageType
    sender: 'Drone'
    content: tuple[int, int]  # Fire position
    timestamp: int  # Simulation step when message was sent
    target_id: Optional[int] = None  # For direct messages
    position: Optional[tuple[int, int]] = None  # Sender's position when sent


class CommunicationModule:
    """Handles communication between drones using a mailbox pattern."""

    def __init__(self, drone: 'Drone'):
        self.drone = drone
        self.outgoing_buffer: list[Message] = []  # Messages to be sent at end of turn

    def broadcast(self):
        """Broadcast messages to all drones in range at end of turn."""
        if not self.outgoing_buffer:
            return

        # Get all drones in communication range
        recipients = self.drone.drones_in_range

        if not recipients:
            self.outgoing_buffer.clear()
            return

        # TODO: should be part of their knowledge
        # Determine valid recipients based on role
        if self.drone.role == DroneRole.LEADER:
            # Leaders broadcast to their followers and base
            valid_recipients = [
                r for r in recipients
                if r in self.drone.knowledge.followers or hasattr(r, 'is_base')
            ]
        elif self.drone.role == DroneRole.SCOUT:
            # Scouts broadcast to other scouts and their leader
            valid_recipients = [
                r for r in recipients
                if (r.role == DroneRole.SCOUT or r == self.drone.knowledge.leader)
            ]
        else:
            valid_recipients = recipients

        # Deliver messages to valid recipients
        current_time = self.drone.model.steps
        for message in self.outgoing_buffer:
            message.timestamp = current_time
            message.position = self.drone.pos

            for recipient in valid_recipients:
                if hasattr(recipient, 'knowledge'):
                    recipient.knowledge.mailbox.append(message)

        # Clear the outgoing buffer
        self.outgoing_buffer.clear()
        logger.debug(f"Drone {self.drone.unique_id} broadcasted messages to {len(valid_recipients)} recipients")

    def send_fire_alert(self, fire_pos: tuple[int, int]):
        """Send fire alert to all drones in range."""
        message = Message(
            type=MessageType.FIRE_ALERT,
            sender=self.drone,
            content=fire_pos,
            timestamp=self.drone.model.steps,
            position=self.drone.pos
        )
        self.outgoing_buffer.append(message)

    # form links to limit the network topology
    def send_registration(self, drones: list['Drone']):
        """Register with other drones in range."""
        message = Message(
            type=MessageType.REGISTRATION,
            sender=self.drone,
            content=None,
            timestamp=self.drone.model.steps,
            position=self.drone.pos
        )
        for drone in drones:
            drone.knowledge.mailbox.append(message)
