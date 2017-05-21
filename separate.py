#!/usr/bin/env python3

import random
import numpy as np
from bson.son import SON
from housepy import drawing, geo, config, log, util, timeutil
from mongo import db
from colors import colors
from geojson import Feature, Point

SIZE = 1

LON_1, LAT_1 = -74.053573, 40.919423
LON_2, LAT_2 = -73.699264, 40.538534
min_x, max_y = geo.project((LON_1, LAT_1))
max_x, min_y = geo.project((LON_2, LAT_2))
ratio = (max_x - min_x) / (max_y - min_y)

location = {'$geoWithin': {'$geometry': {'type': "Polygon", 'coordinates': [[ [LON_1, LAT_1], [LON_2, LAT_1], [LON_2, LAT_2], [LON_1, LAT_2], [LON_1, LAT_1] ]]}}}


def save_users():
    user_ids = db.entries.find({'location': location}).distinct('user_id')
    util.save("user_ids.pkl", user_ids)
# save_users()

user_ids = util.load("user_ids.pkl")
t = timeutil.timestamp()

for u, user_id in enumerate(user_ids):
    log.info("USER %s..." % user_id)
    points = db.entries.find({'user_id': user_id, 'location': location}).sort('t')
    points = np.array([(point['location']['coordinates'][0], point['location']['coordinates'][1], point['t']) for point in points])
    log.info("%d points" % len(points))
    log.debug(points[0])
    log.debug(points[-1])

    ctx = drawing.Context(1000, int(1000 / ratio), relative=True, flip=True, hsv=True)
    log.info("Drawing %d %d..." % (ctx.width, ctx.height))
    for point in points:
        x, y = geo.project((point[0], point[1]))
        x = (x - min_x) / (max_x - min_x)
        y = (y - min_y) / (max_y - min_y)
        ctx.arc(x, y, SIZE / ctx.width, SIZE / ctx.height, fill=(0., 0., 0., 1.), thickness=0.0)

    ctx.output("users/%d_%d.png" % (t, user_id))

    if u == 10:
        break