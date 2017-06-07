#!/usr/bin/env python3

import random, datetime, json, math
import numpy as np
from housepy import config, log, util, timeutil
from colors import colors
from data import *
import drawer


def sequence(user_ids, draw=False):

    sequences = []            

    for (user_id, points) in get_user(user_ids):        
        if points is None or not len(points):
            continue

        user_sequences = []

        # filter out transients
        points, transients = filter_transients(points)     

        # get our start and stop times
        start_dt = timeutil.t_to_dt(points[0].t, tz="America/New_York")  ## why.
        stop_dt = timeutil.t_to_dt(points[-1].t, tz="America/New_York")
        log.info("--> start %s" % start_dt)
        log.info("--> stop  %s" % stop_dt)
        log.info("--> %s" % (stop_dt - start_dt))

        # iterate through days
        day = start_dt.replace(hour=0, minute=0, second=0) + datetime.timedelta(days=1)
        point = None
        while day < stop_dt - datetime.timedelta(days=1):
            d_start_t = timeutil.timestamp(day)
            day += datetime.timedelta(days=1)
            d_stop_t = timeutil.timestamp(day)

            # get points and transients for this day
            day_points = [point for point in points if point.t >= d_start_t and point.t < d_stop_t]
            if len(day_points) == 0:
                continue

            # get the daily period for each of these points
            periods = np.array([point.t for point in day_points])
            periods -= d_start_t
            periods //= 60
            periods //= math.floor(86400 / 60 / PERIODS)
            periods = list(periods)

            ## there is a duplicate problem here. if you go two places, the second gets erased.
            # it should at least be on deck if there is a spare spot
            # print(periods)

            # add this point to the sequence
            sequence = []
            for i in range(PERIODS):
                if i in periods:
                    point = day_points[periods.index(i)]
                sequence.append(point)       
            user_sequences.append(sequence)

        # fix leading Nones
        i = 0
        while user_sequences[0][i] is None:
            i += 1
        user_sequences[0][0:i] = [user_sequences[0][i]] * i

        log.info("--> generated %s sequences for user %s" % (len(user_sequences), user_id))
        if len(user_sequences) == 0:
            continue
        sequences.extend(user_sequences)

        # draw things
        if draw:
            drawer.map(user_sequences, user_id)
            drawer.strips(user_sequences, user_id)

    log.info("--> generated %s total sequences" % len(sequences))

    log.info("Generating grids...")
    grids = [point.grid for sequence in sequences for point in sequence]
    grids = list(set(grids))
    grids.sort()
    util.save("data/grids_%d_%d.pkl" % (config['grid'], config['periods']), grids)
    log.info("--> found grids: %s" % [grids])

    log.info("Labeling...")
    for sequence in sequences:
        for point in sequence:
            point.label = grids.index(point.grid) 
    util.save("data/sequences_%d_%d.pkl" % (config['grid'], config['periods']), sequences)
    log.info("--> done")


if __name__ == "__main__":
    sequence([1], True)
