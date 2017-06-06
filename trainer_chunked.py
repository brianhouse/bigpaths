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
MEMORY = 4
WEIGHTS = None
if len(sys.argv) > 1:
    WEIGHTS = sys.argv[1]


log.info("Generating training input...")
sequences = util.load("data/sequences_%d_%d.pkl" % (config['grid'], config['periods']))
inputs = []
outputs = []
for sequence in sequences:
    for (period, point) in enumerate(sequence):
        vector = [period]
        for m in range(MEMORY):
            if period < MEMORY:
                vector.append(point.label)  ## so this is kind of fake, should be previous sequence
            else:                           ## it means the seeds will always be mono
                vector.append(sequence[period - (m + 1)].label)
        inputs.append(vector)
        outputs.append(point.label)
X = np.array(inputs)
y = to_categorical(np.array(outputs))
log.info("--> %d inputs" % len(inputs))


log.info("Creating model...")
model = Sequential()
model.add(Dense(512, input_shape=X[0].shape))
model.add(Dropout(0.2))
model.add(Dense(512))
model.add(Dropout(0.2))
model.add(Dense(len(y[0]), activation=('softmax')))
if WEIGHTS is not None:
    model.load_weights(WEIGHTS)
model.compile(loss="categorical_crossentropy", optimizer="rmsprop", metrics=['accuracy'])
model.summary()
log.info("--> done")


def generate():
    # get a random seed from the inputs with period 0
    seed_index = random.choice(range(len(X)))
    while inputs[seed_index][0] != 0:
        seed_index += 1
    seed = inputs[seed_index]

    # the result doesnt have periods
    result = seed[1:]

    # iterate
    for period in range(PERIODS-MEMORY):
        x = np.array([[period + MEMORY] + result[-MEMORY:]])
        print(x)
        distribution = model.predict(x, verbose=0)[0]
        label = sample(distribution, 0.5)
        result.append(label)
    return seed, result

def sample(distribution, temperature):
    """Samples an index given a probability distribution"""
    a = np.log(distribution) / temperature
    p = np.exp(a) / np.sum(np.exp(a))
    choices = range(len(distribution))      # array of indexes
    return np.random.choice(choices, p=p)    # select an index based on the probabilities of each one


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
    seed, sequence = generate()
    log.info("--> done")
    print(seed)
    print(sequence)
    print(len(sequence))
    drawer.sequence(sequence, "result")

