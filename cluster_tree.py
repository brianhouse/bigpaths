import time, math
import numpy as np
from collections import defaultdict
from housepy import log, geo
  
class ClusterTree(object):
    """Hierarchical agglomerative clustering"""

    @staticmethod
    def build(vectors, distance_f=geo.distance):  # use geo.distance for geography
        """Build a ClusterTree on the set of input vectors and a given distance function"""
        distance_f = distance_f
        vectors = vectors
        root = None        
        log.info("ClusterTree learning %d vectors..." % len(vectors))

        distances = {}
        current_cluster_id = -1

        # start with every feature in its own cluster
        cluster = [ClusterTree(vectors[i], id=i) for i in range(len(vectors))]

        while len(cluster) > 1:
            log.info("--> number of clusters remaining: %s" % len(cluster))

            # find the smallest distance between pairs            
            closest_pair = (0, 1)
            min_distance = distance_f(cluster[0].vector, cluster[1].vector)
            dists = 0
            for i in range(len(cluster)):
                for j in range(i + 1, len(cluster)):
                    # if (cluster[i].id, cluster[j].id) not in distances:     # cache calcs. how fast is this test?
                    #     distances[(cluster[i].id, cluster[j].id)] = distance_f(cluster[i].vector, cluster[j].vector)        
                    #     dists += 1
                    # d = distances[(cluster[i].id, cluster[j].id)]        
                    try:
                        d = distances[(cluster[i].id, cluster[j].id)]        
                    except KeyError:
                        d = distance_f(cluster[i].vector, cluster[j].vector)        
                        distances[(cluster[i].id, cluster[j].id)] = d   
                        dists += 1
                    if d < min_distance:
                        min_distance = d
                        closest_pair = (i, j)
            log.info("----> calculated %s distances" % dists) # after the first one, should be the same number as total clusters - 1
            ## so slow.

            # create new cluster with a merged vector that is the average between clusters
            average_vector = [(cluster[closest_pair[0]].vector[i] + cluster[closest_pair[1]].vector[i]) / 2.0 for i in range(len(cluster[0].vector))]
            new_cluster = ClusterTree(average_vector, id=current_cluster_id, left=cluster[closest_pair[0]], right=cluster[closest_pair[1]])
            current_cluster_id = current_cluster_id - 1

            # remove the clusters that have been agglomerated and add the new one to the cluster list
            del cluster[closest_pair[1]]
            del cluster[closest_pair[0]]
            cluster.append(new_cluster)

        # just one cluster remaining
        log.info("--> done. Calculating radii...")

        # radius is the furthest leaf node from a cluster's centroid
        ## this is really expensive (too expensive)        
        def calc_radii(master, cluster=None):               
            if cluster is None:
                master.radius_calculated = True        
                calc_radii(master, master)                
            elif cluster.id >= 0:
                # leaf
                d = distance_f(master.vector, cluster.vector)
                if d > master.radius:
                    master.radius = d                
            else:    
                # branches
                if cluster.left is not None: 
                    calc_radii(master, cluster.left)
                    if not cluster.left.radius_calculated:
                        calc_radii(cluster.left)
                if cluster.right is not None: 
                    calc_radii(master, cluster.right)
                    if not cluster.right.radius_calculated:                        
                        calc_radii(cluster.right)
        calc_radii(cluster[0], cluster[0])
        log.info("--> done")
        
        return cluster[0]

    def __init__(self, vector, id=None, left=None, right=None):
        self.left = left
        self.right = right
        self.vector = vector
        self.id = id
        self.radius = 0.0
        self.radius_calculated = False

    def get_order(self):
        """Return a list of indexes for how the input vectors are ordered in a depth first enumeration of the cluster, for ordering by likeness"""
        ids = self.get_leaf_ids()
        inverse = list(zip(list(range(len(ids))), ids))
        inverse.sort(key=lambda t: t[1])
        inverse, nop = list(zip(*inverse))    
        return inverse        

    def get_leaf_ids(self):
        """Perform a depth first listing of ids for elements"""
        if self.id >= 0:
            # leaf
            return [self.id]
        else:
            # branches
            left_branch = []
            right_branch = []
            if self.left is not None: 
                left_branch = self.left.get_leaf_ids()
            if self.right is not None: 
                right_branch = self.right.get_leaf_ids()
            return left_branch + right_branch  

    def get_pruned(self, max_radius):
        """Prune cluster until we have a set of sub-clusters with a maximum radius, return as a list of primary branches"""
        if self.radius <= max_radius:
            return [self]
        else:
            left_branch = []
            right_branch = []
            if self.left is not None:
                left_branch = self.left.get_pruned(max_radius)
            if self.right is not None:
                right_branch = self.right.get_pruned(max_radius)
            return left_branch + right_branch   
            
    def draw(self, n=0):
        """Indent to make a hierarchy layout"""
        ## I really want this to draw the complete lines
        output = []
        for i in range(n-1):
            # output.append("| ")
            output.append("  ")
        if n:   
            output.append("|\n") 
            for i in range(n-1):
                # output.append("| ")
                output.append("  ")
            output.append("|_")
        if self.id < 0:
            # negative id means that this is branch
            output.append("%f %s\n" % (self.radius, self.vector))
        else:
            # positive id means that this is an endpoint
            output.append("<%d> %s\n" % (self.id, self.vector))
        # now print the right and left branches
        if self.left != None:
            output.append(self.left.draw(n+1))
        if self.right != None:
            output.append(self.right.draw(n+1))
        output = "".join(output)    
        return output                             

    def __repr__(self):
        return "<Cluster %d %f %s>" % (self.id, self.radius, str(self.vector))        

