#!/usr/bin/env python3

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


# def strips(sequences, user_id=None):
#     log.info("Drawing %d sequences for user %s..." % (len(sequences), user_id))
#     t = timeutil.timestamp()
#     ctx = drawing.Context(1000, len(sequences) * 2, relative=True, flip=False, hsv=False, background=(0., 0., 0., 1.))
#     for q, sequence in enumerate(sequences):
#         for p, point in enumerate(sequence):
#             color = colors[ord(point.grid[-1]) % len(colors)]
#             ctx.line(p/PERIODS, (q/len(sequences)) - (1 / ctx.height), (p+1)/PERIODS, (q/len(sequences)) - (1 / ctx.height), stroke=color, thickness=2.0)
#     ctx.output("images/%d_%s.png" % (t, user_id))


# def sequence(sequence, suffix=None):
#     t = timeutil.timestamp()    
#     log.info("Drawing sequence...")
#     ctx = drawing.Context(1000, int(1000 / ratio), relative=True, flip=True, hsv=True)
#     ctx.image("basemap/basemap.png")
#     if len(sequence) != PERIODS:
#         log.error("--> bad sequence length (%d, expected %d)" % (len(sequence), PERIODS))
#         return
#     for s, point in enumerate(sequence):
#         if s == len(sequence) - 1:
#             continue
#         if type(point) is Point:
#             x1, y1 = point.x, point.y
#             x2, y2 = sequence[s+1].x, sequence[s+1].y
#         else:
#             x1, y1 = scale(geo.geohash_decode(grids[int(point)]))
#             x2, y2 = scale(geo.geohash_decode(grids[int(sequence[s+1])]))
#         c = s/PERIODS
#         color = c, 1., 1., 0.75
#         ctx.arc(x1, y1, 5 / ctx.width, 5 / ctx.height, fill=color, thickness=0.0)
#         ctx.line(x1, y1, x2, y2, stroke=color, thickness=1.0)
#     suffix = "_%s" % suffix if suffix is not None else ""
#     ctx.output("images/%d%s.png" % (t, suffix))    
#     log.info("--> done")


def path(cells):
    t = timeutil.timestamp()    
    log.info("Drawing path...")
    ctx = drawing.Context(1000, int(1000 / RATIO), relative=True, flip=True, hsv=True)
    ctx.image("basemap/basemap.png")
    for p in range(len(cells) - 1):
        location, duration = cells[p]
        x, y = scale(geo.geohash_decode(locations[location]))
        color = 0., 1., 1., 1.
        ctx.arc(x, y, 5 / ctx.width, 5 / ctx.height, fill=color, thickness=0.0)
    ctx.output("images/%d_path.png" % t)    
    log.info("--> done")



def scale(pt):
    x, y = geo.project(pt)
    x = (x - MIN_X) / (MAX_X - MIN_X)
    y = (y - MIN_Y) / (MAX_Y - MIN_Y)
    return x, y


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
    # gradient_test()

    cells = [53, 13, 9, 101, 2, 37, 16, 39, 109, 38, 6, 39, 93, 73, 23, 46, 111, 108, 50, 143, 8, 101, 1, 94, 26, 46, 53, 108, 21, 102, 14, 108, 43, 101, 1, 40, 3, 46, 59, 108, 51, 143, 8, 108, 1, 101, 1, 39, 80, 108, 53, 13, 11, 101, 1, 68, 1, 46, 1, 40, 1, 95, 13, 40, 55, 39, 3, 108, 65, 125, 1, 99, 15, 98, 2, 48, 2, 46, 144, 24, 2, 22, 2, 35, 3, 39, 9, 1, 6, 18, 1, 37, 2, 68, 2, 69, 19, 46, 49, 40, 2, 102, 1, 108, 48, 143, 5, 108, 8, 104, 3, 85, 24, 46, 49, 56, 2, 105, 1, 108, 19, 102, 11, 108, 11, 105, 1, 13, 15, 102, 7, 73, 1, 95, 12, 77, 1, 46, 58, 108, 51, 143, 4, 106]
    cells = list(zip(cells[1::2], cells[::2]))
    path(cells)
