#!/usr/bin/env python3

import json
import drawer
from sequencer import sequence
from housepy import util, config, log, geo
from data import *



sequences = util.load("data/sequences_%d_%d.pkl" % (config['grid'], config['periods']))

D = 20
sequence = sequences[D]
# drawer.map([sequence])
# drawer.strips([sequence] * 20)

drawer.sequence(sequence)


