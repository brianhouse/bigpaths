#!/usr/bin/env python3

import time, math
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
    ctx.output("images/%d_map.png" % user_id, False)
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
    ctx.output("images/%s_%s_strips.png" % (t, user_id), True)


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


def path_print(points):
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
        if p == 0:
            tod = "Wake"
        else:
            tod = timeutil.seconds_to_string(points[p].period * 10 * 60, show_seconds=False, pm=True).lstrip("0").replace(" ", "")
        print(tod)
        flip = False
        if x1 < midline:
            flip = True
        for pos in poss:
            dist_x = abs(x1 - pos[0]) * ctx.height
            dist_y = abs(y1 - pos[1]) * ctx.height
            # print(dist_x, dist_y)
            if dist_y <= 100 and dist_x <= 400:
                # print("flipping")
                flip = not flip
        # print()
        if not flip:
            x = x1 + (30 / ctx.width)
        else:
            if len(tod) == 6:
                x = x1 - (160 / ctx.width)
            else:
                x = x1 - (180 / ctx.width)
        y = y1 - (12 / ctx.height)
        poss.append((x, y))
        ctx.label(x, y, tod, stroke=(0., 0., 0., 1.), font="Monaco", size=36)
        if p == len(points) - 1:
            ctx.label(x, y - (40 / ctx.height), "Sleep", stroke=(0., 0., 0., 1.), font="Monaco", size=36)
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
