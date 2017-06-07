#!/usr/bin/env python3

import random, datetime, json, math
import numpy as np
from housepy import config, log, util, timeutil
from colors import colors
from data import *
import drawer


def sequence(user_ids, draw=False):

    for (user_id, points) in get_user(user_ids):        
        if points is None or not len(points):
            continue

        points = filter_transients(points)     
        points = join_adjacent(points)
        points = calculate_durations(points)
        cluster(points)
        grids = generate_grid_list(points)

        log.info("Labeling...")
        for point in points:
            point.label = grids.index(point.grid)     

        if draw:
            drawer.map([points])

        log.info("--> total points for user %s: %d" % (user_id, len(points)))

    util.save("data/sequences_alt_%d_%d.pkl" % (config['grid'], config['periods']), points)
    log.info("--> done")



if __name__ == "__main__":
    sequence([1], False)
