#!/usr/bin/env python3

import random, datetime
import numpy as np
from bson.son import SON
from housepy import drawing, geo, config, log, util, timeutil
from mongo import db
from colors import colors
from geojson import Feature, Point

LON_1, LAT_1 = -74.053573, 40.919423
LON_2, LAT_2 = -73.699264, 40.538534
min_x, max_y = geo.project((LON_1, LAT_1))
max_x, min_y = geo.project((LON_2, LAT_2))
ratio = (max_x - min_x) / (max_y - min_y)

location = {'$geoWithin': {'$geometry': {'type': "Polygon", 'coordinates': [[ [LON_1, LAT_1], [LON_2, LAT_1], [LON_2, LAT_2], [LON_1, LAT_2], [LON_1, LAT_1] ]]}}}


def save_users():
    user_ids = db.entries.find({'location': location}).distinct('user_id')
    util.save("user_ids.pkl", user_ids)


def draw_points(user_id, points):
    t = timeutil.timestamp()
    ctx = drawing.Context(1000, int(1000 / ratio), relative=True, flip=True, hsv=True)
    for point in points:
        x, y = geo.project((point[0], point[1]))
        x = (x - min_x) / (max_x - min_x)
        y = (y - min_y) / (max_y - min_y)
        ctx.arc(x, y, 1 / ctx.width, 1 / ctx.height, fill=(0., 0., 0., 1.), thickness=0.0)
    ctx.output("users/%d_%d.png" % (t, user_id))


def draw_path(user_id, day, points):
    t = timeutil.timestamp()
    ctx = drawing.Context(1000, int(1000 / ratio), relative=True, flip=True, hsv=True)
    ps = []
    for point in points:
        x, y = geo.project((point[0], point[1]))
        x = (x - min_x) / (max_x - min_x)
        y = (y - min_y) / (max_y - min_y)
        ps.append((x, y))
        ctx.arc(x, y, 3 / ctx.width, 3 / ctx.height, fill=(0., 0., 0., 1.), thickness=0.0)
    ctx.line(ps, stroke=(0., 0., 0., 1.), thickness=1.0)        
    ctx.output("users/%d_%d_%d.png" % (t, day, user_id))


# save_users()
user_ids = util.load("user_ids.pkl")

for u, user_id in enumerate(user_ids):
    log.info("USER %s..." % user_id)
    points = db.entries.find({'user_id': user_id, 'location': location}).sort('t')
    points = [(point['location']['coordinates'][0], point['location']['coordinates'][1], point['t']) for point in points]
    log.info("--> %d points" % len(points))

    draw_points(user_id, points)
    break

    start_t = points[0][-1]
    stop_t = points[-1][-1]
    start_dt = timeutil.t_to_dt(start_t)
    stop_dt = timeutil.t_to_dt(stop_t)
    delta = stop_dt - start_dt

    log.info("--> start_t %d %s" % (start_t, timeutil.t_to_string(start_t, tz='UTC')))
    log.info("--> stop_t  %d %s" % (stop_t, timeutil.t_to_string(stop_t, tz='UTC')))
    log.info("--> %s" % delta)

    d = 0
    day = start_dt.replace(hour=0, minute=0, second=0) + datetime.timedelta(days=1)
    while day < stop_dt - datetime.timedelta(days=1):
        d_start_t = timeutil.timestamp(day)
        day += datetime.timedelta(days=1)
        d_stop_t = timeutil.timestamp(day)

        day_points = [point for point in points if point[-1] >= d_start_t and point[-1] < d_stop_t]
        if len(day_points) < 10:
            continue

        draw_path(user_id, d, day_points)

        d += 1

