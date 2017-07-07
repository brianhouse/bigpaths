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
log.info("Dataset (%d[%d], %d[%d])..." % (PERIODS, PERIOD_SIZE, LOCATIONS, LOCATION_SIZE))
log.info("--> %d categories" % CATEGORIES)
log.info("--> %d steps memory" % MEMORY)
if MODEL is not None:
    log.info("--> using %s" % MODEL)


# create model
log.info("Creating model...")
model = Sequential()
model.add(LSTM(256, return_sequences=False, stateful=True, input_shape=(MEMORY, CATEGORIES)))   # no dropout, basically trying to overfit
# model.add(LSTM(1024, return_sequences=True))
# model.add(LSTM(1024, return_sequences=False))
model.add(Dense(CATEGORIES, activation="softmax"))
if MODEL is not None:
    model.load_weights(MODEL)
model.compile(loss="categorical_crossentropy", optimizer="rmsprop", metrics=['accuracy'])
model.summary()
log.info("--> done")


# # input generator
# data = util.load(config['points'])
# epoch_size = len(data) - MEMORY
# def input_generator():
#     points = []
#     X = []
#     y = []
#     for p, point in enumerate(data):
#         points.append(point)
#         if len(points) < MEMORY + 1:
#             continue
#         X.append(to_categorical([point.location for point in points[:-1]], CATEGORIES))
#         y.append(to_categorical(points[-1].location, CATEGORIES)[0])
#         points = points[1:]
#         if len(y) == config['batch_size']:
#             yield np.array(X), np.array(y)
#             X = []
#             y = []

def generate_input():
    log.info("Generating input sequences...")
    points = util.load(config['points'])
    cells = [point.location for point in points]
    inputs = []
    outputs = []
    for i in range(0, len(cells[:]) - MEMORY):
        inputs.append(cells[i:i + MEMORY])
        outputs.append(cells[i + MEMORY])
    cells = None
    log.info("--> %d points into %s sequences" % (len(points), len(inputs)))    
    log.info("Making categorical inputs (%s memory required)..." % strings.format_size(len(inputs) * MEMORY * CATEGORIES))
    input_length = (len(inputs) // config['batch_size']) * config['batch_size'] # we need inputs to be a multiple of batch_size so we dont train on multiple users in the same batch
    X = np.zeros((input_length, MEMORY, CATEGORIES), dtype=np.bool)
    y = np.zeros((input_length, CATEGORIES), dtype=np.bool)
    last_percent = 0
    for i, input in enumerate(inputs):
        if i == input_length:
            break
        X[i] = to_categorical(np.array(input), CATEGORIES)
        percent = int((i / input_length) * 100)
        if percent != last_percent:
            util.progress_bar(percent)
        last_percent = percent
    inputs = None
    log.info("--> complete")
    log.info("Categorializing output...")
    outputs = np.array(outputs[:len(X)])
    for o, output in enumerate(outputs):
        y[o][output] = 1
    log.info("--> %d input vectors" % len(X))
    log.info("--> shape: %s" % (X[0].shape,))
    return X, y
X, y = generate_input()


# train
train = True
if not config['autonomous'] and MODEL is not None:
    train = False
    k = input("Train? y/[n]: ")
    if k.lower() == "y":
        train = True
if MODEL is None:
    MODEL = "%s_%d_%d" % (timeutil.timestamp(), PERIOD_SIZE, LOCATION_SIZE)
if train:
    log.info("Training...")
    try:
        if config['checkpoints']:
            callbacks = [ModelCheckpoint(filepath="models/%s-{epoch:02d}-{acc:.4f}.hdf5" % MODEL.strip("models/").strip(".hdf5"), verbose=1, save_best_only=True, monitor="acc", mode="max")]
        else:
            callbacks = None
        # model.fit_generator(input_generator(), epoch_size, epochs=config['epochs'], callbacks=callbacks)
        model.fit(X, y, epochs=config['epochs'], batch_size=config['batch_size'], callbacks=callbacks)
    except KeyboardInterrupt:
        print()
if config['autonomous']:
    model.save("models/%s.hdf5" % MODEL)
else:
    k = input("Save? y/[n]: ")
    if k.lower() == "y":
        model.save("models/%s.hdf5" % MODEL)


# generate outputs
def generate():
    day = []
    index = random.choice(range(len(X)))
    x = X[index]
    for i in range(PERIODS):
        distribution = model.predict(np.array([x[-MEMORY:]]), verbose=0, batch_size=1)[0]
        y = sample(distribution, config['temperature'])
        x = np.append(x, to_categorical(y, CATEGORIES), axis=0)
        day.append(y)
    log.debug(day)
    return day

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
days = []
for i in range(n):    
    day = generate()
    days.append(day)
util.save("data/%s_%s_output.pkl" % (MODEL, config['temperature']), days)
log.info("--> done")
