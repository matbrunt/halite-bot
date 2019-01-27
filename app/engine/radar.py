import logging
from collections import namedtuple

from hlt import constants
from hlt.positionals import Position

from engine.system import calc_move_cost


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
