#!/usr/bin/env python3

import random, datetime, json, math
import numpy as np
from housepy import geo, config, log, util, timeutil
from mongo import db
from sklearn.cluster import Birch


START_DATE = config['start_date']
STOP_DATE  = config['stop_date']

PERIODS = config['periods']

LON_1, LAT_1 = config['bounds']['NW']
LON_2, LAT_2 = config['bounds']['SE']

min_x, max_y = geo.project((LON_1, LAT_1))
max_x, min_y = geo.project((LON_2, LAT_2))
ratio = (max_x - min_x) / (max_y - min_y)
location = {'$geoWithin': {'$geometry': {'type': "Polygon", 'coordinates': [[ [LON_1, LAT_1], [LON_2, LAT_1], [LON_2, LAT_2], [LON_1, LAT_2], [LON_1, LAT_1] ]]}}}

try:
    grids = util.load("data/grids_alt_%d_%d.pkl" % (config['grid'], config['periods']))
    GRIDS = len(grids)
except FileNotFoundError as e:
    log.warning(e)


class Point():

    def __init__(self, lon, lat, t):
        self.lon = lon
        self.lat = lat
        x, y = geo.project((self.lon, self.lat))
        self.x = (x - min_x) / (max_x - min_x)
        self.y = (y - min_y) / (max_y - min_y)
        self.t = t
        self.duration = None
        self.grid = geo.geohash_encode((self.lon, self.lat), precision=config['grid'])
        self.label = None
        self.cluster = None

    def distance(self, pt):
        return geo.distance((self.lon, self.lat), (pt.lon, pt.lat))


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
    log.info("Calculating durations...")    
    for (p, point) in enumerate(points):
        if p == len(points) - 1:
            continue
        duration = points[p + 1].t - point.t
        duration //= 60
        duration //= math.floor(86400 / 60 / PERIODS)
        if duration > PERIODS:
            duration = PERIODS
        # print(points[p + 1].t - point.t, duration)
        point.duration = duration
    a_points = [point for point in points if point.duration is not None and point.duration > 0]        
    log.info("--> removed %d too short points" % (len(points) - len(a_points)))
    return a_points


def generate_grid_list(points):
    log.info("Generating grid list...")    
    grids = [point.grid for point in points]
    grids = list(set(grids))
    grids.sort()
    util.save("data/grids_%d_%d.pkl" % (config['grid'], config['periods']), grids)
    log.info("--> found grids: %s" % [grids])
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


