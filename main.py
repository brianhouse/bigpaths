#!/usr/bin/env python3

from mongo import db

user_id = 8134

result = db.entries.find({'properties.user_id': user_id})

print(result.count())