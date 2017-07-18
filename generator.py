#!/usr/bin/env python3

import subprocess, os, sys, datetime, urllib.parse
from housepy import config, log, timeutil, geo
from itinerarier import Point

if __name__ == "__main__":
if len(sys.argv) != 2:
    print("[model]")
    exit()

slug = sys.argv[1].split('/')[-1].split('.')[0]
log.info("--> using model %s" % slug)
root = os.path.abspath(os.path.dirname(__file__))

current_geohash = "5rkjzk"
dt = timeutil.t_to_dt(tz="America/New_York")
current_period = ((dt.hour * 60) + (dt.minute)) // 10
log.info("Current geohash: %s" % current_geohash)
log.info("Current period: %d" % current_period)
seed = "".join(["%s:%s;" % (current_period - (2 - i), current_geohash) for i in range(3)])



def generate(seed):

    log.info("Seed: %s" % seed)
    log.info("Generating output...")
    p = subprocess.run(["th", "sample.lua", 
                    "-checkpoint", os.path.join(root, "data", "%s.t7" % slug),
                    "-length", str((3 + 1 + 6 + 1) * 144),  # next 24 hours
                    "-gpu", "0" if config['gpu'] else "-1",
                    "-start_text", seed
                    ], 
                    cwd=config['torch-rnn'],
                    stdout=subprocess.PIPE
                    )
    log.info("--> done")
    result = str(p.stdout.decode())
    result = result.replace(seed, "")

    tokens = result.split(';')
    points = [token.split(':') for token in tokens]
    points = [Point(int(point[0]), point[1], False) for point in points if len(point) == 2 and len(point[1]) == 6]

    i = 0
    while i < len(points) - 1 and points[i].geohash == "dr" + current_geohash:
        i += 1
    point = points[i]
    point.resolve()

    return point

    result = "Next location: %s at %s" % (point.address, point.display_time)
    print(result)
    print(point.lat, point.lon)

    link = "https://www.google.com/maps/place/" + str(urllib.parse.quote(point.address))
    print(link)

