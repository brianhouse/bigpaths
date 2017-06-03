#!/usr/bin/env python3

import json
import drawer
from sequencer import sequence
from housepy import util


# user_ids = util.load("data/user_ids.pkl")
# # user_ids = [1]  # me

sequences = sequence(user_ids)

log.info("Flattening...")
corpus = []
for sequence in sequences:
    for point in sequence:
        corpus.append((point.x, point.y))
log.info("--> done")        


# util.save("data/corpus.pkl", corpus)


# corpus = util.load("data/corpus_house.pkl")

# d = 80
# drawer.sequences([corpus[(d * 144):(d * 144) + 144]])