#!/usr/bin/env python3

import time
from housepy import drawing, util, log, config, geo, timeutil
from colors import colors
from points import *


def map(points, user_id=None):
    log.info("Drawing map for user %s..." % user_id)
    ctx = drawing.Context(1000, int(1000 / RATIO), relative=True, flip=True, hsv=False)
    ctx.image("basemap/basemap.png")
    for point in points:
        color = colors[point.location % len(colors)]
        ctx.arc(point.x, point.y, 3 / ctx.width, 3 / ctx.height, fill=color, thickness=0.0)
    ctx.output("images/%d_map.png" % user_id)
    log.info("--> done")


def strips(points, user_id=None):
    log.info("Drawing strips for user %s..." % user_id)
    t = str(timeutil.timestamp(ms=True)).replace(".", "-")
    lines = []
    q = 0
    for p, point in enumerate(points):
        prev = points[p-1] if p > 0 else None
        if prev is not None and point.period < prev.period:
            q += 1
        color = colors[point.location % len(colors)]        
        lines.append([(point.period/PERIODS) * 1000, q, ((point.period + point.duration)/PERIODS) * 1000, q, color, 8.0])
        if point.period + point.duration > PERIODS:
            overflow = (point.period + point.duration) - PERIODS
            lines.append([0, q+1, (overflow/PERIODS) * 1000, q+1, color, 8.0])
    ctx = drawing.Context(1000, ((q + 2) * 10) + 2, relative=False, flip=False, hsv=False, background=(0., 0., 0., 1.))
    for line in lines:
        line[1] = line[3] = (((line[1] / (q + 2))) * ((q + 2) * 10)) + 6
        ctx.line(*line)
    ctx.output("images/%s_%s_strips.png" % (t, user_id))


def path(points):
    t = str(timeutil.timestamp(ms=True)).replace(".", "-")
    log.info("Drawing path...")
    ctx = drawing.Context(1000, int(1000 / RATIO), relative=True, flip=True, hsv=True)
    ctx.image("basemap/basemap.png")
    for p in range(len(points)):
        x1, y1 = points[p].x, points[p].y
        color = points[p].period / PERIODS, 1., 1., 1.
        ctx.arc(x1, y1, 5 / ctx.width, 5 / ctx.height, fill=color, thickness=0.0)
        if p < len(points) - 1:
            x2, y2 = points[p+1].x, points[p+1].y        
            ctx.line(x1, y1, x2, y2, stroke=color, thickness=1.0)
    ctx.output("images/%s_path.png" % t)    
    log.info("--> done")



def gradient_test():
    ctx = drawing.Context(1000, 250, relative=True, flip=True, hsv=True)
    for x in range(1440):
        # c = ((x/288) * 0.35) + .3
        # c = ((x/288) * 0.35) + .0
        c = ((x/1440) * 0.65) + .0
        c = x/1440
        ctx.line(x / 1440, 0, x / 1440, 1, stroke=(c, 1., 1., 1.), thickness=(ctx.width/1440) + 1)
    ctx.output("gradient.png")


if __name__ == "__main__":
    gradient_test()
