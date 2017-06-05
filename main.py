#!/usr/bin/env python3

import json, math
import drawer
from sequencer import sequence
from housepy import util, config, log, geo
from data import *



# sequences = util.load("data/sequences_%d_%d.pkl" % (config['grid'], config['periods']))
# D = 20
# sequence = sequences[D]
# drawer.map([sequence])
# drawer.strips([sequence] * 20)
# drawer.sequence(sequence)

# test sequence
skip = math.ceil(PERIODS / len(grids))
sequence = []
for i in range(PERIODS):
    sequence.append(math.floor(i / skip))
    

drawer.sequence(sequence)