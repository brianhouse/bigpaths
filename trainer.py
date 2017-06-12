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


MEMORY = config['memory']
assert(MEMORY % 2 == 0)
TEMPERATURE = config['temperature']
WEIGHTS = None
if len(sys.argv) > 1:
    WEIGHTS = "models/%s" % sys.argv[1].strip("models/")
BATCH_SIZE = 64 


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
period_refs = []
for i in range(len(cells) - MEMORY):
    inputs.append(cells[i:i + MEMORY])
    outputs.append(cells[i + MEMORY])
    period_refs.append(points[(i + MEMORY)//2].period)    # the period of the target, which we'll use to reconstruct the point when generating
X = np.array([to_categorical(np.array(input), CATEGORIES) for input in inputs])
X = X[:(len(X) // BATCH_SIZE) * BATCH_SIZE] # we need inputs to be a multiple of batch_size so we dont train on multiple users in the same batch
y = to_categorical(np.array(outputs), CATEGORIES)[:len(X)]
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
        model.fit(X, y, epochs=1000, batch_size=BATCH_SIZE)
    except KeyboardInterrupt:
        print()
k = input("Save? y/[n]: ")
if k.lower() == "y":
    model.save("models/%s_%d_%d.hdf5" % (timeutil.timestamp(), PERIOD_SIZE, GRID_SIZE))


def generate(days=1):
    cells = []
    index = random.choice(range(len(inputs) // 2)) * 2 # have to pick an even-numbered seed, otherwise we'll be starting on a duration and not a location
    input = X[index]
    period_ref = period_refs[index] # this is the period of the target
    day_indexes = []
    total_duration = 0
    i = 0
    while True:
        distribution = model.predict(np.array([input[-MEMORY:]]), verbose=0, batch_size=1)[0]
        category = sample(distribution, TEMPERATURE)
        input = np.append(input, to_categorical(category, CATEGORIES), axis=0)
        if i % 2 == 0 and category < LOCATIONS:
            location = category
            cells.append(location)
        elif i % 2 == 1 and category >= LOCATIONS:
            duration = category - LOCATIONS
            cells.append(duration)
            total_duration += duration            
            if total_duration >= PERIODS * days:
                break
        else:
            log.warning("Incorrect category order: %s" % category)
            continue
        i += 1
    cells = list(zip(cells[::2], cells[1::2]))
    print(cells)
    points = []
    total_duration = 0
    for cell in cells:        
        location, duration = cell
        period = (period_ref + total_duration) % PERIODS
        total_duration += duration
        point = GeneratedPoint(location, period, duration)
        points.append(point)
    return points

def sample(distribution, temperature):
    a = np.log(distribution) / temperature
    p = np.exp(a) / np.sum(np.exp(a))
    choices = range(len(distribution))
    return np.random.choice(choices, p=p)

k = input("Generate how many examples? [10]: ")
n = int(k.lower()) if len(k) else 10
log.info("Generating %d examples..." % n)
points = generate(10)
drawer.path(points)
drawer.stips(points)
# all_points = []
# for i in range(n):    
#     points = generate()
#     drawer.path(points)
#     all_points.extend(points)
# drawer.strips(all_points)
