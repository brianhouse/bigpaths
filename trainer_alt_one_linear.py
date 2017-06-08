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


EPOCHS = 50
MEMORY = 30
WEIGHTS = None
if len(sys.argv) > 1:
    WEIGHTS = sys.argv[1]


log.info("Generating training input...")
points = util.load("data/sequences_alt_%d_%d.pkl" % (config['grid'], config['periods']))
cells = [(point.label,) for point in points]
inputs = []
outputs = []
for i in range(len(cells) - MEMORY):
    inputs.append(cells[i:i + MEMORY])
    outputs.append(cells[i + MEMORY])
X = np.array(inputs)
y = np.array(outputs)
log.info("--> %d input vectors" % len(X))

log.info("Creating model...")
model = Sequential()
model.add(LSTM(512, return_sequences=True, input_shape=X[0].shape, dropout=0.2, recurrent_dropout=0.2))
model.add(LSTM(512, return_sequences=False, dropout=0.2))
model.add(Dense(len(y[0]), activation="relu"))
if WEIGHTS is not None:
    model.load_weights(WEIGHTS)
model.compile(loss="mean_squared_error", optimizer="rmsprop", metrics=['accuracy'])
model.summary()
log.info("--> done")

log.info("Training...")
try:
    model.fit(X, y, epochs=EPOCHS)
    model.save("checkpoints/%s_%s.hdf5" % (__file__.split("/")[-1].split(".")[0], timeutil.timestamp()))
except KeyboardInterrupt:
    print()
    exit()

def generate():
    result = []
    input = random.choice(X)
    for i in range(10):
        cell = model.predict(np.array([input[-MEMORY:]]), verbose=0)[0]
        result.append((int(cell[0]), 10))
        input = np.append(input, np.array([cell]), axis=0)
    return result

log.info("Generating examples...")
for i in range(10):    
    cells = list(generate())
    print(cells)
    drawer.path(cells)
