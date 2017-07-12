#!/usr/bin/env python3

import sys, random
import numpy as np
from housepy import config, log, util
from keras.models import Sequential
from keras.layers.recurrent import LSTM
from keras.layers.core import Dense, Activation, Dropout
from keras.callbacks import ModelCheckpoint
from keras.utils import to_categorical

PATH = "1499874653_train_144.pkl"
PATH = "wonderland_train_20.pkl"
MODEL = None

slug = PATH.split('_')[0].split('.')[0].replace("_train", "")
log.info("Loading training data from %s..." % PATH)
X, y, characters, (character_to_label, label_to_character) = util.load("data/%s" % PATH)
sequence_length = len(X[0])
log.info("--> loaded")


log.info("Creating model...")
model = Sequential()
model.add(LSTM(512, return_sequences=True, input_shape=X[0].shape))
model.add(Dropout(0.2))
model.add(LSTM(512, return_sequences=False))
model.add(Dropout(0.2))
model.add(Dense(len(characters), activation=('softmax')))
model.compile(loss='categorical_crossentropy', optimizer='rmsprop')
model.summary()
log.info("--> ready")


if MODEL is not None:
    log.info("Loading saved weights %s..." % MODEL)
    model.load_weights(MODEL)
    log.info("--> done")


log.info("Training...")
try:
    callbacks = [ModelCheckpoint(filepath="models/%s-{epoch:02d}-{loss:.4f}.hdf5" % slug, verbose=1, save_best_only=True, monitor="loss", mode="min")]
    model.fit(X, y, epochs=config['epochs'], batch_size=config['batch_size'], callbacks=callbacks)
except KeyboardInterrupt:
    print()
log.info("--> done")


log.info("Generating...")

def generate(n):
    result = []
    index = random.choice(range(len(X) - sequence_length))
    x = X[index]
    for i in range(n):
        distribution = model.predict(np.array([x[-sequence_length:]]), verbose=0, batch_size=1)[0]
        y = sample(distribution, config['temperature'])
        x = np.append(x, to_categorical(y, len(characters)), axis=0)
        result.append(label_to_character(y))
    return result

def sample(distribution, temperature): # thx gene
    a = np.log(distribution) / temperature
    p = np.exp(a) / np.sum(np.exp(a))
    choices = range(len(distribution))
    return np.random.choice(choices, p=p)

print(generate(sequence_length * 10))