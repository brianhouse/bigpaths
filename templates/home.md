## FOLLOWING PIECE
<div id="status"><a href="javascript:getLocation();">Generate next location</a></div>  

### Concept

Over a period of one year, I continuously track the GPS location of ~1000 anonymous volunteers in NYC, at all times, via a custom mobile app. 

I use these data to train a deep neural network, an artificial intelligence algorithm similar to what is used for self-driving cars, realistic computer voices, predictive policing, and myriad other emerging applications. 

This algorithm is subsequently able to generate new paths around NYC that synthesize the daily behaviors of the volunteers. 

In the spirit of Vito Acconci's [Following Piece](http://www.metmuseum.org/art/collection/search/283737) or Sophie Calle's [Suite Vénitienne](http://www.artcritical.com/2015/07/16/emmalea-russo-on-sophie-calle/), I then follow this path through the city for one week, documenting as I go the daily life I encounter, and (re-)inscribing these times and places with my own lived experience.

The intelligence of AI is not spontaneous, but enculturated. It is uncanny not because it acts _as if_ it were human, but because it _is_ humans. AI is an ensemble of embodied experiences. These may be subsumed into the whole, but the whole is a trace of its parts.

A dataset of movement around the city means that trace is literal. In following it, I experience something neither abstract nor neutral, but a repetition, with difference, of what came before.


### Tech

Data was collected via a project on the [OpenPaths](https://openpaths.cc) platform. **

The model was trained using [Torch](http://torch.ch/) and a two-layer recurrent neural network ([LSTM](https://en.wikipedia.org/wiki/Long_short-term_memory)) running on an Amazon EC2 instance with GPU acceleration (NVIDIA K80). Training took about a day. It has a sequence history of around two hours, meaning that it readily demonstrates a concept of "home" and "work", for example, but it won't remember where these places were the prior day, or even before lunch.

This service is running on a (lower-powered) EC2 instance via nginx/Tornado with a message queue for LuaJIT generation from the trained model.


### Who

Research by [Brian House](http://brianhouse.net).

** Incidentally, I co-founded OP and coded the platform, but Ive not been directly involved since 2012. It is unfortunately rotting away, but still collects good data from a large number (8k+) of users. I would love for it or an alternative to be revived for art/research like this.