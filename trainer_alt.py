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
points = util.load("data/sequences_alt_%d_%d.pkl" % (config['grid'], config['periods']))
data = [(point.label, point.duration) for point in points]
inputs = []
outputs = []
for i in range(len(data) - MEMORY):
    inputs.append(data[i:i + MEMORY])
    outputs.append(data[i + MEMORY])
X = np.array(inputs)
y = np.array(outputs)
log.info("--> %d input vectors" % len(X))


log.info("Creating model...")
model = Sequential()
model.add(LSTM(512, return_sequences=True, input_shape=X[0].shape))
model.add(Dropout(0.2))
model.add(LSTM(512, return_sequences=False))
model.add(Dropout(0.2))
model.add(Dense(len(y[0])))
if WEIGHTS is not None:
    model.load_weights(WEIGHTS)
model.compile(loss="mean_squared_error", optimizer="rmsprop", metrics=['accuracy'])
model.summary()
log.info("--> done")


def generate():
    result = []
    sequence = random.choice(X)    
    for i in range(MEMORY):
        print(sequence[-MEMORY:])
        r = model.predict(np.array([sequence[-MEMORY:]]), verbose=0)[0]
        result.append((int(r[0]), int(r[1])))
        sequence = np.append(sequence, [r], axis=0)
    return result


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
    sequence = generate()
    log.info("--> done")
    print(sequence)
    # drawer.sequence(sequence, "result")

