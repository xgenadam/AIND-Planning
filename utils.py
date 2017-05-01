from aimacode.planning import Action
from aimacode.utils import expr


def load_factory(airport, plane, cargo):
    action = expr("Load({}, {}, {})".format(cargo, plane, airport))

    precond_pos = [
        expr("At({}, {})".format(cargo, airport)),
        expr("At({}, {})".format(plane, airport)),
        expr("Cargo({})".format(cargo)),
        expr("Plane({})".format(plane)),
        expr("Airport({})".format(airport))
    ]

    precond_neg = []

    effect_add = [
        expr("In({}, {})".format(cargo, plane))
    ]

    effect_rem = [
        expr("At({}, {})".format(cargo, airport))
    ]

    return Action(action=action,
                  precond=[precond_pos, precond_neg],
                  effect=[effect_add, effect_rem])

def unload_factory(airport, plane, cargo):
    pass