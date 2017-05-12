#!/usr/bin/env python3

import random
from bson.son import SON
from housepy import drawing, geo, config, log
from mongo import db
from colors import colors
from geojson import Feature, Point

USER_ID = 24676
USER_ID = None

NYC = Point((-74.0059, 40.7128, 0))
MILES = 5

if USER_ID is not None:
    users = 1
    # results = db.entries.find({'properties.user_id': USER_ID, "loc" : SON([("$near", { "$geometry" : SON([("type", "Point"), ("coordinates", [40, 5])])}), ("$maxDistance", 1609 * MILES)])}))
else:
    users = len(db.entries.distinct('user_id'))
    results = db.entries.find({'geometry': {'$near': {'$geometry': NYC, '$maxdistance': 1609 * MILES}}})

log.info("USERS %s" % users)
log.info("POINTS %s" % results.count())

min_x, max_y = geo.project((-180, 85))
max_x, min_y = geo.project((180, -85))
ratio = (max_x - min_x) / (max_y - min_y)

ctx = drawing.Context(10000, int(10000 / ratio), relative=True, flip=True, hsv=True)
log.info("%d %d" % (ctx.width, ctx.height))

for result in results:

    x, y = geo.project((result['location'][0], result['location'][1]))

    if x > max_x or x < min_x or y > max_y or y < min_y:
        continue

    x = (x - min_x) / (max_x - min_x)
    y = (y - min_y) / (max_y - min_y)

    size = 5.0 if users == 1 else 1.0

    ctx.arc(x, y, size / ctx.width, size / ctx.height, fill=(colors[result['user_id'] % len(colors)]), thickness=0.0)

ctx.output("maps")