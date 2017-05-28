#!/usr/bin/env python3

import random, datetime, json
import numpy as np
from housepy import drawing, geo, config, log, util, timeutil
from mongo import db
from colors import colors
from sklearn.cluster import AgglomerativeClustering
from sklearn.cluster import DBSCAN, Birch

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

        sequences = []
        
        # retrieve all user points
        log.info("USER %s..." % user_id)
        # points = db.entries.find({'user_id': user_id, 'location': location}).sort('t')
        points = db.entries.find({'user_id': user_id, 'location': location, 't': {'$gt': 1293840000, '$lt': 1325289600}}).sort('t')
        points = [(point['location']['coordinates'][0], point['location']['coordinates'][1], point['t']) for point in points]
        log.info("--> %d points" % len(points))

        # filter out transient points: greater than 1/20mi (1 city block) covered in 10mins on both sides
        # in theory, if you run to the bodega nearby, that's still cool
        marks = []
        for p, point in enumerate(points):
            if p == 0 or p == len(points) - 1:
                continue
            prev = points[p-1]
            next = points[p+1]
            if point[-1] - prev[-1] <= 10 * 60 and next[-1] - point[-1] <= 10 * 60 and geo.distance(point, prev) > 1/20 and geo.distance(point, next) > 1/20:
                marks.append(p)
        log.info("--> removed %d transients" % len(marks))
        # points = [(point[0], point[1]) for (p, point) in enumerate(points) if p not in marks]
        points = [point for (p, point) in enumerate(points) if p not in marks]

        ## need to keep transients somehow

        # find clusters within ~100ft
        ct = Birch(n_clusters=None, threshold=0.01)   ## calculate this (used .5mi)
        ct.fit(np.array([(point[0], point[1]) for point in points]))
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

        # draw clusters
        clusters = {}
        for c, cluster_label in enumerate(cluster_labels):
            clusters[cluster_label] = centroids[c], cluster_order[c]
        # draw_points(user_id, points, labels, clusters)

        # -- get 255 step daily sequences of clusters (identified by frequency) -- #

        # get our start and stop
        start_t = points[0][-1]
        stop_t = points[-1][-1]
        start_dt = timeutil.t_to_dt(start_t)
        stop_dt = timeutil.t_to_dt(stop_t)
        delta = stop_dt - start_dt
        log.info("--> start_t %d %s" % (start_t, timeutil.t_to_string(start_t, tz='UTC')))
        log.info("--> stop_t  %d %s" % (stop_t, timeutil.t_to_string(stop_t, tz='UTC')))
        log.info("--> %s" % delta)

        # iterate through days
        day = start_dt.replace(hour=0, minute=0, second=0) + datetime.timedelta(days=1)
        while day < stop_dt - datetime.timedelta(days=1):
            d_start_t = timeutil.timestamp(day)
            day += datetime.timedelta(days=1)
            d_stop_t = timeutil.timestamp(day)

            # get point and index for this day
            day_points = [(point, p) for (p, point) in enumerate(points) if point[-1] >= d_start_t and point[-1] < d_stop_t]
            # if len(day_points) <= 10:
            #     continue

            # get the daily period for each of these points
            periods = np.array([point[0][-1] for point in day_points])
            periods -= d_start_t
            periods //= 60
            periods //= 5
            periods = list(periods)

            # add the order index of the cluster of the label of this point to the sequence
            sequence = []
            current = None
            for i in range(288):
                if i in periods:
                    point_index = day_points[periods.index(i)][1]
                    point = points[point_index]
                    label = labels[point_index]
                    cluster_index = cluster_labels[label]
                    current = cluster_order[cluster_index], point
                sequence.append(current)
            # draw_sequences(user_id, [sequence], len(sequences))
            # draw_strips(user_id, [sequence], len(sequences))
            sequences.append(sequence)

        log.info("--> generated %s sequences" % len(sequences))
        draw_sequences(user_id, sequences)        
        draw_strips(user_id, sequences)


def draw_points(user_id, points, labels, clusters):
    log.info("DRAWING POINTS FOR USER %s" % user_id)
    t = timeutil.timestamp()
    ctx = drawing.Context(1000, int(1000 / ratio), relative=True, flip=True, hsv=False)
    for p, point in enumerate(points):

        x, y = geo.project((point[0], point[1]))
        x = (x - min_x) / (max_x - min_x)
        y = (y - min_y) / (max_y - min_y)

        centroid, order = clusters[labels[p]]
        cx, cy = geo.project((centroid[0], centroid[1]))
        cx = (cx - min_x) / (max_x - min_x)
        cy = (cy - min_y) / (max_y - min_y)

        c = colors[order % len(colors)]

        ctx.line(x, y, cx, cy, stroke=.5, thickness=0.5)
        ctx.arc(x, y, 3 / ctx.width, 3 / ctx.height, fill=c, thickness=0.0)

    ctx.output("users/%d_%d.png" % (t, user_id))


def draw_sequences(user_id, sequences, s=None):
    t = timeutil.timestamp()
    ctx = drawing.Context(1000, int(1000 / ratio), relative=True, flip=True, hsv=True)
    for sequence in sequences:
        for p, point in enumerate(sequence):
            if point is None:
                continue
            point = point[-1]
            x1, y1 = geo.project((point[0], point[1]))
            x1 = (x1 - min_x) / (max_x - min_x)
            y1 = (y1 - min_y) / (max_y - min_y)
            c = ((p/288) * 0.65) + .0
            ctx.arc(x1, y1, 5 / ctx.width, 5 / ctx.height, fill=(c, 1., 1., .5), thickness=0.0)
    if s is not None:
        ctx.output("users/%d_s%d_%d.png" % (t, s, user_id), open_file=True)
    else:
        ctx.output("users/%d_%d.png" % (t, user_id), open_file=True)


def draw_strips(user_id, sequences, s=None):
    t = timeutil.timestamp()
    log.info("Drawing %d sequences..." % len(sequences))
    ctx = drawing.Context(1000, len(sequences) * 4, relative=True, flip=True, hsv=True)
    for q, sequence in enumerate(sequences):
        for p, period in enumerate(sequence):
            if period is None:
                continue
            color = colors[period[0] % len(colors)]
            ctx.line(p/288, q/len(sequences), (p+1)/288, q/len(sequences), stroke=color, thickness=4)
    if s is not None:
        ctx.output("users/%d_s%d_%d.png" % (t, s, user_id), open_file=True)
    else:
        ctx.output("users/%d_%d.png" % (t, user_id), open_file=True)


if __name__ == "__main__":
    main()
