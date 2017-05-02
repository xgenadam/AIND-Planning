from aimacode.planning import Action
from aimacode.utils import expr


class AirCargoFactory(object):

    @staticmethod
    def at_state(plane_or_cargo, airport):
        return expr("At({}, {})".format(plane_or_cargo, airport))

    @staticmethod
    def cargo_state(cargo):
        return expr("Cargo({})".format(cargo))

    @staticmethod
    def plane_state(plane):
        return expr("Plane({})".format(plane))

    @staticmethod
    def airport_state(airport):
        return expr("Airport({})".format(airport))

    @staticmethod
    def in_state(cargo, plane):
        return expr("In({}, {})".format(cargo, plane))

    @staticmethod
    def core_states(airport, plane, cargo):
        return [
            AirCargoFactory.airport_state(airport),
            AirCargoFactory.plane_state(plane),
            AirCargoFactory.cargo_state(cargo)
        ]

    @classmethod
    def load_action_factory(cls, airport, plane, cargo):
        action = expr("Load({}, {}, {})".format(cargo, plane, airport))

        precond_pos = [
            cls.at_state(cargo, airport),
            cls.at_state(plane, airport),
            *cls.core_states(airport, plane, cargo)
        ]

        precond_neg = []

        effect_add = [
            cls.in_state(cargo, plane)
        ]

        effect_rem = [
            cls.at_state(cargo, airport)
        ]

        return Action(action=action,
                      precond=[precond_pos, precond_neg],
                      effect=[effect_add, effect_rem])

    @classmethod
    def unload_action_factory(cls, airport, plane, cargo):
        action = expr("Unload({}, {}, {})".format(cargo, plane, airport))

        precond_pos = [
            cls.in_state(cargo, plane),
            cls.at_state(plane, airport),
            *cls.core_states(airport, plane, cargo)
        ]

        precond_neg = []

        effect_add = [
            cls.at_state(cargo, airport)
        ]

        effect_rem = [
            cls.in_state(cargo, plane)
        ]

        return Action(action=action,
                      precond=[precond_pos, precond_neg],
                      effect=[effect_add, effect_rem])

    @classmethod
    def fly_action_factory(cls, plane, airport_from, airport_to):
        action = expr("Fly({}, {}, {})".format(plane, airport_from, airport_to))

        precond_pos = [
            cls.at_state(plane, airport_from),
            cls.plane_state(plane),
            cls.airport_state(airport_from),
            cls.airport_state(airport_to)
        ]

        precond_neg = []

        effect_add = [
            cls.at_state(plane, airport_to)
        ]

        effect_rem = [
            cls.at_state(plane, airport_from)
        ]

        return Action(action=action,
                      precond=[precond_pos, precond_neg],
                      effect=[effect_add, effect_rem])