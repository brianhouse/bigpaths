#!/usr/bin/env python3

import json, sys, os
from housepy import timeutil, log, strings
from geojson import Point
from mongo import db

FILENAME = ""

with open(FILENAME) as f:
    data = json.loads(f.read())
    for entry in data:
        try:
            entry['user_id'] = 1
            point = Point((entry['lon'], entry['lat'], entry['alt']))
            entry['location'] = point
            del entry['lon']
            del entry['lat']
            del entry['alt']
            print(json.dumps(entry, indent=4))
            db.entries.insert(entry)
        except Exception as e:
            log.exc(log.warning(e))

