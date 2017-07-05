#!/usr/bin/env python3

import random, datetime, json, math, requests, json
import numpy as np
from housepy import geo, config, log, util, timeutil
from mongo import db
import drawer


PERIOD_SIZE = config['period_size']
PERIODS = int(1440 / PERIOD_SIZE)
LOCATION_SIZE = config['location_size']
try:
    geohashes = util.load(config['locations'])
    LOCATIONS = len(geohashes)
except FileNotFoundError as e:
    log.warning(e)

LON_1, LAT_1 = config['bounds']['NW']
LON_2, LAT_2 = config['bounds']['SE']
MIN_X, MAX_Y = geo.project((LON_1, LAT_1))
MAX_X, MIN_Y = geo.project((LON_2, LAT_2))
RATIO = (MAX_X - MIN_X) / (MAX_Y - MIN_Y)


class Point():

    def __init__(self, lon, lat, t):
        self.lon = lon
        self.lat = lat
        x, y = geo.project((self.lon, self.lat))
        self.x = (x - MIN_X) / (MAX_X - MIN_X)
        self.y = (y - MIN_Y) / (MAX_Y - MIN_Y)
        self.t = t        
        self.geohash = geo.geohash_encode((self.lon, self.lat), precision=LOCATION_SIZE)
        self.location = None
        dt = timeutil.t_to_dt(self.t, tz="America/New_York")    # not sure why, honestly.        
        self.period = ((dt.hour * 60) + (dt.minute)) // PERIOD_SIZE
        self.address = None
        self.display_time = None

    def get_distance(self, pt):
        return geo.distance((self.lon, self.lat), (pt.lon, pt.lat))

    def geocode(self):
        try:
            url = "https://maps.googleapis.com/maps/api/geocode/json?latlng=%s,%s" % (self.lat, self.lon)
            result = requests.get(url).json()
            self.address = result['results'][0]['formatted_address']
            self.address = self.address.split(", NY ")[0].replace(", New York", "")
        except Exception as e:
            log.error(log.exc(e))
            log.debug(json.dumps(result, indent=4))

    def format_time(self):
        tod = timeutil.seconds_to_string(self.period * 10 * 60, show_seconds=False, pm=True).replace(" ", "")
        if not (tod[3] == "0" or tod[3] == "3"):
            tod = tod[:4] + str(random.randint(0, 9)) + tod[5:]
        self.display_time = tod.lstrip("0")

    def __str__(self):
        return "[%s] (%s)" % (self.location, self.period)



class GeneratedPoint(Point):

    def __init__(self, location, period, duration):
        self.location = location
        self.period = period
        self.duration = duration
        self.geohash = geohashes[self.location]
        self.unhash()
        x, y = geo.project((self.lon, self.lat))
        self.x = (x - MIN_X) / (MAX_X - MIN_X)
        self.y = (y - MIN_Y) / (MAX_Y - MIN_Y)   
        self.address = None
        self.display_time = None     

    def unhash(self):
        CHARMAP = "0123456789bcdefghjkmnpqrstuvwxyz"    # base32
        self.lon, self.lat = geo.geohash_decode("%s%s%s" % (self.geohash, CHARMAP[random.randint(0, len(CHARMAP) - 1)], CHARMAP[random.randint(0, len(CHARMAP) - 1)]))                



def get_user(user_ids):
    location = {'$geoWithin': {'$geometry': {'type': "Polygon", 'coordinates': [[ [LON_1, LAT_1], [LON_2, LAT_1], [LON_2, LAT_2], [LON_1, LAT_2], [LON_1, LAT_1] ]]}}}
    for u, user_id in enumerate(user_ids):
        log.info("USER %s..." % user_id)
        cursor = db.entries.find({'user_id': user_id, 'location': location, 't': {'$gt': timeutil.timestamp(timeutil.string_to_dt(config['start_date'], tz="America/New_York")), '$lt': timeutil.timestamp(timeutil.string_to_dt(config['stop_date'], tz="America/New_York"))}}).sort('t')
        points = [Point(point['location']['coordinates'][0], point['location']['coordinates'][1], point['t']) for point in cursor]
        log.info("--> %d points" % len(points))
        yield user_id, points
    yield (None, None)

def get_geohash_list(points):
    geohashes = [point.geohash for point in points]
    geohashes = list(set(geohashes))
    geohashes.sort()
    log.info("--> found %d locations" % len(geohashes))       
    return geohashes




def main(user_ids, draw=False):

    data = []

    for (user_id, points) in get_user(user_ids):        
        if points is None or not len(points):
            continue

        # generate location list
        geohashes = get_geohash_list(points)     
        for point in points:
            point.location = geohashes.index(point.geohash)     

        # distribute points to all periods
        days = []
        p = 0
        mod = 0
        while True:
            day = [None] * PERIODS
            for period in range(PERIODS):
                # take the most recent point in this period or earlier
                # if two locations are visited within PERIOD, the first is supressed (good)
                while points[p].period + mod <= period + (len(days) * PERIODS):
                    p += 1
                    if p == len(points):
                        break
                    if points[p].period < points[p-1].period:
                        mod += PERIODS
                if p == len(points):
                    break
                day[period] = points[p-1 if p > 0 else 0]
            if p == len(points):
                break
            days.append(day)
            output = " ".join([str(point.location) for point in day])
            print(output)
            print()

        if draw:
            drawer.days(days, user_id)

        log.info("--> total days for user %s: %d" % (user_id, len(days)))
        data += [point for day in days for point in day]


    # regenerate location labels globally
    geohashes = get_geohash_list(data)
    util.save("data/locations_%d_%d.pkl" % (PERIOD_SIZE, LOCATION_SIZE), geohashes)    
    log.info("Labeling...")
    for point in data:
        point.location = geohashes.index(point.geohash)         

    util.save("data/points_%d_%d.pkl" % (PERIOD_SIZE, LOCATION_SIZE), data)
    log.info("--> done")


if __name__ == "__main__":
    users = util.load(config['users'])
    main(users, True)
    # main([1], True)