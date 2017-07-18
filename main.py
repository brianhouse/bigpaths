#!/usr/bin/env python3

import subprocess, os, sys, datetime, urllib.parse, random
from housepy import config, log, timeutil, geo, server, jobs
from itinerarier import Point


class Home(server.Handler):

    def get(self, lonlat=None):
        if lonlat is None or not len(lonlat):
            return self.text("OK")
        try:
            log.debug(lonlat)
            lonlat = lonlat.split(',')
            lonlat.reverse()
            lonlat = [float(coord.strip()) for coord in lonlat]
            current_geohash = [geo.geohash_encode(lonlat)]
            for i in range(8 - len(current_geohash[0])):
                current_geohash.append(random.choice("0123456789bcdefghjkmnpqrstuvwxyz"))            
            current_geohash = str("".join(current_geohash)).lstrip('dr')                
            dt = timeutil.t_to_dt(tz="America/New_York")
            current_period = ((dt.hour * 60) + (dt.minute)) // 10
            log.info("Current geohash: %s" % current_geohash)
            log.info("Current period: %d" % current_period)
            seed = "".join(["%s:%s;" % (current_period - (2 - i), current_geohash) for i in range(3)])
            log.info("Seed: %s" % seed)        
        except Exception as e:
            log.error(log.exc(e))
        return self.text("OK")

handlers = [
    (r"/?([^/]*)", Home),
]    


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("[model]")
        exit()
    slug = sys.argv[1].split('/')[-1].split('.')[0]
    log.info("--> using model %s" % slug)
    root = os.path.abspath(os.path.dirname(__file__))
    jobs.launch_beanstalkd()
    server.start(handlers)
