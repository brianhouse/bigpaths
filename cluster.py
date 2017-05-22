#!/usr/bin/env python3

import random, datetime
import numpy as np
from housepy import drawing, geo, config, log, util, timeutil
from mongo import db
from colors import colors
from cluster_tree import ClusterTree
from sklearn.cluster import AgglomerativeClustering

NPOINTS = 10

LON_1, LAT_1 = -74.053573, 40.919423
LON_2, LAT_2 = -73.699264, 40.538534
min_x, max_y = geo.project((LON_1, LAT_1))
max_x, min_y = geo.project((LON_2, LAT_2))
ratio = (max_x - min_x) / (max_y - min_y)

location = {'$geoWithin': {'$geometry': {'type': "Polygon", 'coordinates': [[ [LON_1, LAT_1], [LON_2, LAT_1], [LON_2, LAT_2], [LON_1, LAT_2], [LON_1, LAT_1] ]]}}}


def draw_points(user_id, points, labels):
    log.info("DRAWING POINTS FOR USER %s" % user_id)
    t = timeutil.timestamp()
    ctx = drawing.Context(1000, int(1000 / ratio), relative=True, flip=True, hsv=True)
    for p, point in enumerate(points):
        x, y = geo.project((point[0], point[1]))
        x = (x - min_x) / (max_x - min_x)
        y = (y - min_y) / (max_y - min_y)
        c = labels[p] / 10, 1., 1., 1.
        ctx.arc(x, y, 3 / ctx.width, 3 / ctx.height, fill=c, thickness=0.0)
    ctx.output("users/%d_%d.png" % (t, user_id))


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
        points = [(point[0], point[1]) for (p, point) in enumerate(points) if p not in marks]
        points = np.array(points)


        ct = AgglomerativeClustering(n_clusters=20)
        labels = ct.fit_predict(points, points.shape)
        draw_points(user_id, points, labels)

        exit()

        # print("place clustertree:")
        # print(ct.draw())
        # clusters = ct.get_pruned(0.5)   # does this suggest a half-mile radius?


        cluster_points = [cluster.vector for (c, cluster) in enumerate(clusters)]

        # label in terms of frequency

        # now we separate into days

if __name__ == "__main__":
    main()

