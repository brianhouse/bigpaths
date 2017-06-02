#!/usr/bin/env python3

import random, sys
import numpy as np
from housepy import config, log
from keras.models import Sequential
from keras.layers.recurrent import LSTM
from keras.layers.core import Dense, Activation, Dropout
from keras.callbacks import ModelCheckpoint
from keras.utils import plot_model

WEIGHTS = None
if len(sys.argv) > 1:
    WEIGHTS = sys.argv[1]

log.info("Creating model...")
model = Sequential()
model.add(LSTM(512, return_sequences=True, input_shape=(sequence_length, len(characters))))     # input-shape matrix of one-hot character array * length of sequence        ## can this work just doubled?
model.add(Dropout(0.2)) # break x% of inputs to the next layer
model.add(LSTM(512, return_sequences=False))
model.add(Dropout(0.2))
model.add(Dense(len(characters), activation=("softmax")))   # set output node activation to softmax for discrete classification problems to pick a class
if WEIGHTS is not None:
    model.load_weights(WEIGHTS)
model.compile(loss="categorical_crossentropy", optimizer="rmsprop", metrics=['accuracy']) # setting for categorical classification
log.info("--> done")