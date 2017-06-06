#!/usr/bin/env python3

import random, sys
import numpy as np
import drawer
from housepy import config, log, geo
from keras.models import Sequential
from keras.layers.recurrent import LSTM, GRU
from keras.layers.core import Dense, Activation, Dropout
from keras.callbacks import ModelCheckpoint
from keras.utils import to_categorical
from data import *


EPOCHS = 10
MEMORY = 5
WEIGHTS = None
if len(sys.argv) > 1:
    WEIGHTS = sys.argv[1]


log.info("Generating training input...")
sequences = util.load("data/sequences_%d_%d.pkl" % (config['grid'], config['periods']))
data = [point.label for sequence in sequences for point in sequence]
inputs = []
outputs = []
for i in range(len(data) - MEMORY):
    inputs.append(to_categorical(data[i:i + MEMORY], GRIDS))
    outputs.append(data[i + MEMORY])
X = inputs
y = to_categorical(np.array(outputs), GRIDS)
log.info("--> %d input vectors" % len(X))


log.info("Creating model...")
model = Sequential()
model.add(LSTM(128, return_sequences=True, input_shape=X[0].shape))
model.add(Dropout(0.2))
model.add(LSTM(256, return_sequences=True))
model.add(Dropout(0.2))
model.add(LSTM(128, return_sequences=False))
model.add(Dropout(0.2))
model.add(Dense(len(y[0]), activation=('softmax')))
if WEIGHTS is not None:
    model.load_weights(WEIGHTS)
model.compile(loss="categorical_crossentropy", optimizer="rmsprop", metrics=['accuracy'])
model.summary()
log.info("--> done")


def generate():
    seed = random.choice(X)
    sequence = seed[:]
    for i in range(PERIODS + len(seed)):
        x = np.array([sequence[-MEMORY:]])
        point = model.predict(x, verbose=0)[0]
        sequence.append(point)
    return seed, sequence


log.info("Training...")
t = timeutil.timestamp()
for i in range(EPOCHS):
    log.info("(%d)" % (i+1))
    try: 
        filepath = "checkpoints/%s_checkpoint-%d-{loss:.4f}.hdf5" % (t, i)
        checkpoint = ModelCheckpoint(filepath, monitor="loss", verbose=1, save_best_only=True, mode="min")
        model.fit(X, y, epochs=1, callbacks=[checkpoint])
    except KeyboardInterrupt:
        print()
        exit()
    log.info("Generating example...")
    seed, sequence = generate()
    log.info("--> done")
    print(seed)
    print(sequence)
    drawer.sequence(sequence, "result")

