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
    inputs.append(data[i:i + MEMORY])
    outputs.append(data[i + MEMORY])
X = np.array([to_categorical(np.array(input), GRIDS) for input in inputs])
y = to_categorical(np.array(outputs), GRIDS)
log.info("--> %d input vectors" % len(X))


log.info("Creating model...")
model = Sequential()
model.add(LSTM(512, return_sequences=True, input_shape=X[0].shape))
model.add(Dropout(0.2))
model.add(LSTM(512, return_sequences=False))
model.add(Dropout(0.2))
model.add(Dense(GRIDS, activation=('softmax')))
if WEIGHTS is not None:
    model.load_weights(WEIGHTS)
model.compile(loss="categorical_crossentropy", optimizer="rmsprop", metrics=['accuracy'])
model.summary()
log.info("--> done")


def generate():
    result = []
    sequence = random.choice(X)
    for i in range(PERIODS):
        distribution = model.predict(np.array([sequence[-MEMORY:]]), verbose=0)[0]
        label = list(distribution).index(np.max(distribution))
        result.append(label)
        sequence = np.append(sequence, to_categorical(label, GRIDS), axis=0)
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
    drawer.sequence(sequence, "result")

