Shipyard cell reports 0 halite_amount.

Turn 1 starts with no ships, you generate them at end of turn 1, so you have one ship ready at turn 2.

Looks like we round up amount collectible on each turn, rounded value goes into hold, and is removed from map cell.

Looks like move cost is rounded down from cell halite amount.

Move cost is paid by ship cargo, so ship stays still and gathers halite even if given a move command, if it does not have enough cargo to leave the cell.