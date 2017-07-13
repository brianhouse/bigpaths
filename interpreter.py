#!/usr/bin/env python3

import sys, random, datetime, json, math, json
import numpy as np
from housepy import geo, config, log, util, timeutil
import drawer

PERIODS = 72
LOCATION_SIZE = 6

if len(sys.argv) != 2:
    print("[generated output]")
    exit()
path = sys.argv[1]
log.info("Loading generated output %s..." % path)
with open("data/%s" % path) as f:
    data = f.read()

days = data.split(".")
d = 0
while d < len(days):
    day = days[d]
    day = day.split(";")
    for l, location in enumerate(day):
        if len(location) != LOCATION_SIZE - 2:
            log.warning("Bad geohash: %s" % location)
            if l > 0:
                day[l] = day[l-1]
            else:
                day[l] = None
    day = [location for location in day if location is not None]
    # if len(day) > PERIODS:
    #     days[d] = day[:PERIODS]
    #     days.insert(d + 1, ";".join(day[PERIODS:]))
    # elif len(day) != PERIODS:
    if len(day) != PERIODS:    
        log.warning("Bad day length (%d)" % len(day))
        days[d] = None
    else:
        days[d] = day
    d += 1
days = [day for day in days if day is not None]
log.info("--> found %d valid days" % len(days))
if len(days):
    drawer.days(days)
    drawer.map(days)