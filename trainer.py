#!/usr/bin/env python3

import subprocess, os, sys, glob, shutil
from housepy import config, log

if len(sys.argv) != 4:
    print("[corpus] [batch_size] [sequence_length]")
    exit()

corpus = sys.argv[1].split('/')[-1].split('.')[0]
batch_size = sys.argv[2]
sequence_length = sys.argv[3]

log.info("--> using corpus %s" % corpus)

root = os.path.abspath(os.path.dirname(__file__))

log.info("Pre-processing...")
subprocess.run(["python", "scripts/preprocess.py", 
                "--input_txt", os.path.join(root, "data", "%s.txt" % corpus),
                "--output_h5", os.path.join(root, "data", "%s.h5" % corpus),
                "--output_json", os.path.join(root, "data", "%s.json" % corpus),
                ], cwd=config['torch-rnn'])
log.info("--> done")

log.info("Training...")
subprocess.run(["time", "th", "train.lua",
                "-input_h5", os.path.join(root, "data", "%s.h5" % corpus),
                "-input_json", os.path.join(root, "data", "%s.json" % corpus),
                "-batch_size", batch_size,
                "-seq_length", sequence_length, 
                "-max_epochs", "100",
                "-gpu", "0" if config['gpu'] else "-1"
                ], cwd=config['torch-rnn'])
log.info("--> done")

log.info("Copying model...")
path = os.path.join(config['torch-rnn'], "cv")
newest_checkpoint = max(glob.iglob(os.path.join(path, "*.t7")), key=os.path.getctime)
slug = corpus.split("_")[0]
shutil.copy(newest_checkpoint, os.path.join(root, "data", "%s_model_b%s_s%s.t7" % (slug, batch_size, sequence_length)))
log.info("--> done")

