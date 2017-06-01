#!/usr/bin/env python3

import random, datetime, json, math
import numpy as np
from housepy import drawing, geo, config, log, util, timeutil
from mongo import db
from colors import colors
from sklearn.cluster import Birch

START_DATE = "2012-01-01"
STOP_DATE  = "2015-01-01"

PERIODS = 144   # 10min
# PERIODS = 288   # 5min

LON_1, LAT_1 = -74.053573, 40.919423    # NW
LON_2, LAT_2 = -73.699264, 40.538534    # SE

min_x, max_y = geo.project((LON_1, LAT_1))
max_x, min_y = geo.project((LON_2, LAT_2))
ratio = (max_x - min_x) / (max_y - min_y)
location = {'$geoWithin': {'$geometry': {'type': "Polygon", 'coordinates': [[ [LON_1, LAT_1], [LON_2, LAT_1], [LON_2, LAT_2], [LON_1, LAT_2], [LON_1, LAT_1] ]]}}}


class Point():

    def __init__(self, lon, lat, t):
        self.lon = lon
        self.lat = lat
        x, y = geo.project((self.lon, self.lat))
        self.x = (x - min_x) / (max_x - min_x)
        self.y = (y - min_y) / (max_y - min_y)
        self.t = t
        self.hash = geo.geohash_encode((lon, lat), precision=6)
        # self.centroid = geo.geohash_decode(self.hash)

    def distance(self, pt):
        return geo.distance((self.lon, self.lat), (pt.lon, pt.lat))


def main():

    user_ids = util.load("user_ids.pkl")
    user_ids = [1]  # me
    user_ids = [8093]

    for u, user_id in enumerate(user_ids):

        if u == 5:
            break

        # retrieve all user points
        log.info("USER %s..." % user_id)
        cursor = db.entries.find({'user_id': user_id, 'location': location, 't': {'$gt': timeutil.timestamp(timeutil.string_to_dt(START_DATE, tz="America/New_York")), '$lt': timeutil.timestamp(timeutil.string_to_dt(STOP_DATE, tz="America/New_York"))}}).sort('t')
        points = [Point(point['location']['coordinates'][0], point['location']['coordinates'][1], point['t']) for point in cursor]
        log.info("--> %d points" % len(points))

        # filter out transient points: greater than 1/20mi (1 city block) covered in 10mins on both sides
        # so in theory, if you run to the bodega nearby, that's still cool
        marks = []
        for p, point in enumerate(points):
            if p == 0 or p == len(points) - 1:
                continue
            prev, next = points[p-1], points[p+1]
            if point.t - prev.t <= 10 * 60 and next.t - point.t <= 10 * 60 and point.distance(prev) > 1/20 and point.distance(next) > 1/20:
                marks.append(p)
        log.info("--> marked %d transients" % len(marks))
        transients = [point for (p, point) in enumerate(points) if p in marks]
        points = [point for (p, point) in enumerate(points) if p not in marks]        

        # draw_points(user_id, points)

        # get our start and stop times
        start_dt = timeutil.t_to_dt(points[0].t, tz="America/New_York")  ## why.
        stop_dt = timeutil.t_to_dt(points[-1].t, tz="America/New_York")
        log.info("--> start %s" % start_dt)
        log.info("--> stop  %s" % stop_dt)
        log.info("--> %s" % (stop_dt - start_dt))

        sequences = []

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

            # add the geohash grid of this point to the sequence
            sequence = []
            for i in range(PERIODS):
                if i in point_periods:
                    current_grid = day_points[point_periods.index(i)].hash
                elif i in transient_periods:    # prioritize the destination
                    current_grid = None
                sequence.append(current_grid)                    
            sequences.append(sequence)

        log.info("--> generated %s sequences" % len(sequences))
        draw_strips(user_id, sequences)
        log.info("--> done")        


def draw_points(user_id, points):
    log.info("Drawing points for user %s..." % user_id)
    t = timeutil.timestamp()
    ctx = drawing.Context(1000, int(1000 / ratio), relative=True, flip=True, hsv=False)
    ctx.image("basemap/basemap.png")
    for point in points:
        color = colors[ord(point.hash[-1]) % len(colors)]
        ctx.arc(point.x, point.y, 3 / ctx.width, 3 / ctx.height, fill=color, thickness=0.0)
    ctx.output("grid/%d_%d.png" % (t, user_id))


def draw_strips(user_id, sequences):
    t = timeutil.timestamp()
    log.info("Drawing %d sequences for user %s..." % (len(sequences), user_id))
    ctx = drawing.Context(1000, len(sequences) * 2, relative=True, flip=False, hsv=False, background=(0., 0., 0., 1.))
    for q, sequence in enumerate(sequences):
        for p, grid in enumerate(sequence):
            if grid is None:
                continue
            color = colors[ord(grid[-1]) % len(colors)]
            ctx.line(p/PERIODS, (q/len(sequences)) - (1 / ctx.height), (p+1)/PERIODS, (q/len(sequences)) - (1 / ctx.height), stroke=color, thickness=2.0)
    ctx.output("strips/%d_%d.png" % (t, user_id))


if __name__ == "__main__":
    main()
