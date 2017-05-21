#!/usr/bin/env python3

import json, sys, os
from housepy import timeutil, log, strings
from geojson import Point
from mongo import db

try:
    FILENAME = os.path.join("..", "data", "w_id", sys.argv[1])
except IndexError:
    print("[PATH]")
    exit()

fields = []
data = []
with open(FILENAME) as f:
    for l, line in enumerate(f):
        try:
            line = line.strip()
            if not len(line):
                continue
            line = line.split(',')
            if l == 0:
                fields = line
                continue
            line = [strings.as_numeric(field.strip('"')) for field in line]
            entry = dict(zip(fields, line))
            del entry['uid']
            entry['user_id'] = entry['i']
            del entry['i']
            point = Point((entry['lon'], entry['lat'], entry['alt']))
            entry['location'] = point
            del entry['lon']
            del entry['lat']
            del entry['alt']
            dt = timeutil.string_to_dt(entry['date'])
            entry['t'] = timeutil.timestamp(dt)
            print(json.dumps(entry, indent=4))
            db.entries.insert(entry)
        except Exception as e:
            log.exc(log.warning(e))


## NOTE: this all ends up labeling all local times as UTC without conversion