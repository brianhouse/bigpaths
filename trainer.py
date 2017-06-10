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
TEMPERATURE = 0.5
WEIGHTS = None
if len(sys.argv) > 1:
    WEIGHTS = sys.argv[1]


log.info("Generating training input (%d[%d], %d[%d])..." % (PERIODS, PERIOD_SIZE, LOCATIONS, GRID_SIZE))
points = util.load("data/points_%d_%d.pkl" % (PERIOD_SIZE, GRID_SIZE))
CATEGORIES = PERIODS + LOCATIONS
log.info("--> %d categories" % CATEGORIES)
cells = []
for point in points:
    cells.append(point.location)
    cells.append(LOCATIONS + point.duration)
inputs = []
outputs = []
for i in range(len(cells) - MEMORY):
    inputs.append(cells[i:i + MEMORY])
    outputs.append(cells[i + MEMORY])
X = np.array([to_categorical(np.array(input), CATEGORIES) for input in inputs])
y = to_categorical(np.array(outputs), CATEGORIES)
log.info("--> %d input vectors" % len(X))
log.info("--> shape: %s" % (X.shape,))


log.info("Creating model...")
model = Sequential()
model.add(LSTM(256, return_sequences=True, input_shape=X[0].shape, dropout=0.2, recurrent_dropout=0.2))
model.add(LSTM(256, return_sequences=False, dropout=0.2, recurrent_dropout=0.2))
model.add(Dense(len(y[0]), activation="softmax"))
if WEIGHTS is not None:
    model.load_weights(WEIGHTS)
model.compile(loss="categorical_crossentropy", optimizer="rmsprop", metrics=['accuracy'])
model.summary()
log.info("--> done")


train = True
if WEIGHTS is not None:
    train = False
    k = input("Train? y/[n]: ")
    if k.lower() == "y":
        train = True    
if train:
    log.info("Training...")
    try:
        model.fit(X, y, epochs=1000, batch_size=64)    ## is this important to this problem
    except KeyboardInterrupt:
        print()
k = input("Save? y/[n]: ")
if k.lower() != "y":
    exit()
model.save("models/%s.hdf5" % timeutil.timestamp())


def generate():
    result = []
    input = random.choice(X)
    total_duration = 0
    i = 0
    while True:
        distribution = model.predict(np.array([input[-MEMORY:]]), verbose=0)[0]
        category = sample(distribution, TEMPERATURE)
        input = np.append(input, to_categorical(label, CATEGORIES), axis=0)
        if i % 2 == 0:
            location = category
            result.append(location)
        else:
            duration = category - LOCATIONS 
            total_duration += duration
            result.append(duration)
            if total_duration >= PERIODS:
                break
        i += 1
    return list(zip(result[::2], result[1::2]))

def sample(distribution, temperature):
    a = np.log(distribution) / temperature
    p = np.exp(a) / np.sum(np.exp(a))
    choices = range(len(distribution))
    return np.random.choice(choices, p=p)

log.info("Generating examples...")
for i in range(10):    
    cells = generate()
    print(cells)
    drawer.path(cells)
