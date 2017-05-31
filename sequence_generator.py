#!/usr/bin/env python3

import random, datetime, json
import numpy as np
from housepy import drawing, geo, config, log, util, timeutil
from mongo import db
from colors import colors
from sklearn.cluster import Birch

LON_1, LAT_1 = -74.053573, 40.919423
LON_2, LAT_2 = -73.699264, 40.538534
min_x, max_y = geo.project((LON_1, LAT_1))
max_x, min_y = geo.project((LON_2, LAT_2))
ratio = (max_x - min_x) / (max_y - min_y)
location = {'$geoWithin': {'$geometry': {'type': "Polygon", 'coordinates': [[ [LON_1, LAT_1], [LON_2, LAT_1], [LON_2, LAT_2], [LON_1, LAT_2], [LON_1, LAT_1] ]]}}}


def main():

    user_ids = util.load("user_ids.pkl")
    user_ids = [1]  # me

    for u, user_id in enumerate(user_ids):

        if u == 1:
            break

        sequences = []
        
        # retrieve all user points
        log.info("USER %s..." % user_id)
        points = db.entries.find({'user_id': user_id, 'location': location}).sort('t')
        # points = db.entries.find({'user_id': user_id, 'location': location, 't': {'$gt': 1293840000, '$lt': 1325289600}}).sort('t')
        def scale(lon, lat):
            x, y = geo.project((lon, lat))
            x = (x - min_x) / (max_x - min_x)
            y = (y - min_y) / (max_y - min_y)
            return x, y            
        points = [(*scale(point['location']['coordinates'][0], point['location']['coordinates'][1]), point['t']) for point in points]
        log.info("--> %d points" % len(points))

        # filter out transient points: greater than 1/20mi (1 city block) covered in 10mins on both sides
        # so in theory, if you run to the bodega nearby, that's still cool
        marks = []
        for p, point in enumerate(points):
            if p == 0 or p == len(points) - 1:
                continue
            prev = points[p-1]
            next = points[p+1]
            if point[-1] - prev[-1] <= 10 * 60 and next[-1] - point[-1] <= 10 * 60 and geo.distance(point, prev) > 1/20 and geo.distance(point, next) > 1/20:
                marks.append(p)
        log.info("--> marked %d transients" % len(marks))
        transients = [point for (p, point) in enumerate(points) if p in marks]
        points = [point for (p, point) in enumerate(points) if p not in marks]        

        # find clusters within ~100ft
        ct = Birch(n_clusters=None, threshold=0.01)
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
        draw_points(user_id, points, labels, clusters)

        # -- get 255 step daily sequences of clusters (identified by frequency) -- #

        # get our start and stop
        start_t = points[0][-1]
        stop_t = points[-1][-1]
        start_dt = timeutil.t_to_dt(start_t, tz="America/New_York")  ## why.
        stop_dt = timeutil.t_to_dt(stop_t, tz="America/New_York")
        delta = stop_dt - start_dt
        log.info("--> start_t %d %s" % (start_t, timeutil.t_to_string(start_t)))
        log.info("--> stop_t  %d %s" % (stop_t, timeutil.t_to_string(stop_t)))
        log.info("--> %s" % delta)

        # iterate through days
        day = start_dt.replace(hour=0, minute=0, second=0) + datetime.timedelta(days=1)
        current_cluster = None
        while day < stop_dt - datetime.timedelta(days=1):
            d_start_t = timeutil.timestamp(day)
            day += datetime.timedelta(days=1)
            d_stop_t = timeutil.timestamp(day)

            # get point and index for this day
            day_points = [(point, p) for (p, point) in enumerate(points) if point[-1] >= d_start_t and point[-1] < d_stop_t]
            day_transients = [(point, p) for (p, point) in enumerate(transients) if point[-1] >= d_start_t and point[-1] < d_stop_t]
            if len(day_points) == 0:
                continue

            # get the daily period for each of these points
            def get_periods(points):            
                periods = np.array([point[0][-1] for point in points])
                periods -= d_start_t
                periods //= 60
                periods //= 5
                periods = list(periods)
                return periods

            point_periods = get_periods(day_points)
            transient_periods = get_periods(day_transients)

            # add the order index of the cluster of this point to the sequence
            sequence = []
            for i in range(288):
                if i in point_periods:
                    point_index = day_points[point_periods.index(i)][1]
                    current_cluster = cluster_order[cluster_labels[labels[point_index]]]                    
                elif i in transient_periods:    # prioritize the destination
                    current_cluster = None
                sequence.append(current_cluster)                    
            sequences.append(sequence)

        log.info("--> generated %s sequences" % len(sequences))
        draw_strips(user_id, sequences)
        log.info("--> done")


def draw_points(user_id, points, labels, clusters):
    log.info("Drawing clusters for user %s..." % user_id)
    t = timeutil.timestamp()
    ctx = drawing.Context(10000, int(10000 / ratio), relative=True, flip=True, hsv=False)
    ctx.image("basemap/basemap.png")
    for p, point in enumerate(points):
        x, y = point[:2]
        centroid, cluster = clusters[labels[p]]
        cx, cy = centroid[:2]
        c = colors[cluster % len(colors)]
        ctx.line(x, y, cx, cy, stroke=.5, thickness=0.5)
        ctx.arc(x, y, 3 / ctx.width, 3 / ctx.height, fill=c, thickness=0.0)
    ctx.output("clusters/%d_%d.png" % (t, user_id))


def draw_strips(user_id, sequences):
    t = timeutil.timestamp()
    log.info("Drawing %d sequences for user %s..." % (len(sequences), user_id))
    ctx = drawing.Context(1000, len(sequences), relative=True, flip=True, hsv=False, background=(0., 0., 0., 1.))
    for q, sequence in enumerate(sequences):
        for p, cluster in enumerate(sequence):
            if cluster is None:
                continue
            color = colors[cluster % len(colors)]
            ctx.line(p/288, q/len(sequences), (p+1)/288, q/len(sequences), stroke=color, thickness=2)
    ctx.output("strips/%d_%d.png" % (t, user_id))


if __name__ == "__main__":
    main()
