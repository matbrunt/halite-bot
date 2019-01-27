import logging
import random

from hlt.positionals import Direction


class CommandExecutor:
    def __init__(self):
        # A command queue holds all the commands you will run this turn.
        # You build this list up and submit it at the end of the turn.
        self.command_queue = []

    def add_command(self, command):
        if isinstance(command, str):
            self.command_queue.append(command)
            return

        logging.exception(f"Command object not valid: {command}")

    def move_randomly(self, ship):
        direction = random.choice([ Direction.North, Direction.South, Direction.East, Direction.West ])
        logging.info(f"Move Random: {ship.id}, {ship.position} -> {ship.position.directional_offset(direction)}, {ship.status}, {Direction.convert(direction)}")
        self.add_command(ship.move(direction))

    def move_direction(self, ship, direction):
        logging.info(f"Move Direction: {ship.id}, {ship.position} -> {ship.position.directional_offset(direction)}, {ship.status}, {Direction.convert(direction)}")
        self.add_command(ship.move(direction))

    def hold_position(self, ship):
        logging.info(f"Hold Position: {ship.id}, {ship.position}, {ship.status}")
        self.add_command(ship.stay_still())
