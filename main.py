#!/usr/bin/env python3

import json
import drawer
from sequencer import sequence
from housepy import util


# user_ids = util.load("data/user_ids.pkl")
# # user_ids = [1]  # me

# corpus = sequence(user_ids)

# util.save("data/corpus.pkl", corpus)


corpus = util.load("data/corpus_house.pkl")

d = 80
drawer.sequences([corpus[(d * 144):(d * 144) + 144]])