from aimacode.planning import Action
from aimacode.utils import expr

from lp_utils import FluentState

class ModifiedAction(Action):

    def is_valid(self, kb):
        for clause in self.precond_pos:
            if clause not in kb.clauses:
                return False

        for clause in self.precond_neg:
            if clause in kb.clauses:
                return False

        return True


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
        ]

        precond_neg = []

        effect_add = [
            cls.in_state(cargo, plane)
        ]

        effect_rem = [
            cls.at_state(cargo, airport)
        ]

        return cls.generate_action(action, precond_pos, precond_neg, effect_add, effect_rem)

    @classmethod
    def unload_action_factory(cls, airport, plane, cargo):
        action = expr("Unload({}, {}, {})".format(cargo, plane, airport))

        precond_pos = [
            cls.in_state(cargo, plane),
            cls.at_state(plane, airport),
        ]

        precond_neg = []

        effect_add = [
            cls.at_state(cargo, airport)
        ]

        effect_rem = [
            cls.in_state(cargo, plane)
        ]

        return cls.generate_action(action, precond_pos, precond_neg, effect_add, effect_rem)

    @classmethod
    def fly_action_factory(cls, plane, airport_from, airport_to):
        action = expr("Fly({}, {}, {})".format(plane, airport_from, airport_to))

        precond_pos = [
            cls.at_state(plane, airport_from),
        ]

        precond_neg = []

        effect_add = [
            cls.at_state(plane, airport_to)
        ]

        effect_rem = [
            cls.at_state(plane, airport_from)
        ]

        return cls.generate_action(action, precond_pos, precond_neg, effect_add, effect_rem)

    @staticmethod
    def generate_action(action, precond_pos, precond_neg, effect_add, effect_rem):
        return ModifiedAction(action=action,
                              precond=[precond_pos, precond_neg],
                              effect=[effect_add, effect_rem])

    @staticmethod
    def problem_factory(cargos, planes, airports, pos, goal):
        from my_air_cargo_problems import AirCargoProblem
        neg = []
        for cargo in cargos:
            for plane in planes:
                state = AirCargoFactory.in_state(cargo, plane)
                if state not in pos:
                    neg.append(state)

            for airport in airports:
                state = AirCargoFactory.at_state(cargo, airport)
                if state not in pos:
                    neg.append(state)

        for plane in planes:
            for airport in airports:
                state = AirCargoFactory.at_state(plane, airport)
                if state not in pos:
                    neg.append(state)

        init = FluentState(pos, neg)
        return AirCargoProblem(cargos, planes, airports, init, goal)