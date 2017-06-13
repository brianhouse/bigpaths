#!/usr/bin/env python3

import random, sys
import numpy as np
import drawer
from housepy import config, log, geo
from points import *

# days = util.load("data/1497307838_10_6_house_0.25_output.pkl")
# drawer.strips([point for day in days for point in day])


days = util.load("data/1497313211_10_7_house_0.25_output.pkl")
day = random.choice(days)
drawer.path_print(day)

