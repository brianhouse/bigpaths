#!/usr/bin/env python3

import subprocess, os, sys, glob, shutil
from housepy import config, log

if len(sys.argv) != 2:
    print("[model]")
    exit()

slug = sys.argv[1].split('/')[-1].split('.')[0]

log.info("--> using model %s" % slug)

root = os.path.abspath(os.path.dirname(__file__))

log.info("Generating output...")
p = subprocess.run(["th", "sample.lua", 
                "-checkpoint", os.path.join(root, "data", "%s.t7" % slug),
                # "-length 100000",
                "-length", "1000",                
                "-gpu", "0" if config['gpu'] else "-1"
                ], 
                cwd=config['torch-rnn'],
                stdout=subprocess.PIPE
                )
output = str(p.stdout)
path = os.path.join(root, "data", "%s.txt" % slug.replace("model", "output"))
with open(path, 'w') as f:
    f.write(output)
log.info("--> done")
