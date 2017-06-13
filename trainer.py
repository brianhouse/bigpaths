#!/usr/bin/env python3

import random, sys
import numpy as np
import drawer
from housepy import config, log, geo, strings
from keras.models import Sequential
from keras.layers.recurrent import LSTM, GRU
from keras.layers.core import Dense, Activation, Dropout
from keras.utils import to_categorical
from points import *


# assign constants
MEMORY = config['memory']
assert(MEMORY % 2 == 0)
TEMPERATURE = config['temperature']
WEIGHTS = None
MODEL = None
if len(sys.argv) > 1:
    MODEL = sys.argv[1].strip("models/").strip(".hdf5")
    WEIGHTS = "models/%s.hdf5" % MODEL    
BATCH_SIZE = 64 
log.info("Data size (%d[%d], %d[%d])..." % (PERIODS, PERIOD_SIZE, LOCATIONS, GRID_SIZE))
CATEGORIES = PERIODS + LOCATIONS
log.info("--> %d categories" % CATEGORIES)


# create model
log.info("Creating model...")
model = Sequential()
model.add(LSTM(256, return_sequences=True, input_shape=(MEMORY, CATEGORIES), dropout=0.2, recurrent_dropout=0.2))
model.add(LSTM(256, return_sequences=False, dropout=0.2, recurrent_dropout=0.2))
model.add(Dense(CATEGORIES, activation="softmax"))
if WEIGHTS is not None:
    model.load_weights(WEIGHTS)
model.compile(loss="categorical_crossentropy", optimizer="rmsprop", metrics=['accuracy'])
model.summary()
log.info("--> done")


# generate inputs
def generate_input():
    log.info("Generating input data...")
    points = util.load("data/points_%d_%d.pkl" % (PERIOD_SIZE, GRID_SIZE))
    cells = []
    for point in points:
        cells.append(point.location)
        cells.append(LOCATIONS + point.duration)
    inputs = []
    outputs = []
    period_refs = []
    for i in range(0, len(cells[:]) - MEMORY, 2):
        inputs.append(cells[i:i + MEMORY])
        outputs.append(cells[i + MEMORY])
        period_refs.append(points[(i + MEMORY)//2].period)    # the period of the target, which we'll use to reconstruct the point when generating
    log.info("--> %d points into %s prelim inputs" % (len(points), len(inputs)))    
    log.info("Categoricalizing (%s memory required)..." % strings.format_size(len(inputs) * MEMORY * CATEGORIES))
    input_length = (len(inputs) // BATCH_SIZE) * BATCH_SIZE # we need inputs to be a multiple of batch_size so we dont train on multiple users in the same batch
    log.info("--> made array")
    X = np.zeros((input_length, MEMORY, CATEGORIES), dtype=np.bool)
    last_percent = 0
    for i, input in enumerate(inputs):
        if i == input_length:
            break
        X[i] = to_categorical(np.array(input), CATEGORIES)
        percent = int((i / input_length) * 100)
        if percent != last_percent:
            log.info("%s%%" % percent)
        last_percent = percent
    log.info("--> filled")
    log.info("Categorializing output...")
    y = to_categorical(np.array(outputs), CATEGORIES)[:len(X)]
    log.info("--> %d input vectors" % len(X))
    log.info("--> shape: %s" % (X[0].shape,))
    return X, y, period_refs
X, y, period_refs = generate_input()


# train
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
if MODEL is None:
    MODEL = "%s_%d_%d" % (timeutil.timestamp(), PERIOD_SIZE, GRID_SIZE)
k = input("Save? y/[n]: ")
if k.lower() == "y":
    model.save("models/%s.hdf5" % model)


# generate outputs
def generate():
    cells = []
    index = random.choice(range(len(X)))
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
            if total_duration >= PERIODS:
                break
        else:
            log.warning("Incorrect category order: %s" % category)
            continue
        i += 1
    cells = list(zip(cells[::2], cells[1::2]))
    log.debug(cells)
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
points = []
for i in range(n):    
    day = generate()
    drawer.path(day)
    points.append(day)
drawer.strips([point for day in points for point in day])
util.save("data/%s_%s_output.pkl" % (MODEL, TEMPERATURE), points)
log.info("--> done")
