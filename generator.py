#!/usr/bin/env python3

import subprocess, os, sys, datetime, urllib.parse
from housepy import config, log, timeutil, geo
from itinerarier import Point

def generate(geohash):
    try:
        log.info(geohash)
        current_geohash = geohash.lstrip('dr')
        dt = timeutil.t_to_dt(tz="America/New_York")
        current_period = ((dt.hour * 60) + (dt.minute)) // 10
        log.info("Current geohash: %s" % current_geohash)
        log.info("Current period: %d" % current_period)
        seed = "".join(["%s:%s;" % (current_period - (2 - i), current_geohash) for i in range(3)])        
        log.info("Seed: %s" % seed)
        log.info("Generating output...")
        p = subprocess.run([config['torch-bin'], "sample.lua", 
                        "-checkpoint", os.path.join(root, "data", "%s.t7" % slug),
                        "-length", str((3 + 1 + 6 + 1) * 144),  # next 24 hours
                        "-gpu", "0" if config['gpu'] else "-1",
                        "-start_text", seed
                        ], 
                        cwd=config['torch-rnn'],
                        stdout=subprocess.PIPE
                        )
        log.info("--> done")
        result = str(p.stdout.decode())
        result = result.replace(seed, "")

        tokens = result.split(';')
        points = [token.split(':') for token in tokens]
        points = [Point(int(point[0]), point[1], False) for point in points if len(point) == 2 and len(point[1]) == 6]

        i = 0
        while i < len(points) - 1 and points[i].geohash[:-1] == "dr" + current_geohash[:-1]:
            i += 1
        point = points[i]
        log.info("--> %s" % point.geohash)
        point.resolve()

        return point
    except Exception as e:
        log.error(log.exc(e))
        return None


if __name__ == "__main__":
    if 'model' in config:
        model_path = config['model']            
    else:    
        if len(sys.argv) < 2:
            print("[model] [geohash]")
            exit()
        model_path = sys.argv[1]

    slug = model_path.split('/')[-1].split('.')[0]
    log.info("--> using model %s" % slug)
    root = os.path.abspath(os.path.dirname(__file__))

    if len(sys.argv) == 3:
        point = generate(sys.argv[2])
        if point is not None:
            result = "Next location: %s at %s" % (point.address, point.display_time)
            log.debug(result)
            log.debug("%s,%s" % (point.lat, point.lon))
            link = "https://www.google.com/maps/place/" + str(urllib.parse.quote(point.address))
            log.debug(link)

    else:
        log.info("--> job process mode")
        from housepy import jobs
        jobs.launch_beanstalkd()
        jobs = jobs.Jobs()
        def on_job(data):
            point = generate(data['geohash'])
            log.info("%s %s" % (point.display_time, point.address))
            jobs.add(data={'job_id': data['job_id'], 'point': point}, tube="receive")
            return True
        jobs.process(handler=on_job, tube="generate")


# ./generator.py 1500327721_model_b16_s60.t7 dr5rkjzk
