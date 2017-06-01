#!/usr/bin/env python3

import random, datetime, json, math
import numpy as np
from housepy import drawing, geo, config, log, util, timeutil
from colors import colors
from data import *


def sequence():

    sequences = []            

    for (user_id, points) in get_user():        
        if points is None:
            break

        user_sequences = []

        # filter out transients
        points, transients = filter_transients(points)     

        # draw_points(user_id, points)

        # get our start and stop times
        start_dt = timeutil.t_to_dt(points[0].t, tz="America/New_York")  ## why.
        stop_dt = timeutil.t_to_dt(points[-1].t, tz="America/New_York")
        log.info("--> start %s" % start_dt)
        log.info("--> stop  %s" % stop_dt)
        log.info("--> %s" % (stop_dt - start_dt))

        # iterate through days
        day = start_dt.replace(hour=0, minute=0, second=0) + datetime.timedelta(days=1)
        current_grid = None
        while day < stop_dt - datetime.timedelta(days=1):
            d_start_t = timeutil.timestamp(day)
            day += datetime.timedelta(days=1)
            d_stop_t = timeutil.timestamp(day)

            # get points and transients for this day
            day_points = [point for point in points if point.t >= d_start_t and point.t < d_stop_t]
            day_transients = [point for point in transients if point.t >= d_start_t and point.t < d_stop_t]
            if len(day_points) == 0:
                # current_grid = None
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
                    current_grid = day_points[point_periods.index(i)]
                elif i in transient_periods:    # prioritize the destination
                    current_grid = None
                sequence.append(current_grid)                    
            user_sequences.append(sequence)

        log.info("--> generated %s sequences for user %s" % (len(user_sequences), user_id))
        # draw_strips(user_id, user_sequences)

        sequences.extend(user_sequences)

    log.info("--> generated %s total sequences" % len(sequences))
    log.info("--> done")        

    return sequences


if __name__ == "__main__":
    sequence()
