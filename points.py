#!/usr/bin/env python3

import random, datetime, json, math, requests, json
import numpy as np
from housepy import geo, config, log, util, timeutil
from mongo import db
from sklearn.cluster import Birch
import drawer


START_DATE = config['start_date']
STOP_DATE  = config['stop_date']

PERIOD_SIZE = config['period_size']
PERIODS = int(1440 / PERIOD_SIZE)
GRID_SIZE = config['grid_size']

LON_1, LAT_1 = config['bounds']['NW']
LON_2, LAT_2 = config['bounds']['SE']

MIN_X, MAX_Y = geo.project((LON_1, LAT_1))
MAX_X, MIN_Y = geo.project((LON_2, LAT_2))
RATIO = (MAX_X - MIN_X) / (MAX_Y - MIN_Y)
location = {'$geoWithin': {'$geometry': {'type': "Polygon", 'coordinates': [[ [LON_1, LAT_1], [LON_2, LAT_1], [LON_2, LAT_2], [LON_1, LAT_2], [LON_1, LAT_1] ]]}}}

try:
    locations = util.load(config['locations'])
    LOCATIONS = len(locations)
except FileNotFoundError as e:
    log.warning(e)

CHARMAP = "0123456789bcdefghjkmnpqrstuvwxyz"    # base32


class Point():

    def __init__(self, lon, lat, t):
        self.lon = lon
        self.lat = lat
        x, y = geo.project((self.lon, self.lat))
        self.x = (x - MIN_X) / (MAX_X - MIN_X)
        self.y = (y - MIN_Y) / (MAX_Y - MIN_Y)
        self.t = t        
        self.grid = geo.geohash_encode((self.lon, self.lat), precision=GRID_SIZE)
        self.location = None
        self.cluster = None
        dt = timeutil.t_to_dt(self.t, tz="America/New_York")    # not sure why, honestly.        
        self.period = ((dt.hour * 60) + (dt.minute)) // PERIOD_SIZE
        self.duration = None
        self.address = None
        self.display_time = None

    def distance(self, pt):
        return geo.distance((self.lon, self.lat), (pt.lon, pt.lat))

    def __str__(self):
        return "[%d] (%f,%f) %f,%f %d %d" % (self.location, self.lon, self.lat, self.x, self.y, self.period, self.duration)



class GeneratedPoint(Point):

    def __init__(self, location, period, duration):
        self.location = location
        self.period = period
        self.duration = duration
        self.grid = locations[self.location]
        self.unhash()
        x, y = geo.project((self.lon, self.lat))
        self.x = (x - MIN_X) / (MAX_X - MIN_X)
        self.y = (y - MIN_Y) / (MAX_Y - MIN_Y)   
        self.address = None
        self.display_time = None     

    def unhash(self):
        self.lon, self.lat = geo.geohash_decode("%s%s%s" % (self.grid, CHARMAP[random.randint(0, len(CHARMAP) - 1)], CHARMAP[random.randint(0, len(CHARMAP) - 1)]))                


def get_user(user_ids):
    for u, user_id in enumerate(user_ids):
        log.info("USER %s..." % user_id)
        cursor = db.entries.find({'user_id': user_id, 'location': location, 't': {'$gt': timeutil.timestamp(timeutil.string_to_dt(START_DATE, tz="America/New_York")), '$lt': timeutil.timestamp(timeutil.string_to_dt(STOP_DATE, tz="America/New_York"))}}).sort('t')
        points = [Point(point['location']['coordinates'][0], point['location']['coordinates'][1], point['t']) for point in cursor]
        log.info("--> %d points" % len(points))
        yield user_id, points
    yield (None, None)


def filter_transients(points):
    log.info("Filtering transients...")    
    # filter out transient points: greater than 1/20mi (1 city block) covered in 10mins on both sides
    # so in theory, if you run to the bodega nearby, that's still cool
    marks = []
    for p, point in enumerate(points):
        if p == 0 or p == len(points) - 1:
            continue
        prev, next = points[p-1], points[p+1]
        if point.t - prev.t <= 10 * 60 and next.t - point.t <= 10 * 60 and point.distance(prev) > 1/20 and point.distance(next) > 1/20:
            marks.append(p)
    points = [point for (p, point) in enumerate(points) if p not in marks]       
    log.info("--> removed %d transients" % len(marks))    
    return points


def join_adjacent(points):
    log.info("Joining like adjacent points...")
    a_points = []
    p = 0    
    while True:        
        point = points[p]
        a_points.append(point)
        q = p + 1
        while q < len(points) and points[q].grid == points[p].grid:
            q += 1
        p = q
        if p == len(points):
            break
    log.info("--> joined %d points" % (len(points) - len(a_points)))
    return a_points


def calculate_durations(points):
    log.info("Calculating durations (%d min)..." % PERIOD_SIZE)  
    for (p, point) in enumerate(points):
        if p == len(points) - 1:
            continue
        duration = points[p + 1].t - point.t
        duration //= 60
        duration //= PERIOD_SIZE
        if duration >= PERIODS:   # one day
            duration = PERIODS - 1
        point.duration = duration
    a_points = [point for point in points if point.duration is not None and point.duration > 0]        
    log.info("--> removed %d too short points" % (len(points) - len(a_points)))
    return a_points


def generate_locations(points):
    log.info("Generating location list...")    
    grids = [point.grid for point in points]
    grids = list(set(grids))
    grids.sort()
    util.save("data/locations_%d_%d.pkl" % (PERIOD_SIZE, GRID_SIZE), grids)
    log.info("--> found %d locations" % len(grids))
    return grids


def cluster(points):

    log.info("Clustering...")

    # find clusters within ~100ft
    ct = Birch(n_clusters=None, threshold=0.01)
    ct.fit(np.array([(point.x, point.y) for point in points]))
    centroids = ct.subcluster_centers_
    cluster_labels = ct.subcluster_labels_ # just consecutive
    labels = ct.labels_
    log.info("--> %d clusters" % len(centroids))    

    # get the size of each cluster
    cluster_sizes = [np.sum(labels == cluster_label) for cluster_label in cluster_labels]

    # get the order of clusters by size
    cluster_order = [(cluster_label, cluster_size) for (cluster_label, cluster_size) in enumerate(cluster_sizes)]
    cluster_order.sort(key=lambda x: x[1], reverse=True)
    cluster_order = [c[0] for c in cluster_order]
    cluster_order = [cluster_order.index(cluster_label) for cluster_label in cluster_labels]

    # store clusters
    clusters = {}
    for c, cluster_label in enumerate(cluster_labels):
        clusters[cluster_label] = cluster_order[c]

    for p, point in enumerate(points):
        point.cluster = clusters[labels[p]]


def geocode(points):
    log.info("Geocoding %d points..." % len(points))
    for point in points:
        try:
            url = "https://maps.googleapis.com/maps/api/geocode/json?latlng=%s,%s" % (point.lat, point.lon)
            result = requests.get(url).json()
            point.address = result['results'][0]['formatted_address']
            point.address = point.address.split(", NY ")[0].replace(", New York", "")
            # log.debug(point.address)
        except Exception as e:
            log.error(log.exc(e))
            log.debug(json.dumps(result, indent=4))
    log.info("--> done")
    return points


def format_times(points):
    for point in points:
        tod = timeutil.seconds_to_string(point.period * 10 * 60, show_seconds=False, pm=True).replace(" ", "")
        if not (tod[3] == "0" or tod[3] == "3"):
            tod = tod[:4] + str(random.randint(0, 9)) + tod[5:]
        point.display_time = tod.lstrip("0")
    return points


def main(user_ids, draw=False):

    data = []

    for (user_id, points) in get_user(user_ids):        
        if points is None or not len(points):
            continue

        try:
            points = filter_transients(points)     
            points = join_adjacent(points)
            points = calculate_durations(points)
            # cluster(points)
            locations = generate_locations(points)

            log.info("Labeling...")
            for point in points:
                point.location = locations.index(point.grid)     

            if draw:
                drawer.map(points, user_id)
                drawer.strips(points, user_id)

            log.info("--> total points for user %s: %d" % (user_id, len(points)))
            data = data + points
        except Exception as e:
            log.error(log.exc(e))
            continue

    # regenerate labels globally
    locations = generate_locations(data)
    log.info("Labeling...")
    for point in data:
        point.location = locations.index(point.grid)         

    util.save("data/points_%d_%d.pkl" % (PERIOD_SIZE, GRID_SIZE), data)
    log.info("--> done")


if __name__ == "__main__":
    users = util.load(config['users'])
    main(users, False)