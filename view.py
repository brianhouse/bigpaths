#!/usr/bin/env python3

import random
from housepy import log, util, geo, drawing
from separate import draw_sequence

LON_1, LAT_1 = -74.053573, 40.919423
LON_2, LAT_2 = -73.699264, 40.538534
min_x, max_y = geo.project((LON_1, LAT_1))
max_x, min_y = geo.project((LON_2, LAT_2))
ratio = (max_x - min_x) / (max_y - min_y)


def draw_sequence(s, sequence):
    ctx = drawing.Context(1000, int(1000 / ratio), relative=True, flip=True, hsv=True)
    for p, point in enumerate(sequence[:-1]):
        x1, y1 = geo.project((point[0], point[1]))
        x2, y2 = geo.project((sequence[p+1][0], sequence[p+1][1]))
        x1 = (x1 - min_x) / (max_x - min_x)
        y1 = (y1 - min_y) / (max_y - min_y)
        x2 = (x2 - min_x) / (max_x - min_x)
        y2 = (y2 - min_y) / (max_y - min_y)
        c = ((p/288) * 0.65) + .0
        ctx.arc(x1, y1, 5 / ctx.width, 5 / ctx.height, fill=(c, 1., 1., .5), thickness=0.0)
        ctx.line(x1, y1, x2, y2, stroke=(c, 1., 1., 1.), thickness=5.0)        
    ctx.output("sequences/%d.png" % s, open_file=False)


log.info("Loading...")
sequences = util.load("sequences_50.pkl")
log.info("--> %d sequences" % len(sequences))

for i in range(100):
    index = random.choice(range(len(sequences)))
    sequence = sequences[index]
    draw_sequence(index, sequence)