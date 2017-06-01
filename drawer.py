from housepy import drawing
from colors import colors
from data import *


def map(user_id, points):
    log.info("Drawing map for user %s..." % user_id)
    t = timeutil.timestamp()
    ctx = drawing.Context(1000, int(1000 / ratio), relative=True, flip=True, hsv=False)
    ctx.image("basemap/basemap.png")
    for point in points:
        color = colors[point.cluster % len(colors)]
        ctx.arc(point.x, point.y, 3 / ctx.width, 3 / ctx.height, fill=color, thickness=0.0)
    ctx.output("maps/%d_%d.png" % (t, user_id))


def strips(user_id, sequences):
    t = timeutil.timestamp()
    log.info("Drawing %d sequences for user %s..." % (len(sequences), user_id))
    ctx = drawing.Context(1000, len(sequences) * 2, relative=True, flip=False, hsv=False, background=(0., 0., 0., 1.))
    for q, sequence in enumerate(sequences):
        for p, point in enumerate(sequence):
            if point is None:
                continue
            color = colors[point.cluster % len(colors)]
            ctx.line(p/PERIODS, (q/len(sequences)) - (1 / ctx.height), (p+1)/PERIODS, (q/len(sequences)) - (1 / ctx.height), stroke=color, thickness=2.0)
    ctx.output("strips/%d_%d.png" % (t, user_id))
