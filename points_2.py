#!/usr/bin/env python3

import random, datetime, json, math, requests, json
import numpy as np
from housepy import geo, config, log, util, timeutil
from sklearn.cluster import Birch
from mongo import db
import drawer


PERIOD_SIZE = config['period_size']
PERIODS = int(1440 / PERIOD_SIZE)
LON_1, LAT_1 = config['bounds']['NW']
LON_2, LAT_2 = config['bounds']['SE']
MIN_X, MAX_Y = geo.project((LON_1, LAT_1))
MAX_X, MIN_Y = geo.project((LON_2, LAT_2))


# generator for retrieving user points from mongo
def get_user_points(user_ids):
    location = {'$geoWithin': {'$geometry': {'type': "Polygon", 'coordinates': [[ [LON_1, LAT_1], [LON_2, LAT_1], [LON_2, LAT_2], [LON_1, LAT_2], [LON_1, LAT_1] ]]}}}
    for u, user_id in enumerate(user_ids):
        log.info("USER %s..." % user_id)
        cursor = db.entries.find({'user_id': user_id, 'location': location, 't': {'$gt': timeutil.timestamp(timeutil.string_to_dt(config['start_date'], tz="America/New_York")), '$lt': timeutil.timestamp(timeutil.string_to_dt(config['stop_date'], tz="America/New_York"))}}).sort('t')
        points = [Point(point['location']['coordinates'][0], point['location']['coordinates'][1], point['t']) for point in cursor]
        log.info("--> %d points" % len(points))
        yield user_id, points
    yield (None, None)


class Point():
    def __init__(self, lon, lat, t):
        self.lon = lon
        self.lat = lat
        x, y = geo.project((self.lon, self.lat))
        self.x = (x - MIN_X) / (MAX_X - MIN_X)
        self.y = (y - MIN_Y) / (MAX_Y - MIN_Y)        
        dt = timeutil.t_to_dt(t, tz="America/New_York")
        self.period = ((dt.hour * 60) + (dt.minute)) // PERIOD_SIZE


def get_geohash_list(points):
    geohashes = [point.geohash for point in points]
    geohashes = list(set(geohashes))
    geohashes.sort()
    log.info("--> found %d locations" % len(geohashes))       
    return geohashes


def main(user_ids, draw=False):

    data = []

    for (user_id, points) in get_user_points(user_ids):        
        if points is None or not len(points):
            continue

        # cluster the points
        ct = Birch(n_clusters=None, threshold=0.01)
        ct.fit(np.array([(point.x, point.y) for point in points]))  # need to do this on normalized x,y
        centroids = ct.subcluster_centers_
        labels = ct.labels_
        log.info("--> %d clusters" % len(centroids))    
        print(len(points), len(labels))

        # reassign point properties to cluster properties
        for p, point in enumerate(points):
            point.x, point.y = centroids[labels[p]]
            x = (point.x * (MAX_X - MIN_X)) + MIN_X
            y = (point.y * (MAX_Y - MIN_Y)) + MIN_Y
            lon, lat = geo.unproject((x, y))
            point.lon = lon
            point.lat = lat
            point.geohash = geo.geohash_encode((point.lon, point.lat), precision=config['location_size'])
            point.location = labels[p]

        # distribute points to all periods
        days = []
        p = 0
        mod = 0
        while True:
            day = [None] * PERIODS
            for period in range(PERIODS):
                # take the most recent point in this period or earlier
                # if two locations are visited within PERIOD, the first is supressed (good)
                while points[p].period + mod <= period + (len(days) * PERIODS):
                    p += 1
                    if p == len(points):
                        break
                    if points[p].period < points[p-1].period:
                        mod += PERIODS
                if p == len(points):
                    break
                day[period] = points[p-1 if p > 0 else 0]
            if p == len(points):
                break
            days.append(day)

        # toss points that were too quick, and calculate locations
        points = set([point for day in days for point in day])
        geohashes = get_geohash_list(points)     
        for point in points:
            point.location = geohashes.index(point.geohash)     

        # output
        for day in days:
            output = " ".join([str(point.location) for point in day])
            print(output)
            print()
        if draw:
            drawer.days(days, user_id)
            drawer.map(points, user_id)

        log.info("--> total days for user %s: %d" % (user_id, len(days)))
        data += [point for day in days for point in day]

    # regenerate location labels globally
    geohashes = get_geohash_list(data)
    util.save("data/locations_%d_%d.pkl" % (PERIOD_SIZE, config['location_size']), geohashes)    
    log.info("Labeling...")
    for point in data:
        point.location = geohashes.index(point.geohash)         

    util.save("data/points_%d_%d.pkl" % (PERIOD_SIZE, config['location_size']), data)
    log.info("--> done")


if __name__ == "__main__":
    # users = util.load(config['users'])
    # main(users, False)
    main([1], True)



