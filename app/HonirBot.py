#!/usr/bin/env python3
# Python 3.6

# Import the Halite SDK, which will let you interact with the game.
import hlt

# This library contains constant values.
from hlt import constants

# This library contains direction metadata to better interface with the game.
from hlt.positionals import Direction

# This library contains ship information
from hlt.entity import ShipStatus

# Logging allows you to save messages for yourself.
# This is required because the regular STDOUT (print statements) are reserved for the engine-bot communication.
import logging

from engine.system import calc_halite_collection, calc_move_cost, calc_halite_proportion
from engine.executor import CommandExecutor
from engine.radar import radar_sweep
from strategy.collection import get_optimal_halite_track, get_closest_dropoff_move

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
            logging.debug("Ship {} {} not enough halite to move: {} / {}".format(
                ship.id,
                ship.position,
                cell_move_cost,
                ship.halite_amount
            ))
            executor.hold_position(ship)
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

            executor.move_direction(ship, move)
            continue

        if ship.status == ShipStatus.GATHER:
            # sweep for next optimal position to move to
            sweep = radar_sweep(game.my_id, game_map, ship.position)
            score, track = get_optimal_halite_track(sweep)
            if track.position == ship.position:
                # optimal collecting point is current position
                executor.hold_position(ship)
            else:
                # move to next position
                move = game_map.naive_navigate(ship, track.position)
                if move == Direction.Still:
                    logging.warning(f"Optimal track didn't pick up on current position being best: {ship.id} {track}")
                executor.move_direction(ship, move)
            continue

        logging.warning("We shouldn't get here, as it means the ship doesn't know what to do")
        executor.move_randomly(ship)

    # If the game is in the first 200 turns and you have enough halite, spawn a ship.
    # Don't spawn a ship if you currently have a ship at port, though - the ships will collide.
    if game.turn_number <= 200 and me.halite_amount >= constants.SHIP_COST and not game_map[me.shipyard].is_occupied:
        executor.add_command(me.shipyard.spawn())

    # Send your moves back to the game environment, ending this turn.
    game.end_turn(executor.command_queue)

