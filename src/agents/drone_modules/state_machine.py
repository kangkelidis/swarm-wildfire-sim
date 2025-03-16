from typing import TYPE_CHECKING

from statemachine import Event, State, StateMachine
from statemachine.contrib.diagram import DotGraphMachine

from src.agents.drone_modules.drone_enums import DroneRole

if TYPE_CHECKING:
    from src.agents.drone import Drone


class DroneBehaviour(StateMachine):
    idle = State('Idle', initial=True)
    dispersing = State('Dispersing')
    formation = State('Formation')
    hovering_leader = State('Hovering_leader')
    patrolling = State('Patrolling')
    cordoning = State('Cordoning')
    return_to_base = State('Return_to_base')
    recharging = State('Recharging')

    stop_dispersing = Event(name='Stop dispersing')
    aligned = Event(name='Aligned')
    broke_formation = Event(name='Broke formation')

    # events
    deploy = (
        idle.to(dispersing, cond='is_crowded')
        | idle.to(formation, cond='is_leader')
        | idle.to(patrolling, cond='is_scout')
        | dispersing.to(
            formation,
            cond='is_leader and not is_crowded',
            event="stop_dispersing",
        )
        | dispersing.to(patrolling, cond='is_scout')
        | dispersing.to.itself()
        | formation.to(hovering_leader, cond='is_leader and is_in_formation')
        | formation.to.itself()
        | hovering_leader.to(formation, cond='is_leader and not is_in_formation')
        | hovering_leader.to(dispersing, cond='is_crowded')
        | hovering_leader.to.itself()
        | patrolling.to.itself()
    )

    fire_detected = patrolling.to(cordoning) | cordoning.to.itself()

    need_to_return = (
        dispersing.to(return_to_base) |
        patrolling.to(return_to_base) |
        cordoning.to(return_to_base) |
        hovering_leader.to(return_to_base) |
        formation.to(return_to_base) |
        return_to_base.to(recharging, cond='is_at_base') |
        return_to_base.to.itself())

    recharge = (recharging.to(idle, cond='is_fully_recharged') |
                recharging.to.itself())

    turn_to_scout = hovering_leader.to(patrolling) | formation.to(patrolling)
    turn_to_leader = patrolling.to(formation) | cordoning.to(formation)

    def is_at_base(self):
        drone: 'Drone' = self.model
        return drone.knowledge.base_pos == drone.pos

    def is_fully_recharged(self):
        drone: 'Drone' = self.model
        return drone.battery.is_fully_charged()

    def is_crowded(self):
        drone: 'Drone' = self.model
        return len(drone.same_cell_drones) > 0

    def is_leader(self):
        drone: 'Drone' = self.model
        return drone.role == DroneRole.LEADER

    def is_scout(self):
        drone: 'Drone' = self.model
        return drone.role == DroneRole.SCOUT

    def is_in_formation(self):
        drone: 'Drone' = self.model
        return drone.navigation.is_in_formation()

    def on_enter_deploy(self):
        drone: 'Drone' = self.model
        highest_leader_score = max([drone.leader_score() for drone in drone.neighbours])
        if drone.leader_score() < highest_leader_score:
            drone.role = DroneRole.SCOUT
        elif drone.leader_score() > highest_leader_score:
            drone.role = DroneRole.LEADER

    def on_enter_dispersing(self):
        drone: 'Drone' = self.model
        drone.navigation.disperse()

    def on_enter_formation(self):
        drone: 'Drone' = self.model
        drone.navigation.formation()

    def on_enter_patrolling(self):
        drone: 'Drone' = self.model
        drone.navigation.random_walk()

    def on_enter_return_to_base(self):
        drone: 'Drone' = self.model
        drone.navigation.move_towards(drone.knowledge.base_pos)

    def on_enter_recharging(self):
        drone: 'Drone' = self.model
        drone.battery.recharge()

    def on_transition(self, event):
        drone: 'Drone' = self.model
        drone.drone_logger.debug(f"Drone is transitioning to {self.current_state}, triggered by {event}")

    def print_state_diagram(self):
        graph = DotGraphMachine(self)
        dot = graph()
        dot.write_png("drone_state_machine.png")
