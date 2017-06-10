#!/usr/bin/env python3

import random, sys
import numpy as np
import drawer
from housepy import config, log, geo
from keras.models import Sequential
from keras.layers.recurrent import LSTM, GRU
from keras.layers.core import Dense, Activation, Dropout
from keras.utils import to_categorical
from points import *


MEMORY = 30
WEIGHTS = None
if len(sys.argv) > 1:
    WEIGHTS = sys.argv[1]

# batch size could be important


log.info("Generating training input (%d[%d], %d[%d])..." % (PERIODS, PERIOD_SIZE, LOCATIONS, GRID_SIZE))
points = util.load("data/points_%d_%d.pkl" % (PERIOD_SIZE, GRID_SIZE))
CATEGORIES = max(PERIODS, LOCATIONS)
cells = []
for point in points:
    cells.append(point.location)
    cells.append(point.duration)
inputs = []
outputs = []
for i in range(len(cells) - MEMORY):
    inputs.append(cells[i:i + MEMORY])
    outputs.append(cells[i + MEMORY])
X = np.array([to_categorical(np.array(input), CATEGORIES) for input in inputs])
y = to_categorical(np.array(outputs), CATEGORIES)
log.info("--> %d input vectors" % len(X))
log.info("--> %d categories" % CATEGORIES)


log.info("Creating model...")
model = Sequential()
model.add(LSTM(512, return_sequences=True, input_shape=X[0].shape, dropout=0.2, recurrent_dropout=0.2))
model.add(LSTM(512, return_sequences=False, dropout=0.2))
model.add(Dense(len(y[0]), activation="softmax"))
if WEIGHTS is not None:
    model.load_weights(WEIGHTS)
model.compile(loss="categorical_crossentropy", optimizer="rmsprop", metrics=['accuracy'])
model.summary()
log.info("--> done")


log.info("Training...")
try:
    model.fit(X, y, epochs=1000)
except KeyboardInterrupt:
    print()
    k = input("Save? y/[n]:")
    if k.lower() != "y":
        exit()

model.save("models/%s_%s.hdf5" % (__file__.split("/")[-1].split(".")[0], timeutil.timestamp()))


def generate():
    result = []
    input = random.choice(X)
    for i in range(PERIODS):
        distribution = model.predict(np.array([input[-MEMORY:]]), verbose=0)[0]
        label = sample(distribution, 0.5)
        result.append(label)
        input = np.append(input, to_categorical(label, GRIDS), axis=0)
    return result

def sample(distribution, temperature):
    a = np.log(distribution) / temperature
    p = np.exp(a) / np.sum(np.exp(a))
    choices = range(len(distribution))
    return np.random.choice(choices, p=p)

log.info("Generating examples...")
for i in range(10):    
    labels = list(generate())
    drawer.sequence(labels)
