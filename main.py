#!/usr/bin/env python3

import json
from sequencer import sequence
from housepy import util


user_ids = util.load("user_ids.pkl")
# user_ids = [1]  # me

sequences = sequence(user_ids)

util.save("sequences.pkl", sequences)