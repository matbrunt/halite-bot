**Maximise Collection**

If a ship stays still, it collects 25% of halite available in the cell, rounded up to the nearest whole number. Ships can carry up to 1000 halite.

So at a new turn, if the amount of halite to be collected is less than the space remaining on the ship, change status to 'rtb' and start moving to the nearest shipyard.

If collect amount is less than move amount of next cell, then move on rather than stay still.

*Alternative: could also have a parameter saying RTB when ship is X% full.*

---
**End Turn: Crash Ships**
On each turn, calculate how many moves required to get back to nearest shipyard.

If this is the same number of turns remaining to the end game limit (400 or 500), then start moving the ship back to the shipyard.

Intention is to collide all the ships into the shipyard on the final turn to more rapidly deposit their halite into the player account.

---
**Opponent Disposition**

Loop over all `game.players` at game start, filtering out my id, to query the strength and disposition of the players.

Use this data to find the location of enemy ships, and the halite amounts they hold (for aggressive play, could look at sinking their ship).

Ships have an `owner`, `id`, `position` and `halite_amount`.

---
**Shipyard Construction**

How do we determine where to build a shipyard?

- It wants to be nearest to the high yield halite deposits to make it worthwhile?
- Or halfway between existing shipyard and deposits, to minimise the return cost of ships?

---
**Aggressive Posture**

Tunable parameter for either:
- max num of assault ships, e.g. 4
- proportion of total ships to use for assault, e.g. 0.2

Mark these ships as attack ships, their purpose is to intentionally collide with max halite opponent ships.

Shadow attack ships with collection ships, to recover the dropped halite following collision.

- Dedicated attack ships, or repurpose ships in the area if a opportunistic target appears?
- If no viable halite in surrounding area, but viable enemy ships, change posture to attack