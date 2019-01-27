import logging
import math

from hlt import constants


def calc_halite_proportion(total, collected):
    return round(collected / total, 2)

def calc_move_cost(halite_amount):
    cost_ratio = 1 / constants.MOVE_COST_RATIO
    return math.floor(halite_amount * cost_ratio)

def calc_halite_collection(halite_amount):
    # this doesn't account for inspiration ratio currently
    collect_ratio = 1 / constants.EXTRACT_RATIO
    return math.ceil(halite_amount * collect_ratio)
