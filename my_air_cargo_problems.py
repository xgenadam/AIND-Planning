from aimacode.logic import PropKB
from aimacode.planning import Action
from aimacode.search import (
    Node, Problem,
)
from aimacode.search import greedy_best_first_graph_search
from aimacode.utils import expr
from lp_utils import (
    FluentState, encode_state, decode_state,
)
from my_planning_graph import PlanningGraph

from functools import lru_cache


class AirCargoProblem(Problem):
    def __init__(self, cargos, planes, airports, initial: FluentState, goal: list):
        """

        :param cargos: list of str
            cargos in the problem
        :param planes: list of str
            planes in the problem
        :param airports: list of str
            airports in the problem
        :param initial: FluentState object
            positive and negative literal fluents (as expr) describing initial state
        :param goal: list of expr
            literal fluents required for goal test
        """
        self.state_map = initial.pos + initial.neg
        self.initial_state_TF = encode_state(initial, self.state_map)
        Problem.__init__(self, self.initial_state_TF, goal=goal)
        self.cargos = cargos
        self.planes = planes
        self.airports = airports
        self.actions_list = self.get_actions()

    def get_actions(self):
        """
        This method creates concrete actions (no variables) for all actions in the problem
        domain action schema and turns them into complete Action objects as defined in the
        aimacode.planning module. It is computationally expensive to call this method directly;
        however, it is called in the constructor and the results cached in the `actions_list` property.

        Returns:
        ----------
        list<Action>
            list of Action objects
        """

        # create concrete Action objects based on the domain action schema for: Load, Unload, and Fly
        # concrete actions definition: specific literal action that does not include variables as with the schema
        # for example, the action schema 'Load(c, p, a)' can represent the concrete actions 'Load(C1, P1, SFO)'
        # or 'Load(C2, P2, JFK)'.  The actions for the planning problem must be concrete because the problems in
        # forward search and Planning Graphs must use Propositional Logic

        def load_actions():
            """Create all concrete Load actions and return a list

            :return: list of Action objects
            """
            loads = []
            for airport in self.airports:
                for plane in self.planes:
                    for cargo in self.cargos:
                        loads.append(
                            AirCargoFactory.load_action_factory(
                                airport,
                                plane,
                                cargo)
                        )
            return loads

        def unload_actions():
            """Create all concrete Unload actions and return a list

            :return: list of Action objects
            """
            unloads = []
            for airport in self.airports:
                for plane in self.planes:
                    for cargo in self.cargos:
                        unloads.append(
                            AirCargoFactory.unload_action_factory(
                                airport,
                                plane,
                                cargo)
                        )
            return unloads

        def fly_actions():
            """Create all concrete Fly actions and return a list

            :return: list of Action objects
            """
            flys = []
            for airport_from in self.airports:
                for airport_to in self.airports:
                    if airport_from != airport_to:
                        for plane in self.planes:
                            flys.append(
                                AirCargoFactory.fly_action_factory(
                                    plane,
                                    airport_from,
                                    airport_to
                                )
                            )

            return flys

        return load_actions() + unload_actions() + fly_actions()

    def actions(self, state: str) -> list:
        """ Return the actions that can be executed in the given state.

        :param state: str
            state represented as T/F string of mapped fluents (state variables)
            e.g. 'FTTTFF'
        :return: list of Action objects
        """
        possible_actions = []

        kb = self.get_kb(state)

        for action in self.actions_list:
            if action.is_valid(kb) is True:
                possible_actions.append(action)
        return possible_actions

    def result(self, fluent: str, action: Action):
        """ Return the state that results from executing the given
        action in the given state. The action must be one of
        self.actions(state).BF

        :param fluent: state entering node
        :param action: Action applied
        :return: resulting state after action
        """
        current_state = decode_state(fluent, self.state_map)
        pos_list = []
        neg_list = []

        for fluent in current_state.pos:
            if fluent not in action.effect_rem:
                pos_list.append(fluent)

        for fluent in current_state.neg:
            if fluent not in action.effect_add:
                neg_list.append(fluent)

        pos_list = list(set(pos_list + action.effect_add))
        neg_list = list(set(neg_list + action.effect_rem))

        new_state = FluentState(pos_list, neg_list)
        return encode_state(new_state, self.state_map)

    def goal_test(self, state: str) -> bool:
        """ Test the state to see if goal is reached

        :param state: str representing state
        :return: bool
        """
        kb = PropKB()
        kb.tell(decode_state(state, self.state_map).pos_sentence())
        for clause in self.goal:
            if clause not in kb.clauses:
                return False
        return True

    def h_1(self, node: Node):
        # note that this is not a true heuristic
        h_const = 1
        return h_const

    @lru_cache(maxsize=8192)
    def h_pg_levelsum(self, node: Node):
        """This heuristic uses a planning graph representation of the problem
        state space to estimate the sum of all actions that must be carried
        out from the current state in order to satisfy each individual goal
        condition.
        """
        # requires implemented PlanningGraph class
        pg = PlanningGraph(self, node.state)
        pg_levelsum = pg.h_levelsum()
        return pg_levelsum

    @lru_cache(maxsize=8192)
    def h_ignore_preconditions(self, node: Node) -> int:
        """This heuristic estimates the minimum number of actions that must be
        carried out from the current state in order to satisfy all of the goal
        conditions by ignoring the preconditions required for an action to be
        executed.
        """
        count = 0
        # similar to goal test here, but rather than returning false when a goal is not satisfied
        # we count the number of unsatisfied goals

        kb = self.get_kb(node.state)
        for clause in self.goal:
            if clause not in kb.clauses:
                count += 1

        return count

    def get_kb(self, state):
        kb = PropKB()
        kb.tell(decode_state(state, self.state_map).pos_sentence())

        return kb


def air_cargo_p1() -> AirCargoProblem:
    cargos = ['C1', 'C2']
    planes = ['P1', 'P2']
    airports = ['JFK', 'SFO']
    pos = [expr('At(C1, SFO)'),
           expr('At(C2, JFK)'),
           expr('At(P1, SFO)'),
           expr('At(P2, JFK)'),
           ]
    neg = [expr('At(C2, SFO)'),
           expr('In(C2, P1)'),
           expr('In(C2, P2)'),
           expr('At(C1, JFK)'),
           expr('In(C1, P1)'),
           expr('In(C1, P2)'),
           expr('At(P1, JFK)'),
           expr('At(P2, SFO)'),
           ]
    init = FluentState(pos, neg)
    goal = [expr('At(C1, JFK)'),
            expr('At(C2, SFO)'),
            ]
    return AirCargoProblem(cargos, planes, airports, init, goal)


def air_cargo_p2() -> AirCargoProblem:
    cargos = ['C1', 'C2', 'C3']
    planes = ['P1', 'P2', 'P3']
    airports = ['JFK', 'SFO', 'ATL']
    pos = [expr('At(C1, SFO)'),
           expr('At(C2, JFK)'),
           expr('At(C3, ATL)'),
           expr('At(P1, SFO)'),
           expr('At(P2, JFK)'),
           expr('At(P3, ATL)')]

    goal = [expr('At(C1, JFK)'),
            expr('At(C2, SFO)'),
            expr('At(C3, SFO)')]
    return AirCargoFactory.problem_factory(cargos, planes, airports, pos, goal)


def air_cargo_p3() -> AirCargoProblem:
    cargos = ['C1', 'C2', 'C3', 'C4']
    planes = ['P1', 'P2']
    airports = ['JFK', 'SFO', 'ATL', 'ORD']
    pos = [expr('At(C1, SFO)'),
           expr('At(C2, JFK)'),
           expr('At(C3, ATL)'),
           expr('At(C4, ORD)'),
           expr('At(P1, SFO)'),
           expr('At(P2, JFK)')]

    goal = [expr('At(C1, JFK)'),
            expr('At(C2, SFO)'),
            expr('At(C3, JFK)'),
            expr('At(C4, SFO)')]

    return AirCargoFactory.problem_factory(cargos, planes, airports, pos, goal)


"""
UTILS   
"""

from aimacode.planning import Action
from aimacode.utils import expr

from lp_utils import FluentState


class ConcreteAction(Action):

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
        return ConcreteAction(action=action,
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