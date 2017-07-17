#!/usr/bin/env python3

import sys, random, datetime, json, math, json
import numpy as np
from housepy import geo, config, log, util, timeutil
import drawer

PERIODS = 144
LOCATION_SIZE = 7


def parse(data):
    days = data.split("000")
    d = 0
    while d < len(days):
        day = days[d]
        day = day.split(";")
        for l, location in enumerate(day):
            location = location.split(":")[-1]
            if not len(location):
                day[l] = None
                continue
            if len(location) != LOCATION_SIZE - 2:
                log.warning("Bad geohash: %s" % location)
                if l > 0:
                    day[l] = day[l-1]
                else:
                    day[l] = None
            else:
                day[l] = location
        day = [location for location in day if location is not None]
        if len(day) != PERIODS:    
            log.warning("Bad day length (%d)" % len(day))
            days[d] = None
        else:
            days[d] = day
        d += 1
    days = [day for day in days if day is not None]
    log.info("--> found %d valid days" % len(days))
    return days


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("[output]")
        exit()
    path = sys.argv[1]
    slug = path.split(".")[0].replace("output_", "")
    log.info("Loading generated output %s..." % path)
    with open("data/%s" % path) as f:
        data = f.read()    
    days = parse(data)
    if len(days):
        drawer.days(days, slug)
        drawer.map(days, slug)