#!/usr/bin/env python3

import random, sys
import numpy as np
import drawer
from housepy import config, log, geo
from keras.models import Sequential
from keras.layers.recurrent import LSTM
from keras.layers.core import Dense, Activation, Dropout
from keras.callbacks import ModelCheckpoint
from keras.utils import plot_model
from data import *

SAMPLE_LIMIT = None
EPOCHS = 10

WEIGHTS = None
if len(sys.argv) > 1:
    WEIGHTS = sys.argv[1]

GRIDS = len(grids)

# test sequence
skip = math.ceil(PERIODS / GRIDS)
sequence = []
for i in range(PERIODS):
    sequence.append(math.floor(i / skip))

corpus = sequence * 1000


# split the dataset into moving sequences
log.info("Generating training sequences...")
sequence_length = PERIODS
sequences = []
outputs = []
for i in range(len(corpus) - sequence_length):
    sequences.append(corpus[i:i + sequence_length])  # this is the sequence of clusters
    outputs.append(corpus[i + sequence_length])      # the expected output is the next cluster
if SAMPLE_LIMIT is not None:
    sequences = sequences[:SAMPLE_LIMIT]
    outputs = outputs[:SAMPLE_LIMIT]
log.info("--> %d sequences" % len(sequences))


# prep one-hot tensors
X = np.zeros((len(sequences), sequence_length, GRIDS), dtype=np.bool)     ## fix constant
y = np.zeros((len(sequences), GRIDS), dtype=np.bool)
for s, sequence in enumerate(sequences):
    for p, label in enumerate(sequence):
        X[s, p, label] = 1
    y[s, label] = 1


log.info("Creating model...")
model = Sequential()
model.add(LSTM(512, return_sequences=True, input_shape=X[0].shape))
model.add(Dropout(0.2))
model.add(LSTM(512, return_sequences=True))
model.add(Dropout(0.2))
model.add(LSTM(512, return_sequences=False))
model.add(Dropout(0.2))
model.add(Dense(GRIDS, activation=('softmax')))
if WEIGHTS is not None:
    model.load_weights(WEIGHTS)
model.compile(loss="categorical_crossentropy", optimizer="rmsprop", metrics=['accuracy'])
plot_model(model, to_file="model.png", show_shapes=True, show_layer_names=True)
log.info("--> done")


def generate():
    start_index = random.randint(0, len(corpus) - sequence_length - 1)
    seed = corpus[start_index:start_index + sequence_length]
    sequence = seed[:]
    for i in range(sequence_length):
        x = np.zeros((1, sequence_length, GRIDS))
        for p, label in enumerate(sequence[-sequence_length:]):
            x[0, p, label] = 1.
        distribution = model.predict(x, verbose=0)[0]    
        label = list(distribution).index(np.max(distribution))        
        sequence.append(label)
        sequence.pop(0)
    return sequence, seed


log.info("Training...")
t = timeutil.timestamp()
for i in range(EPOCHS):
    log.info("(%d)" % (i+1))
    try: 
        filepath = "checkpoints/%s_checkpoint-%d-{loss:.4f}.hdf5" % (t, i)
        checkpoint = ModelCheckpoint(filepath, monitor="loss", verbose=1, save_best_only=True, mode="min")
        model.fit(X, y, epochs=1, batch_size=128, callbacks=[checkpoint])
    except KeyboardInterrupt:
        print()
        exit()
    log.info("Generating example...")
    sequence, seed = generate()
    log.info("--> done")
    drawer.sequence(seed, "seed")
    drawer.sequence(sequence, "result")

