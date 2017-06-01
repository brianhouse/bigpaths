#!/usr/bin/env python3

import sys
from housepy import config, log
from pymongo import MongoClient, GEOSPHERE, ASCENDING, DESCENDING

mongo = config['mongo']
client = MongoClient(mongo['host'], mongo['port'])
db = client[mongo['database']]

def make_indexes():
    db.entries.drop_indexes()
    try:
        db.entries.create_index("t")
        db.entries.create_index("user_id")
        db.entries.create_index([("location", GEOSPHERE)])
        db.entries.create_index([("location", GEOSPHERE), ("user_id", ASCENDING)])
        db.entries.create_index([("t", ASCENDING), ("user_id", ASCENDING)], unique=True)
    except Exception as e:
        log.error(log.exc(e))


if __name__ == "__main__":
    arg = None
    if len(sys.argv) > 1:
        arg = sys.argv[1]
    if arg == 'dump':
        result = db.entries.remove()
        print(result)
    elif arg == 'index':
        make_indexes()
    else:
        print("index|dump")
