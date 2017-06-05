#!/usr/bin/env python3

from housepy import drawing, util, log, config, geo
from colors import colors
from data import *


def map(user_id, sequences):
    log.info("Drawing map for user %s..." % user_id)
    t = timeutil.timestamp()
    ctx = drawing.Context(1000, int(1000 / ratio), relative=True, flip=True, hsv=False)
    ctx.image("basemap/basemap.png")
    for sequence in sequences:
        for point in sequence:
            color = colors[ord(point.grid[-1]) % len(colors)]
            ctx.arc(point.x, point.y, 3 / ctx.width, 3 / ctx.height, fill=color, thickness=0.0)
    ctx.output("maps/%d_%d.png" % (t, user_id))
    log.info("--> done")


def strips(user_id, sequences):
    log.info("Drawing %d sequences for user %s..." % (len(sequences), user_id))
    t = timeutil.timestamp()
    ctx = drawing.Context(1000, len(sequences) * 2, relative=True, flip=False, hsv=False, background=(0., 0., 0., 1.))
    for q, sequence in enumerate(sequences):
        for p, point in enumerate(sequence):
            color = colors[ord(point.grid[-1]) % len(colors)]
            ctx.line(p/PERIODS, (q/len(sequences)) - (1 / ctx.height), (p+1)/PERIODS, (q/len(sequences)) - (1 / ctx.height), stroke=color, thickness=2.0)
    ctx.output("strips/%d_%d.png" % (t, user_id))


def sequence(sequence, suffix=None):
    t = timeutil.timestamp()    
    log.info("Drawing sequence...")
    ctx = drawing.Context(1000, int(1000 / ratio), relative=True, flip=True, hsv=True)
    ctx.image("basemap/basemap.png")
    grids = util.load("data/grids_%d_%d.pkl" % (config['grid'], config['periods']))
    if len(sequence) != PERIODS:
        log.error("--> bad sequence length")
        return
    for s, cell in enumerate(sequence):
        if s == len(sequence) - 1:
            continue
        x1, y1 = scale(geo.geohash_decode(grids[cell]))
        x2, y2 = scale(geo.geohash_decode(grids[sequence[s+1]]))
        c = s/PERIODS
        color = c, 1., 1., 0.75
        ctx.arc(x1, y1, 5 / ctx.width, 5 / ctx.height, fill=color, thickness=0.0)
        ctx.line(x1, y1, x2, y2, stroke=color, thickness=1.0)
    suffix = "_%s" % suffix if suffix is not None else ""
    ctx.output("sequences/%d%s.png" % (t, suffix))    
    log.info("--> done")


def scale(pt):
    x, y = geo.project(pt)
    x = (x - min_x) / (max_x - min_x)
    y = (y - min_y) / (max_y - min_y)
    return x, y


def gradient_test():
    ctx = drawing.Context(1000, 250, relative=True, flip=True, hsv=True)
    for x in range(PERIODS):
        # c = ((x/288) * 0.35) + .3
        # c = ((x/288) * 0.35) + .0
        c = ((x/PERIODS) * 0.65) + .0
        c = x/PERIODS
        ctx.line(x / PERIODS, 0, x / PERIODS, 1, stroke=(c, 1., 1., 1.), thickness=(ctx.width/PERIODS) + 1)
    ctx.output("gradient.png")


if __name__ == "__main__":
    gradient_test()