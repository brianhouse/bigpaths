#!/usr/bin/env python3

import random, sys
import numpy as np
import drawer
from housepy import config, log, geo, strings, util
from keras.models import Sequential
from keras.layers.recurrent import LSTM
from keras.layers.core import Dense, Activation
from keras.utils import to_categorical
from keras.callbacks import ModelCheckpoint
from points import *


# assign constants
MODEL = None
if len(sys.argv) > 1:
    MODEL = sys.argv[1].strip("models/").strip(".hdf5")
    MODEL = "models/%s.hdf5" % MODEL    
CATEGORIES = LOCATIONS
MEMORY = PERIODS * 2
log.info("Dataset (%d[%d], %d[%d])..." % (PERIODS, PERIOD_SIZE, LOCATIONS, GRID_SIZE))
log.info("--> %d categories" % CATEGORIES)
log.info("--> %d steps memory" % MEMORY)
if MODEL is not None:
    log.info("--> using %s" % MODEL)


# create model
log.info("Creating model...")
model = Sequential()
model.add(LSTM(1024, return_sequences=True, input_shape=(MEMORY, CATEGORIES)))   # no dropout, basically trying to overfit
model.add(LSTM(1024, return_sequences=True))
model.add(LSTM(1024, return_sequences=False))
model.add(Dense(CATEGORIES, activation="softmax"))
if MODEL is not None:
    model.load_weights(MODEL)
model.compile(loss="categorical_crossentropy", optimizer="rmsprop", metrics=['accuracy'])
model.summary()
log.info("--> done")


# input generator
data = util.load(config['points'])
epoch_size = len(data) - MEMORY
def generate_input():
    points = []
    X = []
    y = []
    for point in data:
        points.append(point)
        if len(points) < MEMORY + 1:
            continue
        X.append(to_categorical(points[:-1], CATEGORIES))
        y.append(to_categorical(points[-1].location, CATEGORIES))
        points = points[-1:]
        if len(y) == config['batch_size']:
            yield X, y
            X = []
            y = []


# train
train = True
if not config['autonomous'] and MODEL is not None:
    train = False
    k = input("Train? y/[n]: ")
    if k.lower() == "y":
        train = True
if MODEL is None:
    MODEL = "%s_%d_%d" % (timeutil.timestamp(), PERIOD_SIZE, GRID_SIZE)
if train:
    log.info("Training...")
    try:
        if config['checkpoints']:
            callbacks = [ModelCheckpoint(filepath="models/%s-{epoch:02d}-{acc:.4f}.hdf5" % MODEL.strip("models/").strip(".hdf5"), verbose=1, save_best_only=True, monitor="acc", mode="max")]
        else:
            callbacks = None
        model.fit_generator(generate_input, epoch_size, epochs=config['epochs'], callbacks=callbacks)
    except KeyboardInterrupt:
        print()
if config['autonomous']:
    model.save(MODEL)
else:
    k = input("Save? y/[n]: ")
    if k.lower() == "y":
        model.save(MODEL)


# generate outputs
def generate():
    locations = []
    index = random.choice(range(len(X)))
    x = X[index]
    for i in range(MEMORY):
        distribution = model.predict(np.array([x[-MEMORY:]]), verbose=0, batch_size=1)[0]
        y = sample(distribution, config['temperature'])
        x = np.append(x, to_categorical(y, CATEGORIES), axis=0)
        locations.append(y)
    log.debug(locations)
    return locations

def sample(distribution, temperature): # thx gene
    a = np.log(distribution) / temperature
    p = np.exp(a) / np.sum(np.exp(a))
    choices = range(len(distribution))
    return np.random.choice(choices, p=p)

if not config['autonomous']:
    k = input("Generate how many examples? [10]: ")
    n = int(k.lower()) if len(k) else 10
else:
    n = 100
log.info("Generating %d examples..." % n)
sets = []
for i in range(n):    
    locations = generate()
    sets.append(locations)
util.save("data/%s_%s_output.pkl" % (MODEL, config['temperature']), sets)
log.info("--> done")
