#!/usr/bin/env python3

import json
import drawer
from sequencer import sequence
from housepy import util, config, log, geo
from data import *



corpus = util.load("data/corpus_%d_%d.pkl" % (config['grid'], config['periods']))

# test sequence drawing
d = 20
sequence = corpus[(d * PERIODS):(d * PERIODS) + PERIODS]
print(sequence)
drawer.sequence(sequence)


