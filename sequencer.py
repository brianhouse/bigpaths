#!/usr/bin/env python3

import random, datetime, json, math
import numpy as np
from housepy import config, log, util, timeutil
from colors import colors
from data import *
import drawer


def sequence(user_ids, draw_maps=False, draw_strips=False):

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
        current_location = None
        while day < stop_dt - datetime.timedelta(days=1):
            d_start_t = timeutil.timestamp(day)
            day += datetime.timedelta(days=1)
            d_stop_t = timeutil.timestamp(day)

            # get points and transients for this day
            day_points = [point for point in points if point.t >= d_start_t and point.t < d_stop_t]
            day_transients = [point for point in transients if point.t >= d_start_t and point.t < d_stop_t]
            if len(day_points) == 0:
                continue

            # get the daily period for each of these points
            def get_periods(points):            
                periods = np.array([point.t for point in points])
                periods -= d_start_t
                periods //= 60
                periods //= math.floor(86400 / 60 / PERIODS)
                periods = list(periods)
                return periods                
            point_periods = get_periods(day_points)
            transient_periods = get_periods(day_transients)

            # add this point to the sequence
            sequence = []
            for i in range(PERIODS):
                if i in point_periods:
                    current_location = day_points[point_periods.index(i)]
                # elif i in transient_periods:    # prioritize the destination
                #     current_location = None
                sequence.append(current_location)       
            user_sequences.append(sequence)

        log.info("--> generated %s sequences for user %s" % (len(user_sequences), user_id))
        if len(user_sequences) == 0:
            continue

        # draw things
        if draw_maps or draw_strips:
            cluster(points)
            if draw_maps:
                drawer.map(user_id, points)
            if draw_strips:
                drawer.strips(user_id, user_sequences)      

        # fix leading Nones
        i = 0
        while user_sequences[0][i] is None:
            i += 1
        user_sequences[0][0:i] = [user_sequences[0][i]] * i
        sequences.extend(user_sequences)

    log.info("--> generated %s total sequences" % len(sequences))

    return sequences


if __name__ == "__main__":
    sequence([1], True, True)
