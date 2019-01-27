#!/usr/bin/env python3
# Python 3.6

# Import the Halite SDK, which will let you interact with the game.
import hlt

# This library contains constant values.
from hlt import constants

# This library contains direction metadata to better interface with the game.
from hlt.positionals import Direction, Position

# This library contains ship information
from hlt.entity import ShipStatus

# This library allows you to generate random numbers.
import random

import math
from collections import namedtuple

# Logging allows you to save messages for yourself. This is required because the regular STDOUT
#   (print statements) are reserved for the engine-bot communication.
import logging

""" <<<Game Begin>>> """

# This game object contains the initial game state.
game = hlt.Game(log_level=logging.INFO)
# At this point "game" variable is populated with initial map data.
# This is a good place to do computationally expensive start-up pre-processing.
logging.info(f"Game halite total amount: {game.game_map.halite_total}")

# As soon as you call "ready" function below, the 2 second per turn timer will start.
game.ready("HonirBot")

# Now that your bot is initialized, save a message to yourself in the log file with some important information.
#   Here, you log here your id, which you can always fetch from the game object by using my_id.
logging.info("Successfully created bot! My Player ID is {}.".format(game.my_id))

logging.debug(f"Player Shipyard: {game.me.shipyard}")

""" <<<Game Loop>>> """

def calc_halite_proportion(total, collected):
    return round(collected / total, 2)

def calc_move_cost(halite_amount):
    cost_ratio = 1 / constants.MOVE_COST_RATIO
    return math.floor(halite_amount * cost_ratio)

def calc_halite_collection(halite_amount):
    # this doesn't account for inspiration ratio currently
    collect_ratio = 1 / constants.EXTRACT_RATIO
    return math.ceil(halite_amount * collect_ratio)

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

    return priority[0]

HaliteCell = namedtuple('HaliteCell', ['position', 'halite_amount', 'distance', 'move_cost'])
EnemyCell = namedtuple('EnemyCell', ['position', 'id', 'halite_amount'])
FriendlyCell = namedtuple('FriendlyCell', ['position', 'id'])
StructureCell = namedtuple('StructureCell', ['position', 'structure_type'])

def radar_sweep(player_id, game_map, origin, sweep_distance=1):
    sweep = {
        'origin': None,
        'halite': [],
        'targets': [],
        'friendlies': [],
        'structures': []
    }

    sweep_range = range(-sweep_distance, sweep_distance+1)
    for y in sweep_range:
        for x in sweep_range:
            if x == 0 and y == 0:
                map_cell = game_map[origin]
            else:
                norm_x = (origin.x + x) % constants.WIDTH
                norm_y = (origin.y + y) % constants.HEIGHT
                map_cell = game_map[origin + Position(x, y, normalize=False)]

            distance = abs(x) + abs(y)  # how many cells will we have to move?

            if (x == 0 and y == 0):
                # origin map cell
                move_cost = calc_move_cost(map_cell.halite_amount)
                cell = HaliteCell(map_cell.position, map_cell.halite_amount, distance, move_cost)
                sweep['origin'] = cell
                sweep['halite'].append(cell)
            elif map_cell.is_empty:
                # halite map cell
                move_cost = calc_move_cost(map_cell.halite_amount)
                sweep['halite'].append(HaliteCell(map_cell.position, map_cell.halite_amount, distance, move_cost))
            elif map_cell.is_occupied:
                if map_cell.ship.owner != player_id:
                    # contains an enemy ship, so add ship cargo to location halite
                    target_halite = map_cell.halite_amount + map_cell.ship.halite_amount
                    sweep['targets'].append(EnemyCell(map_cell.position, map_cell.ship.id, target_halite))
                else:
                    # contains a friendly ship
                    sweep['friendlies'].append(FriendlyCell(map_cell.position, map_cell.ship.id))
            elif map_cell.has_structure:
                # contains a dropoff or shipyard
                sweep['structures'].append(StructureCell(map_cell.position, map_cell.structure_type))
            else:
                logging.warning(f"Radar sweep ran out of options for {map_cell}")

    return sweep

def get_closest_dropoff_move(game_map, ship, dropoff_positions):
    distances = []
    for dropoff in dropoff_positions:
        distance = game_map.calculate_distance(ship.position, dropoff)
        distances.append((distance, dropoff))

    distances = sorted(distances, key=lambda x: x[0])
    logging.debug(f"Distances: {distances}")

    closest_dropoff = distances[0]

    move = game_map.naive_navigate(ship, closest_dropoff[1])
    logging.info("Closest Dropoff: {} -> {}, {} units, move {}".format(
        ship.position,
        closest_dropoff[1],
        closest_dropoff[0],
        Direction.convert(move)
    ))
    if move == Direction.Still:
        logging.warning("This shouldn't happen, the nearest dropoff is current position?")

    return move

class CommandExecutor:
    def __init__(self):
        # A command queue holds all the commands you will run this turn. You build this list up and submit it at the
        #   end of the turn.
        self.command_queue = []

    def add_command(self, command):
        if isinstance(command, str):
            self.command_queue.append(command)
            return

        logging.exception(f"Command object not valid: {command}")

    def move_randomly(self, ship, move_cost):
        direction = random.choice([ Direction.North, Direction.South, Direction.East, Direction.West ])
        logging.info(f"Move Random: {ship.id}, {ship.position} -> {ship.position.directional_offset(direction)}, {move_cost} cost, {ship.status}, {Direction.convert(direction)}")
        self.add_command(ship.move(direction))

    def move_direction(self, ship, move_cost, direction):
        logging.info(f"Move Direction: {ship.id}, {ship.position} -> {ship.position.directional_offset(direction)}, {move_cost} cost, {ship.status}, {Direction.convert(direction)}")
        self.add_command(ship.move(direction))

    def hold_position(self, ship, collect_amount):
        logging.info(f"Hold Position: {ship.id}, {ship.position}, {collect_amount} collected, {ship.status}")
        self.add_command(ship.stay_still())


while True:
    # This loop handles each turn of the game. The game object changes every turn, and you refresh that state by
    #   running update_frame().
    game.update_frame()

    # You extract player metadata and the updated map metadata here for convenience.
    me = game.me
    game_map = game.game_map

    logging.info("Game halite remaining: {}, Player % of total: {}% ({})".format(
        game_map.halite_remaining,
        calc_halite_proportion(game_map.halite_total, me.halite_amount),
        me.halite_amount
    ))

    executor = CommandExecutor()

    dropoffs = [x.position for x in me.get_dropoffs()] + [me.shipyard.position]
    logging.info(f"Dropoffs: {dropoffs}")

    for ship in me.get_ships():
        # how much halite could we collect from current position if we remained
        origin_halite = game_map[ship.position].halite_amount
        origin_collection_halite = calc_halite_collection(origin_halite)
        cell_move_cost = calc_move_cost(origin_halite)

        logging.info(f"==== Ship {ship} ====")

        logging.info(f"Cell: {ship.position}, {origin_halite} amount, {origin_collection_halite} collectable, {cell_move_cost} move cost")

        if cell_move_cost > ship.halite_amount:
            # Ship can't move anywhere until gathered enough halite to move
            logging.info("Ship {} {} not enough halite to move: {} / {}".format(
                ship.id,
                ship.position,
                cell_move_cost,
                ship.halite_amount
            ))
            executor.hold_position(ship, origin_collection_halite)
            continue

        # determine whether to deliver cargo, continue mining or search for next mining spot

        if origin_collection_halite > ship.space_remaining:
            # Not enough space left to gather at current point, return to dropoff
            ship.status = ShipStatus.DELIVER

        if ship.position in dropoffs:
            # Ship has dropped off, needs to move back onto the grid
            ship.status = ShipStatus.GATHER

        if ship.status == ShipStatus.DELIVER:
            # move towards nearest dropoff point
            move = get_closest_dropoff_move(game_map, ship, dropoffs)
            next_position = ship.position.directional_offset(move)
            if next_position in dropoffs:
                logging.info("Ship depositing: {} halite".format(
                    ship.halite_amount - cell_move_cost
                ))

            executor.move_direction(ship, cell_move_cost, move)
            continue

        if ship.status == ShipStatus.GATHER:
            # sweep for next optimal position to move to
            sweep = radar_sweep(game.my_id, game_map, ship.position)
            score, track = get_optimal_halite_track(sweep)
            logging.info(f"Optimal track: {track}, score: {score}")
            if track.position == ship.position:
                # optimal collecting point is current position
                executor.hold_position(ship, origin_collection_halite)
            else:
                # move to next position
                move = game_map.naive_navigate(ship, track.position)
                if move == Direction.Still:
                    logging.warning(f"Optimal track didn't pick up on current position being best: {ship.id} {track}")
                executor.move_direction(ship, cell_move_cost, move)
            continue

        logging.warning("We shouldn't get here, as it means the ship doesn't know what to do")
        executor.move_randomly(ship, cell_move_cost)

    # If the game is in the first 200 turns and you have enough halite, spawn a ship.
    # Don't spawn a ship if you currently have a ship at port, though - the ships will collide.
    if game.turn_number <= 200 and me.halite_amount >= constants.SHIP_COST and not game_map[me.shipyard].is_occupied:
        executor.add_command(me.shipyard.spawn())

    # Send your moves back to the game environment, ending this turn.
    game.end_turn(executor.command_queue)

