import logging

from hlt import constants

from .ship import ShipProcessor


class TurnProcessor:
    def __init__(self, game):
        self.game = game
        self.me = game.me
        self.game_map = game.game_map

        self.command_queue = []

    def add_command(self, command):
        # TODO: We should have some error checking logic here
        self.command_queue.append(command)

    def pre_execute(self):
        self.dropoffs = [x.position for x in self.me.get_dropoffs()] + [self.me.shipyard.position]
        logging.info(f"Dropoffs: {self.dropoffs}")

    def run(self):
        self.pre_execute()

        for ship in self.me.get_ships():
            processor = ShipProcessor(ship.owner, self.game_map, ship)
            self.add_command(processor.process(self.dropoffs))

        self.post_execute()

        return self.command_queue

    def post_execute(self):
        if len(self.me.get_ships()) < 1:
            self.add_command(self.me.shipyard.spawn())

        return

        # If the game is in the first 200 turns and you have enough halite, spawn a ship.
        # Don't spawn a ship if you currently have a ship at port, though - the ships will collide.
        if self.game.turn_number <= 200 \
            and self.me.halite_amount >= constants.SHIP_COST \
            and not self.game_map[self.me.shipyard].is_occupied:
            self.add_command(self.me.shipyard.spawn())
