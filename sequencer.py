#!/usr/bin/env python3

import sys, random
import numpy as np
from housepy import config, log, util


slug = config['corpus'].split('_')[0].split('.')[0]
log.info("Loading corpus %s..." % slug)
corpus = open("data/%s" % config['corpus']).read().lower()
characters = list(set(corpus))
log.info("--> %d unique characters" % len(characters))


log.info("Preparing sequences of length %d..." % config['sequence_length'])
sequences = []
outputs = []
for i in range(0, len(corpus) - config['sequence_length']):
    sequences.append(corpus[i:i + config['sequence_length']])  # this is the sequence
    outputs.append(corpus[i + config['sequence_length']])      # the expected output is the next character
log.info("--> %d sequences" % len(sequences))


log.info("Creating tensors...")
# mapping between characters and integers
character_to_label = {ch:i for i, ch in enumerate(characters)}
label_to_character = {i:ch for i, ch in enumerate(characters)}    
X = np.zeros((len(sequences), config['sequence_length'], len(characters)), dtype=np.bool)
y = np.zeros((len(sequences), len(characters)), dtype=np.bool)
for i, sequence in enumerate(sequences):
    for t, character in enumerate(sequence):
        X[i, t, character_to_label[character]] = 1
    y[i, character_to_label[outputs[i]]] = 1
log.info("--> done")


path = "data/%s_train_%s.pkl" % (slug, config['sequence_length'])
log.info("--> Saving to %s..." % path)
util.save(path, (X, y, characters, (character_to_label, label_to_character)))
log.info("--> done")
