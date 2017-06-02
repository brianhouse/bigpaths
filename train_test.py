#!/usr/bin/env python3

import random, sys
import numpy as np
from housepy import config, log
from keras.models import Sequential
from keras.layers.recurrent import LSTM
from keras.layers.core import Dense, Activation, Dropout
from keras.callbacks import ModelCheckpoint
from keras.utils import plot_model
from data import *

WEIGHTS = None
if len(sys.argv) > 1:
    WEIGHTS = sys.argv[1]

corpus = util.load("sequences_house.pkl")

# split the dataset into moving sequences
log.info("Generating training sequences...")
sequence_length = PERIODS
sequences = []
outputs = []
for i in range(0, len(corpus) - sequence_length):
    sequences.append(corpus[i:i + sequence_length])  # this is the sequence
    outputs.append(corpus[i + sequence_length])   # the expected output is the next lonlat
log.info("--> %d sequences" % len(sequences)) 

# make an empty 3-tensor for the input sequences
X = np.zeros((len(sequences), sequence_length, 2), dtype=np.float)

# make an empty tensor for the output (which is just 2d, a lonlat for each input sequence)
y = np.zeros((len(sequences), 2), dtype=np.bool)

# set the appropriate indices to 1 in each one-hot vector
for i, sequence in enumerate(sequences):
    for t, character in enumerate(sequence):
        X[i, t, character_to_label[character]] = 1
    y[i, character_to_label[outputs[i]]] = 1



exit()



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