#!/usr/bin/env python3

import random, datetime, sys
import numpy as np
from housepy import geo, config, log, util, timeutil, drawing
from sklearn.cluster import Birch
from mongo import db
from colors import colors
import drawer


LON_1, LAT_1 = config['bounds']['NW']
LON_2, LAT_2 = config['bounds']['SE']
MIN_X, MAX_Y = geo.project((LON_1, LAT_1))
MAX_X, MIN_Y = geo.project((LON_2, LAT_2))
RATIO = (MAX_X - MIN_X) / (MAX_Y - MIN_Y)

SIZE = 1

config['start_date'] = config['start_date_1']
config['stop_date'] = config['stop_date_1']


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
        self.centroid_x = None
        self.centroid_y = None
        self.label = None

gen = get_user_points([1], 10)
points = next(gen)[1]

# cluster the points
ct = Birch(n_clusters=None, threshold=0.001)                 # clusters of points within ~100ft are likely the same location
ct.fit(np.array([(point.x, point.y) for point in points]))   # need to do this on normalized x,y
centroids = ct.subcluster_centers_
labels = ct.labels_
log.info("--> %d clusters" % len(centroids))    

for p, point in enumerate(points):
    point.centroid_x, point.centroid_y = centroids[labels[p]]
    point.label = labels[p]


ctx = drawing.Context(3000, int(3000 / RATIO), relative=True, flip=True, hsv=False)
ctx.image("basemap/basemap.png")

for point in points:
    color = colors[point.label % len(colors)]
    ctx.arc(point.x, point.y, SIZE / ctx.width, SIZE / ctx.height, fill=color, thickness=0.0)
    ctx.line(point.x, point.y, point.centroid_x, point.centroid_y, stroke=color, thickness=1.0)

ctx.output("images/clusters.png")


