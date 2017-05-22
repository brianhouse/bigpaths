#!/usr/bin/env python3

import random, datetime
import numpy as np
from bson.son import SON
from housepy import drawing, geo, config, log, util, timeutil
from mongo import db
from colors import colors
from geojson import Feature, Point
from separate import draw_points
from cluster_tree import ClusterTree

NPOINTS = 10

LON_1, LAT_1 = -74.053573, 40.919423
LON_2, LAT_2 = -73.699264, 40.538534
min_x, max_y = geo.project((LON_1, LAT_1))
max_x, min_y = geo.project((LON_2, LAT_2))
ratio = (max_x - min_x) / (max_y - min_y)

location = {'$geoWithin': {'$geometry': {'type': "Polygon", 'coordinates': [[ [LON_1, LAT_1], [LON_2, LAT_1], [LON_2, LAT_2], [LON_1, LAT_2], [LON_1, LAT_1] ]]}}}


def main():

    user_ids = util.load("user_ids.pkl")
    user_ids = [1]

    for u, user_id in enumerate(user_ids):
        
        log.info("USER %s..." % user_id)
        points = db.entries.find({'user_id': user_id, 'location': location}).sort('t')
        points = [(point['location']['coordinates'][0], point['location']['coordinates'][1], point['t']) for point in points]
        log.info("--> %d points" % len(points))

        # draw_points(user_id, points)

        # filter out (some) transient points (10mins matches QR)
        marks = []
        for p, point in enumerate(points):
            if p == 0 or p == len(points) - 1:
                continue
            prev = points[p-1]
            next = points[p+1]
            if point[-1] - prev[-1] < 10 * 60 and next[-1] - point[-1] < 10 * 60:
                marks.append(p)
        points = [point for (p, point) in enumerate(points) if p not in marks]

        draw_points(user_id, points)

        ct = ClusterTree.build(points, geo.distance)
        print("place clustertree:")
        print(ct.draw())
        clusters = ct.get_pruned(0.5)


if __name__ == "__main__":
    main()

