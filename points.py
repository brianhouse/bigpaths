#!/usr/bin/env python3

import random, datetime
import numpy as np
from housepy import geo, config, log, util, timeutil
from sklearn.cluster import Birch
from mongo import db
import drawer


LON_1, LAT_1 = config['bounds']['NW']
LON_2, LAT_2 = config['bounds']['SE']
MIN_X, MAX_Y = geo.project((LON_1, LAT_1))
MAX_X, MIN_Y = geo.project((LON_2, LAT_2))
RATIO = (MAX_X - MIN_X) / (MAX_Y - MIN_Y)


# generator for retrieving user points from mongo
def get_user_points(user_ids, period_size):
    location = {'$geoWithin': {'$geometry': {'type': "Polygon", 'coordinates': [[ [LON_1, LAT_1], [LON_2, LAT_1], [LON_2, LAT_2], [LON_1, LAT_2], [LON_1, LAT_1] ]]}}}
    for u, user_id in enumerate(user_ids):
        log.info("USER %s..." % user_id)
        cursor = db.entries.find({'user_id': user_id, 'location': location, 't': {'$gt': timeutil.timestamp(timeutil.string_to_dt(config['start_date'], tz="America/New_York")), '$lt': timeutil.timestamp(timeutil.string_to_dt(config['stop_date'], tz="America/New_York"))}}).sort('t')
        points = [Point(point['location']['coordinates'][0], point['location']['coordinates'][1], point['t'], period_size) for point in cursor]
        log.info("--> %d points" % len(points))
        yield user_id, points
    yield (None, None)


class Point():
    def __init__(self, lon, lat, t, period_size):
        self.lon = lon
        self.lat = lat
        x, y = geo.project((self.lon, self.lat))
        self.x = (x - MIN_X) / (MAX_X - MIN_X)
        self.y = (y - MIN_Y) / (MAX_Y - MIN_Y)        
        dt = timeutil.t_to_dt(t, tz="America/New_York")
        self.period = ((dt.hour * 60) + (dt.minute)) // period_size
        self.location = None


def main(user_ids, period_size, location_size, draw=False):

    all_days = []

    for (user_id, points) in get_user_points(user_ids, period_size):        
        if points is None or not len(points):
            continue

        # cluster the points
        ct = Birch(n_clusters=None, threshold=0.01)
        ct.fit(np.array([(point.x, point.y) for point in points]))  # need to do this on normalized x,y
        centroids = ct.subcluster_centers_
        labels = ct.labels_
        log.info("--> %d clusters" % len(centroids))    

        # reassign point properties to cluster properties (spatial low-pass)
        for p, point in enumerate(points):
            point.x, point.y = centroids[labels[p]]
            x = (point.x * (MAX_X - MIN_X)) + MIN_X
            y = (point.y * (MAX_Y - MIN_Y)) + MIN_Y
            lon, lat = geo.unproject((x, y))
            point.lon = lon
            point.lat = lat
            point.location = geo.geohash_encode((point.lon, point.lat), precision=location_size).lstrip('dr')

        # distribute points to all periods, toss transients (temporal low-pass)
        periods = int(1440 / period_size)
        days = []
        p = 0
        mod = 0
        while True:
            day = [None] * periods
            for period in range(periods):
                # take the most recent point in this period or earlier
                # if two locations are visited within PERIOD, the first is supressed (good)
                while points[p].period + mod <= period + (len(days) * periods):
                    p += 1
                    if p == len(points):
                        break
                    if points[p].period < points[p-1].period:
                        mod += periods
                if p == len(points):
                    break
                day[period] = points[p-1 if p > 0 else 0]
            if p == len(points):
                break
            days.append(day)

        # flatten to location
        for day in days:
            for p, point in enumerate(day):
                day[p] = point.location

        # monitor output
        for day in days:
            output = " ".join([location for period, location in enumerate(day)])
            print(output)
            print()
        if draw:
            drawer.days(days, "user_%d" % user_id)
            drawer.map(days, "user_%d" % user_id)

        log.info("--> total days for user %s: %d" % (user_id, len(days)))
        all_days += days

    t = timeutil.timestamp()
    X_train = np.array(all_days)
    # drawer.days(X_train[:1000], t)  # cairo has limits

    # flatten into text
    output = ".".join([";".join(day) for day in all_days])

    with open("data/%d_corpus_%d_%d_%d.txt" % (t, period_size, location_size, len(user_ids)), 'w') as f:
        f.write(output)
    log.info("--> done")


if __name__ == "__main__":
    user_ids = util.load("data/user_ids_filtered.pkl")
    main(user_ids, 20, 6, False)
    # main([1], 20, 6, True)
