#!/usr/bin/env python3

import sys, random
import numpy as np
from housepy import config, log, util
from keras.models import Sequential
from keras.layers.recurrent import LSTM
from keras.layers.core import Dense, Activation, Dropout
from keras.callbacks import ModelCheckpoint
from keras.utils import to_categorical


if len(sys.argv) < 2:
    print("[train] [model]")
    exit()
path = sys.argv[1]
model_path = sys.argv[2] if len(sys.argv) > 2 else None
slug = path.split('.')[0].replace("_train", "")
log.info("Loading training data from %s..." % path)
X, y, characters, (character_to_label, label_to_character) = util.load("data/%s" % path)
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


if model_path is None:
    log.info("Training...")
    try:
        callbacks = [ModelCheckpoint(filepath="models/%s-{epoch:02d}-{loss:.4f}.hdf5" % slug, verbose=1, save_best_only=True, monitor="loss", mode="min")]
        model.fit(X, y, epochs=config['epochs'], batch_size=config['batch_size'], callbacks=callbacks)
    except KeyboardInterrupt:
        print()
    log.info("--> done")


if model_path is not None:
    log.info("Loading saved weights %s..." % model_path)
    model.load_weights("models/%s" % model_path)
    log.info("--> done")


log.info("Generating...")

def generate(n):
    result = []
    index = random.choice(range(len(X) - sequence_length))
    x = X[index]
    for i in range(n):
        log.info(i)
        distribution = model.predict(np.array([x[-sequence_length:]]), verbose=0, batch_size=1)[0]
        y = sample(distribution, config['temperature'])
        x = np.append(x, to_categorical(y, len(characters)), axis=0)
        result.append(label_to_character[y])
    return "".join(result)

def sample(distribution, temperature): # thx gene
    a = np.log(distribution) / temperature
    p = np.exp(a) / np.sum(np.exp(a))
    choices = range(len(distribution))
    return np.random.choice(choices, p=p)

output = generate(sequence_length * 100)
util.save("data/%s_%s_output.txt" % (slug, config['temperature']), output)