#!/bin/sh

./halite --replay-directory replays/ -vvv --no-timeout --seed 1548505975 --width 32 --height 32 "python3 HonirBot.py" "python3 MyBot.py"

# ./halite --replay-directory replays/ -vvv --no-timeout --no-replay --no-logs --turn-limit 10 --seed 1548505975 --width 32 --height 32 "python3 HonirBot.py" "python3 MyBot.py"
