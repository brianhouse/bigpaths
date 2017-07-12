#!/usr/bin/env python3

import time, math
from housepy import drawing, util, log, config, geo, timeutil
from points import RATIO, MIN_X, MAX_X, MIN_Y, MAX_Y


def days(days, prefix=None, open_file=True):
    log.info("Drawing %d days for %s..." % (len(days), prefix))
    ctx = drawing.Context(1000, len(days) * 10, relative=True, flip=False, hsv=True, background=(0., 0., 0., 1.))    
    locations = list(set([location for day in days for location in day]))
    locations.sort()
    for d, day in enumerate(days):
        for period, location in enumerate(day):
            color = locations.index(location) / len(locations), 1., 1., 1.                 
            ctx.line(period / len(day), (d / len(days)) + 5/ctx.height, (period + 1) / len(day), (d / len(days)) + 5/ctx.height, stroke=color, thickness=8)
    ctx.output("images/%s_days.png" % prefix, open_file)
    log.info("--> done")

def map(days, prefix=None, open_file=True):
    log.info("Drawing map for %s..." % prefix)
    ctx = drawing.Context(3000, int(3000 / RATIO), relative=True, flip=True, hsv=True)
    ctx.image("basemap/basemap.png")
    locations = list(set([location for day in days for location in day]))
    locations.sort()    
    for d, day in enumerate(days):
        for period, location in enumerate(day):
            color = locations.index(location) / len(locations), 1., 1., 1.
            lonlat = geo.geohash_decode("dr" + location)
            x, y = geo.project(lonlat)
            x = (x - MIN_X) / (MAX_X - MIN_X)
            y = (y - MIN_Y) / (MAX_Y - MIN_Y)                    
            ctx.arc(x, y, 30 / ctx.width, 30 / ctx.height, fill=color, thickness=0.0)
    ctx.output("images/%s_map.png" % prefix, open_file)
    log.info("--> done")
