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
for d, day in enumerate(days):
    day = day.split(";")
    valid = True
    for l, location in enumerate(day):
        if len(location) != LOCATION_SIZE - 2:
            log.warning("Bad geohash: %s" % location)
            if l > 0:
                day[l] = day[l-1]
            else:
                day[l] = None
    day = [location for location in day if location is not None]
    # if len(day) != PERIODS:
    #     log.warning("Bad day length (%d)" % len(day))
    #     valid = False        
    if not valid:
        days[d] = None
    else:
        days[d] = day
days = [day for day in days if day is not None]
log.info("--> found %d valid days" % len(days))
if len(days):
    drawer.days(days)
    drawer.map(days)