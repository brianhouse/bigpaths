#!/usr/bin/env python3

import random
from bson.son import SON
from housepy import drawing, geo, config, log
from mongo import db
from colors import colors
from geojson import Feature, Point


NYC = Point((-74.0059, 40.7128, 0))
PVD = Point((-71.4128, 41.8240, 0))

CITY = NYC
USER_ID = None

MILES = 20
SIZE = 1


if USER_ID is not None:
    users = 1
    results = db.entries.find({'user_id': USER_ID, 'location': {'$near': {'$geometry': CITY, '$maxDistance': 1609 * MILES}}})
else:
    users = len(db.entries.distinct('user_id'))
    # results = db.entries.find({'location': {'$near': {'$geometry': CITY, '$maxDistance': 1609 * MILES}}})
    results = db.entries.find()

log.info("USERS %s" % users)
log.info("POINTS %s" % results.count())

min_x, max_y = geo.project((-180, 85))
max_x, min_y = geo.project((180, -85))

# min_x, max_y = geo.project((-75, 42))
# max_x, min_y = geo.project((-73, 40))

ratio = (max_x - min_x) / (max_y - min_y)

ctx = drawing.Context(10000, int(10000 / ratio), relative=True, flip=True, hsv=True)
log.info("%d %d" % (ctx.width, ctx.height))

for result in results:

    lon, lat, alt = result['location']['coordinates']
    x, y = geo.project((lon, lat))

    if x > max_x or x < min_x or y > max_y or y < min_y:
        continue

    x = (x - min_x) / (max_x - min_x)
    y = (y - min_y) / (max_y - min_y)

    ctx.arc(x, y, SIZE / ctx.width, SIZE / ctx.height, fill=(colors[result['user_id'] % len(colors)]), thickness=0.0)

ctx.output("maps")

