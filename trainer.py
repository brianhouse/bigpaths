#!/usr/bin/env python3

import sys, random
import numpy as np
from housepy import config, log
from keras.models import Sequential
from keras.layers.recurrent import LSTM
from keras.layers.core import Dense, Activation
from keras.callbacks import ModelCheckpoint


slug = corpus.split('_')[0].split('.')[0]
log.info("Loading corpus from %s (%s)..." % (corpus, slug))
corpus = open("data/%s" % config['corpus']).read().lower()
characters = list(set(corpus))
log.info("--> %d unique characters" % len(characters))


log.info("Preparing sequences...")
sequences = []
outputs = []
for i in range(0, len(corpus) - config['sequence_length']):
    sequences.append(corpus[i:i + config['sequence_length']])  # this is the sequence
    outputs.append(corpus[i + config['sequence_length']])      # the expected output is the next character
log.info("--> %d sequences" % len(sequences))


log.info("Creating tensors...")
# mapping between characters and integers
character_to_label = {ch:i for i, ch in enumerate(characters)}
label_to_character = {i:ch for i, ch in enumerate(characters)}    
X = np.zeros((len(sequences), config['sequence_length'], len(characters)), dtype=np.bool)
y = np.zeros((len(sequences), len(characters)), dtype=np.bool)
for i, sequence in enumerate(sequences):
    for t, character in enumerate(sequence):
        X[i, t, character_to_label[character]] = 1
    y[i, character_to_label[outputs[i]]] = 1


log.info("Creating model...")
model = Sequential()
model.add(LSTM(512, return_sequences=True, input_shape=X[0].shape))
model.add(Dropout(0.2))
model.add(LSTM(512, return_sequences=False))
model.add(Dropout(0.2))
model.add(Dense(len(characters), activation=('softmax')))
if WEIGHTS is not None:
    model.load_weights(WEIGHTS)
model.compile(loss='categorical_crossentropy', optimizer='rmsprop')
model.summary()
log.info("--> ready")


log.info("Training...")
try:
    callbacks = [ModelCheckpoint(filepath="models/%s-{epoch:02d}-{loss:.4f}.hdf5" % slug, verbose=1, save_best_only=True, monitor="loss", mode="min")]
    model.fit(X, y, epochs=config['epochs'], batch_size=config['batch_size'], callbacks=callbacks)
except KeyboardInterrupt:
    print()
log.info("--> done")

