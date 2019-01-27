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

from engine.system import calc_halite_proportion
import executors

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
    
    # Initialise the strategy turn processor (logic engine)
    executor = executors.hlt_alpha.TurnProcessor(game)

    # Send your moves back to the game environment, ending this turn.
    game.end_turn(executor.run())
