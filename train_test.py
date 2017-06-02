#!/usr/bin/env python3

import random, sys
import numpy as np
import drawer
from housepy import config, log
from keras.models import Sequential
from keras.layers.recurrent import LSTM
from keras.layers.core import Dense, Activation, Dropout
from keras.callbacks import ModelCheckpoint
from keras.utils import plot_model
from data import *

SAMPLE_LIMIT = 2000
EPOCHS = 10

WEIGHTS = None
if len(sys.argv) > 1:
    WEIGHTS = sys.argv[1]

corpus = util.load("data/corpus_house.pkl")


# split the dataset into moving sequences
log.info("Generating training sequences...")
sequence_length = PERIODS
sequences = []
outputs = []
for i in range(len(corpus) - sequence_length):
    sequences.append(corpus[i:i + sequence_length])  # this is the sequence
    outputs.append(corpus[i + sequence_length])   # the expected output is the next lonlat
if SAMPLE_LIMIT is not None:
    sequences = sequences[:SAMPLE_LIMIT]
    outputs = outputs[:SAMPLE_LIMIT]
X = np.array(sequences)
y = np.array(outputs)
log.info("--> %d sequences" % len(sequences))


log.info("Creating model...")
model = Sequential()
model.add(LSTM(100, return_sequences=True, input_shape=X[0].shape))
model.add(Dropout(0.2))
model.add(LSTM(200, return_sequences=False))
model.add(Dropout(0.2))
model.add(Dense(2))
if WEIGHTS is not None:
    model.load_weights(WEIGHTS)
model.compile(loss="mean_squared_error", optimizer="rmsprop", metrics=['accuracy'])
plot_model(model, to_file="model.png", show_shapes=True, show_layer_names=True)
log.info("--> done")


def generate(temperature=0.35):
    start_index = random.randint(0, len(corpus) - sequence_length - 1)
    seed = corpus[start_index:start_index + sequence_length]
    sequence = seed[:]
    for i in range(sequence_length):    # replace the randomly seeded sequence with a sequence of newly generated points
        x = np.array([sequence])
        point = model.predict(x, verbose=0)[0]
        sequence.append(point)
        sequence.pop(0)
    return sequence, seed


log.info("Training...")
t = timeutil.timestamp()
for i in range(EPOCHS):
    log.info("(%d)" % (i+1))

    try: 
        filepath = "checkpoints/%s_checkpoint-%d-{loss:.4f}.hdf5" % (t, i)
        checkpoint = ModelCheckpoint(filepath, monitor="loss", verbose=1, save_best_only=True, mode="min")
        model.fit(X, y, epochs=1, callbacks=[checkpoint])
    except KeyboardInterrupt:
        exit()

    # for temp in [0.2, 0.5, 1.0]:
    for temp in [1.0]:
        log.info("Generating with temperature %0.2f..." % temp)
        sequence, seed = generate(temperature=temp)
        log.info("--> done")
        log.info("Drawing...")
        drawer.sequences([sequence, seed])
        log.info("--> done")

