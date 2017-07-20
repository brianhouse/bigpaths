#!/usr/bin/env python3

import subprocess, os, sys, datetime, urllib.parse, random, markdown
from housepy import config, log, timeutil, geo, server, jobs, process
from itinerarier import Point

process.secure_pid(os.path.abspath(os.path.join(os.path.dirname(__file__), "run")))

class Home(server.Handler):

    def get(self, lonlat=None):
        if lonlat is None or not len(lonlat):
            try:
                with open(os.path.abspath(os.path.join(os.path.dirname(__file__), "templates", "home.md"))) as f:
                    text = f.read()
                    readme = markdown.markdown(text)
            except Exception as e:
                log.error(log.exc(e))
            return self.render("index.html", readme=readme)
        try:
            log.debug(lonlat)
            lonlat = lonlat.split(',')
            lonlat.reverse()
            lonlat = [float(coord.strip()) for coord in lonlat]
            current_geohash = geo.geohash_encode(lonlat, 8)
            log.info("Got location: %s" % current_geohash)
            job_id = str(random.randint(0, 1000000))
            self.jobs.add(tube="generate", data={'job_id': job_id, 'geohash': current_geohash})
            log.info("Sent job, waiting for generator (%s)..." % job_id) 
            result = []
            def on_job(data):
                log.info("--> got %s" % data['job_id'])
                if data['job_id'] == job_id:
                    result.append(data['point'])            
            while not len(result):
                self.jobs.process(handler=on_job, tube="receive", num_jobs=1)    
            point = result.pop()                
            log.info("--> %s" % point.address)                                
            text = "%s*%s" % (point.address, point.display_time)
            return self.text(text)
        except Exception as e:
            log.error(log.exc(e))
        return self.text("OK")

handlers = [
    (r"/?([^/]*)", Home),
]    

server.start(handlers)
