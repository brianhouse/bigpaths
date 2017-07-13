#!/usr/bin/env python3

import sys, random, h5py
import numpy as np
from housepy import config, log
from keras.models import Sequential
from keras.layers.recurrent import LSTM
from keras.layers.core import Dense, Activation, Dropout
from keras.callbacks import ModelCheckpoint
from keras.utils import to_categorical
from tqdm import tqdm

EPOCHS = 100
BATCH_SIZE = 64

if len(sys.argv) < 2:
    print("[input] [model]")
    exit()
path = sys.argv[1]
model_path = sys.argv[2] if len(sys.argv) > 2 else None
slug = path.split('.')[0].replace("_input", "")
log.info("Loading training data from %s..." % path)
with h5py.File("data/%s" % path) as f:
    X = f['X'][:]
    y = f['y'][:]
    categories = int(f['categories'][:])
    label_to_character = list(f['label_to_character'][:])
    label_to_character = [ch.decode() for ch in label_to_character]
sequence_length = len(X[0])
log.info("--> loaded")


log.info("Creating model...")
model = Sequential()
model.add(LSTM(512, return_sequences=True, input_shape=X[0].shape))
model.add(Dropout(0.2))
model.add(LSTM(512, return_sequences=False))
model.add(Dropout(0.2))
model.add(Dense(categories, activation=('softmax')))
model.compile(loss='categorical_crossentropy', optimizer='rmsprop')
model.summary()
log.info("--> ready")


if model_path is None:
    log.info("Training...")
    try:
        callbacks = [ModelCheckpoint(filepath="models/%s-{epoch:02d}-{loss:.4f}.hdf5" % slug, verbose=1, save_best_only=True, monitor="loss", mode="min")]
        model.fit(X, y, epochs=EPOCHS, batch_size=64, callbacks=callbacks)
    except KeyboardInterrupt:
        print()
    log.info("--> done")


if model_path is not None:
    log.info("Loading saved weights %s..." % model_path)
    model.load_weights("models/%s" % model_path)
    log.info("--> done")


log.info("Generating...")

def generate():
    result = []
    index = random.choice(range(len(X) - sequence_length))
    x = X[index]
    for i in tqdm(range(sequence_length)):
        distribution = model.predict(np.array([x[-sequence_length:]]), verbose=0, batch_size=1)[0]
        y = sample(distribution, config['temperature'])
        x = np.append(x, to_categorical(y, categories), axis=0)
        result.append(label_to_character[y])
    return "".join(result)

def sample(distribution, temperature): # thx gene
    a = np.log(distribution) / temperature
    p = np.exp(a) / np.sum(np.exp(a))
    choices = range(len(distribution))
    return np.random.choice(choices, p=p)

output = []
for i in range(10):
    output.append(generate())
output = ".".join(output)
path = "data/%s_%s.txt" % (slug.replace("_", "_output_"), config['temperature'])
with open(path, 'w') as f:
    f.write(output)
log.info("--> saved %s" % path)