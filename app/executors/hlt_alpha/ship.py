import logging
from collections import namedtuple

from hlt.entity import ShipStatus
from hlt.positionals import Direction

from engine.system import calc_halite_collection, calc_move_cost
from engine.radar import radar_sweep

from .collection import get_closest_dropoff_move, get_optimal_halite_track


class OriginCell( namedtuple("Cell", ['position', 'total', 'collect', 'move_cost']) ):
    # https://stackoverflow.com/questions/7914152/can-i-overwrite-the-string-form-of-a-namedtuple
    __slots__ = ()

    def __repr__(self):
        return "Cell: {}, {} amount, {} collectable, {} move cost".format(
            self.position,
            self.total,
            self.collect,
            self.move_cost
        )


class ShipProcessor:
    def __init__(self, player_id, game_map, ship):
        self.player_id = player_id
        self.game_map = game_map
        self.ship = ship

        self.origin_cell = self._build_origin_cell(game_map, ship)

        logging.info(f"==== {self.ship} ====")
        logging.info(f"{self.origin_cell}")

    def _build_origin_cell(self, game_map, ship):
        # how much halite could we collect from current position if we remained
        home_halite_amount = game_map[ship.position].halite_amount
        
        return OriginCell(
            ship.position,
            home_halite_amount,
            calc_halite_collection(home_halite_amount),
            calc_move_cost(home_halite_amount)
        )

    def process(self, dropoffs):
        if not self.ship_can_move():
            return self.ship.stay_still()

        # determine whether to deliver cargo, continue mining or search for next mining spot

        self.check_cargo_capacity()
        self.check_if_dropoff_location(dropoffs)

        if self.ship.status == ShipStatus.DELIVER:
            # move towards nearest dropoff point
            return self.move_to_nearest_dropoff(dropoffs)

        if self.ship.status == ShipStatus.GATHER:
            sweep = radar_sweep(self.player_id, self.game_map, self.ship.position)
            return self.determine_optimal_action(sweep)

        logging.warning("We shouldn't get here, as it means the ship doesn't know what to do")
        return self.ship.move_randomly()

    def ship_can_move(self):
        if self.origin_cell.move_cost > self.ship.halite_amount:
            # Ship can't move anywhere until gathered enough halite to move
            logging.debug("Ship {} {} not enough halite to move: {} / {}".format(
                self.ship.id,
                self.ship.position,
                self.origin_cell.move_cost,
                self.ship.halite_amount
            ))
            return False

        return True

    def check_cargo_capacity(self):
        if self.origin_cell.collect > self.ship.space_remaining:
            # Not enough space left to gather at current point, return to dropoff
            self.ship.status = ShipStatus.DELIVER

    def check_if_dropoff_location(self, dropoffs):
        if self.ship.position in dropoffs:
            # Ship has dropped off, needs to move back onto the grid
            self.ship.status = ShipStatus.GATHER

    def move_to_nearest_dropoff(self, dropoffs):
        direction = get_closest_dropoff_move(self.game_map, self.ship, dropoffs)
        next_position = self.ship.position.directional_offset(direction)
        if next_position in dropoffs:
            logging.info("Ship depositing: {} halite".format(
                self.ship.halite_amount - self.origin_cell.move_cost
            ))
        return self.ship.move(direction)

    def determine_optimal_action(self, sweep):
        # calculate optimal track from radar sweep
        score, track = get_optimal_halite_track(sweep)

        if track.position == self.ship.position:
            # optimal collecting point is current position
            return self.ship.stay_still()

        # move to next position
        direction = self.game_map.naive_navigate(self.ship, track.position)
        if direction == Direction.Still:
            logging.warning(f"Optimal track didn't pick up on current position being best: {self.ship.id} {track}")
        return self.ship.move(direction)
