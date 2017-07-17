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

def itinerary(points, slug, index):
    t = str(timeutil.timestamp(ms=True)).replace(".", "-")
    log.info("Drawing path...")
    ctx = drawing.Context(3000, int(3000 / RATIO), relative=True, flip=True, hsv=True)
    ctx.image("basemap/basemap.png")
    midline = sum([point.x for point in points]) / len(points)
    poss = []
    for p in range(len(points)):
        x1, y1 = points[p].x, points[p].y
        if p < len(points) - 1:
            x2, y2 = points[p+1].x, points[p+1].y        
            ctx.line(x1, y1, x2, y2, stroke=(0., 0., .5, 1.), thickness=5.0)
        ctx.arc(x1, y1, 15 / ctx.width, 15 / ctx.height, fill=(0., 0., 0., 1.), thickness=0.0)
        flip = False
        if x1 < midline:
            flip = True
        for pos in poss:
            dist_x = abs(x1 - pos[0]) * ctx.height
            dist_y = abs(y1 - pos[1]) * ctx.height
            if dist_y <= 100 and dist_x <= 400:
                flip = not flip
        if not flip:
            x = x1 + (30 / ctx.width)
        else:
            x = x1 - (50 / ctx.width)
        y = y1 - (12 / ctx.height)
        poss.append((x, y))
        ctx.label(x, y, str(p+1), stroke=(0., 0., 0., 1.), font="Monaco", size=36)        
    for p, point in enumerate(points):
        label = "%d) %s %s%s" % (p+1, "Wake up at" if p == 0 else "%s," % point.display_time, point.address, "" if p != (len(points) - 1) else " ... sleep")
        ctx.label((200 / ctx.width), 1.0 - ((200 + (40*p)) / ctx.height), label, stroke=(0., 0., 0., 1.), font="Monaco", size=36)
    ctx.output("images/%s_%s_path.png" % (slug, index))    
    log.info("--> done")