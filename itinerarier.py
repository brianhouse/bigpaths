#!/usr/bin/env python3

import random, sys, requests, json, time
import numpy as np
import drawer
from housepy import config, log, geo, timeutil
from interpreter import parse

random.seed(42)

LON_1, LAT_1 = config['bounds']['NW']
LON_2, LAT_2 = config['bounds']['SE']
MIN_X, MAX_Y = geo.project((LON_1, LAT_1))
MAX_X, MIN_Y = geo.project((LON_2, LAT_2))
RATIO = (MAX_X - MIN_X) / (MAX_Y - MIN_Y)

# careful: I've made some hardcoded assumptions about period length being 10 min

class Point():

    geohashes = {}
    addresses = {}

    def __init__(self, period, geohash):
        self.period = period
        if geohash in Point.geohashes:
            self.geohash = Point.geohashes[geohash]
        else:
            self.geohash = ["dr", geohash]
            # for i in range(9 - len(geohash) - 2): # if we approximated upstream, get it down here to a single building (geohash 9)
            #     self.geohash.append(random.choice("0123456789bcdefghjkmnpqrstuvwxyz"))
            self.geohash = str("".join(self.geohash))
            Point.geohashes[geohash] = self.geohash
        self.lon, self.lat = geo.geohash_decode(self.geohash)
        x, y = geo.project((self.lon, self.lat))
        self.x = (x - MIN_X) / (MAX_X - MIN_X)
        self.y = (y - MIN_Y) / (MAX_Y - MIN_Y) 
        self.address = self.degeocode()
        self.display_time = self.format_time()

    def degeocode(self):
        if self.geohash in Point.addresses:
            return Point.addresses[self.geohash]            
        try:
            url = "https://maps.googleapis.com/maps/api/geocode/json?latlng=%s,%s" % (self.lat, self.lon)
            result = requests.get(url).json()
            time.sleep(0.25)
            address = result['results'][0]['formatted_address']
            address = address.split(", NY ")[0].replace(", New York", "")
            log.debug(address)
            Point.addresses[self.geohash] = address
            return address
        except Exception as e:            
            log.error(log.exc(e))
            log.debug(json.dumps(result, indent=4))   

    def format_time(self):
        tod = timeutil.seconds_to_string(self.period * 10 * 60, show_seconds=False, pm=True).replace(" ", "")
        # if not (tod[3] == "0" or tod[3] == "3"):
        tod = tod[:4] + str(random.randint(0, 9)) + tod[5:]     # add some temporal detail
        return tod.lstrip("0")                 


def collapse(day):
    result = []
    for p in range(len(day)):
        if p == 0 or day[p].geohash != day[p-1].geohash:
            result.append(day[p])
    return result



def trim(day):      
    """adjust a "day" to more reasonable lived hours (4am shift instead of midnight) and trim the excess"""

    # chop off anything before 4am  
    start_d = 0
    while start_d < len(day) and day[start_d].period < 24:
        start_d += 1    
    start_d -= 1    
    log.debug("sleep %d %s" % (start_d, (day[start_d].period * 10) / 60))
    log.debug("start %d %s" % (start_d+1, (day[start_d+1].period * 10) / 60))

    # fast forward to the first point of the next clock day
    end_d = start_d
    while end_d < len(day) and day[end_d].period < day[end_d+1].period:
        end_d += 1
    end_d += 1
    log.debug("clock day ends %d %s" % (end_d, day[end_d].period))

    # if its still before 4am, advance
    while end_d < len(day) and day[end_d].period < 24:
        end_d += 1
    log.debug("human day ends %d %s" % (end_d, day[end_d].period))

    day = day[start_d:end_d]

    return day


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

    index = random.choice(range(len(days) - 1))
    log.info("INDEX: %s" % index)
    day = days[index] + days[index+1]
    day = [Point(period % 144, geohash) for (period, geohash) in enumerate(day)]
    day = collapse(day)
    for p, point in enumerate(day):
        log.debug("%d %s %s" % (p, (point.period * 10) / 60, point.address))
    day = trim(day)

    for p, point in enumerate(day):
        label = "%d) %s %s%s" % (p+1, "Wake up at" if p == 0 else "%s," % point.display_time, point.address, "" if p != (len(day) - 1) else " ... sleep")
        log.info(label)

    drawer.itinerary(day, slug, index)

