#!/usr/bin/env python3

import random, datetime
import numpy as np
from housepy import drawing, geo, config, log, util, timeutil
from mongo import db
from colors import colors
from geojson import Feature, Point

ctx = drawing.Context(1000, 250, relative=True, flip=True, hsv=True)

for x in range(288):
    c = ((x/288) * 0.35) + .3
    c = ((x/288) * 0.65) + .0
    ctx.line(x / 288, 0, x / 288, 1, stroke=(c, 1., 1., .5), thickness=7)


ctx.output("gradient.png")