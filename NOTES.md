- for directions, prioritize destination times (which is intuitive anyway)

- for strips, use grid=6

- for actual printing, need vector map, b&w, light grey paths with time labels

- test training with grid=7

- for just my dataset, two LSTM layers of 256 nodes seemed to work great, but on the full dataset, I feel like that's too small. the bigger the better, but the bigger need more data. so that makes sense. Karpathy mentions a 3-layer LSTM with around 10million parameters that took a few days to train. this model is 10.5million, 3 layers, and a couple days. so I'm in the right ballpark.