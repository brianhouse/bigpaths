#!/usr/bin/env python3

import json
import drawer
from sequencer import sequence
from housepy import util, config, log, geo
from data import *


# user_ids = util.load("data/user_ids.pkl")
user_ids = [1]  # me

sequences = sequence(user_ids)

# make hash data
hashes = [point.hash for sequence in sequences for point in sequence]
hashes = list(set(hashes))
hashes.sort()
for hash in hashes:
    print(hash)
print(len(hashes))
util.save("data/hashes.pkl", hashes)

for sequence in sequences:
    for point in sequence:
        point.cluster = hashes.index(point.hash)

log.info("Flattening...")
corpus = [point.cluster for sequence in sequences for point in sequence]
log.info("--> done")        

util.save("data/corpus_house_hash.pkl", corpus)



# test sequence drawing
d = 80
sequence = corpus[(d * 144):(d * 144) + 144]
for p, cluster in enumerate(sequence):
    point = Point(*geo.geohash_decode(hashes[cluster]), None)
    sequence[p] = point.x, point.y
drawer.sequences([sequence])

exit()


# drawer.map(1, [point for sequence in sequences for point in sequence])        



# log.info("Flattening...")
# corpus = [(point.x, point.y) for sequence in sequences for point in sequence]
# log.info("--> done")        


# util.save("data/corpus.pkl", corpus)


# corpus = util.load("data/corpus_house.pkl")

