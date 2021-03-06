#!/usr/bin/env python3

import random
import numpy as np
from housepy import drawing, geo, config, log
from mongo import db
from colors import colors
from geojson import Point


# PVD = Point((-71.4128, 41.8240, 0))
NYC = Point((-74.0059, 40.7128, 0))
LAX = Point((-118.2437, 34.0522))
BER = Point((13.4050, 52.5200))
LON = Point((-0.1278, 51.5074))
SFO = Point((-122.4194, 37.7749))
ATL = Point((-84.3880, 33.7490))
TOK = Point((139.6917, 35.6895))
MOS = Point((37.6173, 55.7558))

BKN = Point((-73.9442, 40.6783))
QNS = Point((-73.919632, 40.743276))

CITY = QNS
MILES = 10
SIZE = 1
# results = db.entries.find({'location': {'$near': {'$geometry': CITY, '$maxDistance': 1609 * MILES}}})

LON_1, LAT_1 = -74.053573, 40.919423
LON_2, LAT_2 = -73.699264, 40.538534
results = db.entries.find({'location': {'$geoWithin': {'$geometry': {'type': "Polygon", 'coordinates': [[ [LON_1, LAT_1], [LON_2, LAT_1], [LON_2, LAT_2], [LON_1, LAT_2], [LON_1, LAT_1] ]]}}}})
    

log.info("POINTS %s" % results.count())
users = len(results.distinct('user_id'))
log.info("USERS %s" % users)

points = np.array([(result['location']['coordinates'][0], result['location']['coordinates'][1], result['user_id']) for result in results])

min_lon, max_lon = (np.min(points[:,0]), np.max(points[:,0]))
min_lat, max_lat = (np.min(points[:,1]), np.max(points[:,1]))
log.debug("%f %f %f %f" % (min_lon, max_lon, min_lat, max_lat))

min_x, max_y = geo.project((min_lon, max_lat))
max_x, min_y = geo.project((max_lon, min_lat))

ratio = (max_x - min_x) / (max_y - min_y)

ctx = drawing.Context(1000, int(1000 / ratio), relative=True, flip=True, hsv=True)
log.info("Drawing %d %d..." % (ctx.width, ctx.height))

for point in points:

    x, y = geo.project((point[0], point[1]))

    if x > max_x or x < min_x or y > max_y or y < min_y:
        continue

    x = (x - min_x) / (max_x - min_x)
    y = (y - min_y) / (max_y - min_y)

    ctx.arc(x, y, SIZE / ctx.width, SIZE / ctx.height, fill=(colors[int(point[2]) % len(colors)]), thickness=0.0)

ctx.output("cities")

