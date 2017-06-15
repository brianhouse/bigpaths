- for directions, prioritize destination times (which is intuitive anyway)

- for strips, use grid=6

- test training with grid=7

- for actual printing, need vector map, b&w, light grey paths with time labels

- for just my dataset, two LSTM layers of 256 nodes seemed to work great, but on the full dataset, I feel like that's too small. the bigger the better, but the bigger need more data. so that makes sense. Karpathy mentions a 3-layer LSTM with around 10million parameters that took a few days to train. this model is 10.5million, 3 layers of 512 nodes, and a couple days. so I'm in the right ballpark.

- eliminating dropout. unless we're hitting 100% on accuracy, overfitting isnt a problem, because there is no validation set. and even then, temperature will prevent it from reproducing exact training paths. they will be amalgamations, as desired, and the stochastics will further fuzz it.

- basing this on training accuracy. if it can learn to predict accurately over the training set, it's a valid claim that's it's learned from the data and the subsequent generations reflect that.