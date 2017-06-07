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
cells = [(point.label, 0) for point in points]
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
model.add(Dense(len(y[0]), activation="softmax"))
if WEIGHTS is not None:
    model.load_weights(WEIGHTS)
model.compile(loss="categorical_crossentropy", optimizer="rmsprop", metrics=['accuracy'])
model.summary()
log.info("--> done")

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
    cells = list(generate())
    log.info("--> done")    
    print(cells)
    for c, cell in enumerate(cells):
        cells[c] = cell, 10
    drawer.path(cells)
