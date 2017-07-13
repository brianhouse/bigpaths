#!/usr/bin/env python3

import sys, random, h5py
import numpy as np
from housepy import config, log
from tqdm import tqdm

if len(sys.argv) != 3:
    print("[corpus] [sequence_length]")
    exit()
path = sys.argv[1]
sequence_length = int(sys.argv[2])
slug = path.split('_')[0].split('.')[0]
log.info("Loading corpus %s..." % slug)
corpus = open("data/%s" % path).read().lower()
characters = list(set(corpus))
characters.sort()
log.info("--> %d unique characters" % len(characters))


log.info("Preparing sequences of length %d..." % sequence_length)
sequences = []
outputs = []
for i in range(0, len(corpus) - sequence_length):
    sequences.append(corpus[i:i + sequence_length])  # this is the sequence
    outputs.append(corpus[i + sequence_length])      # the expected output is the next character
log.info("--> %d sequences" % len(sequences))


log.info("Creating tensors...")
character_to_label = {ch:i for i, ch in enumerate(characters)}
X = np.zeros((len(sequences), sequence_length, len(characters)), dtype=np.bool)
y = np.zeros((len(sequences), len(characters)), dtype=np.bool)
for i in tqdm(range(len(sequences))):
    sequence = sequences[i]
    for t, character in enumerate(sequence):
        X[i, t, character_to_label[character]] = 1
    y[i, character_to_label[outputs[i]]] = 1
log.info("--> done")


path = "data/%s_input_%s.mdf5" % (slug, sequence_length)
log.info("--> Saving to %s..." % path)
with h5py.File(path, 'w') as f:
    f.create_dataset('X', data=X)
    f.create_dataset('y', data=y)
    f.create_dataset('categories', data=[len(characters)])
    f.create_dataset('label_to_character', data=[ch.encode('utf-8') for ch in characters])
log.info("--> done")
