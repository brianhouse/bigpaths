#!/usr/bin/env python3

import sys, random, datetime, json, math, json
import numpy as np
from housepy import geo, config, log, util, timeutil
import drawer

if len(sys.argv) != 3:
    print("[corpus] [output]")
    exit()
orig_path = sys.argv[1]
gen_path = sys.argv[2]

# load data
log.info("Loading original output %s..." % orig_path)
with open("data/%s" % orig_path) as f:
    orig_data = f.read()
log.info("Loading generated output %s..." % gen_path)
with open("data/%s" % gen_path) as f:
    gen_data = f.read()

# split into days
orig_data = orig_data.split("00")
gen_data = gen_data.split("00")

# count correspondances
overfit_count = 0
for gd in gen_data:
    try:
        log.info("----------%s" % orig_data.index(gd))
        overfit_count += 1
    except ValueError:
        pass

log.info("--> overfit percentage: %%%.2f" % ((overfit_count / len(gen_data) * 100)))
