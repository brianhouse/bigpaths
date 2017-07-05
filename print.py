#!/usr/bin/env python3

import random, sys, requests, json
import numpy as np
import drawer
from housepy import config, log, geo
from points import *

# days = util.load("data/1497313211_10_7_house_0.25_output.pkl")
# days = util.load("data/1498344519_10_7_ct-30-0.9313_0.25_output.pkl")
# days = util.load("data/1498344519_10_7_ct-30-0.9313_0.01_output.pkl")
days = util.load("data/1498344519_10_7_ct-30-0.9313_0.95_output.pkl")
index = random.choice(range(len(days)))

print("INDEX", index)

day = days[index] + days[index+1]

def trim(day):
    d = 0
    while True:
        if day[d].period < day[d+1].period:
            d += 1
        else:
            d += 1
            break    
    while day[d].period < 24 or day[d].period > 120:   # 4am, 8pm
        d += 1
    day = day[d:]
    d = 0
    while True:
        if day[d].period < day[d+1].period:
            d += 1
        else:
            d += 1
            break       
    while day[d].period < 24 or day[d].period > 120:   # 4am, 8pm
        d += 1
    day = day[:d]        
    return day

day = trim(day)

geocode(day)
format_times(day)
for point in day:
    point.unhash()

for p, point in enumerate(day):
    label = "%d) %s %s%s" % (p+1, "Wake up at" if p == 0 else "%s," % point.display_time, point.address, "" if p != (len(day) - 1) else " ... sleep")
    print(label)

drawer.path_print(day, index)

