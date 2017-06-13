#!/usr/bin/env python3

import random, sys
import numpy as np
import drawer
from housepy import config, log, geo
from points import *

days = util.load("data/1497311751_output.pkl")

for day in days:
    drawer.path(day)
    break

# drawer.strips([point for day in days for point in day])
