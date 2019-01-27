import logging

from hlt.positionals import Direction

from engine.system import calc_halite_collection, calc_move_cost


def calc_collection_over_x_turns(halite_amount, num_turns=1):
    total = 0
    cell_amount = halite_amount

    for turn in range(num_turns):
        collected = calc_halite_collection(cell_amount)
        total += collected
        cell_amount -= collected

    return total


def estimate_collection_if_travel(origin_amount, target_amount, distance):
    target = calc_halite_collection(target_amount)

    # TODO: This is a fudge, we need to add up move cost of each cell passed through
    move_cost = distance * calc_move_cost(origin_amount)
    
    return target - move_cost


def get_optimal_halite_track(sweep):
    origin_halite = sweep['origin'].halite_amount

    def calc_move_stay_difference(cell):
        # Distance is how many cells to get there, +1 to gather when on target
        num_turns = cell.distance + 1
        remain_score = calc_collection_over_x_turns(origin_halite, num_turns)
        move_score = estimate_collection_if_travel(origin_halite, cell.halite_amount, cell.distance)
        return move_score - remain_score

    priority = sorted([(calc_move_stay_difference(cell), cell) for cell in sweep['halite']], key=lambda x: x[0], reverse=True)
    logging.debug(f"Sweep Halite Priority: {priority}")
    logging.info(f"Optimal track: {priority[0][1]}, score: {priority[0][0]}")

    return priority[0]


def get_closest_dropoff_move(game_map, ship, dropoff_positions):
    distances = []
    for dropoff in dropoff_positions:
        distance = game_map.calculate_distance(ship.position, dropoff)
        distances.append((distance, dropoff))

    distances = sorted(distances, key=lambda x: x[0])
    logging.debug(f"Distances: {distances}")

    closest_dropoff = distances[0]

    move = game_map.naive_navigate(ship, closest_dropoff[1])
    logging.info("Closest Dropoff: {} -> {}, distance {}, move {}".format(
        ship.position,
        closest_dropoff[1],
        closest_dropoff[0],
        Direction.convert(move)
    ))
    if move == Direction.Still:
        logging.warning("This shouldn't happen, the nearest dropoff is current position?")

    return move