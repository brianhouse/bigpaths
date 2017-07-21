## FOLLOWING PIECE
<div id="status"><a href="javascript:getLocation();">Generate next location</a></div>  

### Concept

An AI often uses data from a large group of people to learn how to behave. 

The specifics of those people -- who they are, their individual experiences, their collective biases -- are obscured. An AI seems like a "black box" without a body, and gives the impression that its intelligence is spontaneous, rather than enculturated.

But the uncanniness of an AI is not that it acts _as if_ it were human, but that it _is_ human. It is an ensemble of embodied experiences whose parts may be subsumed into the whole, but of which that whole is still a trace.

That trace might become literal, given a dataset of movement around the city. In 1969, Vito Acconci [followed](http://www.metmuseum.org/art/collection/search/283737) stangers around NYC streets, surrendering to their logics of navigating public space. What if I did the same with an AI? That is, follow an AI that is itself following hundreds of people, at once, having amalgamated their tracks into its own "novel" idea of NYC life?

/

Using a mobile app, I collected continuous location data on 606 anonymous volunteers living in NYC over a three year period. Whenever any of them moved further than 100ft I logged a point. Segmenting them into "days" -- the path of a single individual over a 24-hour period -- gave me a training set of half a million examples of daily routines.  

I used these data to train a deep learning algorithm, producing an AI that when given a location knows where (and when) to go next.

/

The plan, from here, is to use this for a durational performance in NYC. I'll follow the AI for a week, riffing (again) on its rhythms. Taking a cue from [Sophie Calle](http://www.artcritical.com/2015/07/16/emmalea-russo-on-sophie-calle/), I'll get as close as I can to the individuals behind it -- I'll photograph what might be their workplace, their favorite coffee shop or dreaded clinic, or imagine that they might live behind this unmarked door -- while simultaneously (re-)inscribing these locations with my own lived experiences.

I'm rehearsing with an ensemble that might be obfuscated but which is neither abstract nor neutral. Vito said, "I am almost not an 'I' anymore; I put myself in the service of this scheme." He consciously surrendered control. As AI moves into everyday life, do we?


### Technical

Data was collected via a project on the [OpenPaths](https://openpaths.cc) platform. **

The model was trained using [Torch](http://torch.ch/) and a two-layer recurrent neural network ([LSTM](https://en.wikipedia.org/wiki/Long_short-term_memory)) running on an Amazon EC2 instance with GPU acceleration (NVIDIA K80). Training took about a day.  

This service is running on a (lower-powered) EC2 instance via nginx/Tornado with a message queue for LuaJIT generation from the trained model.


### Etc

Research by [Brian House](http://brianhouse.net).

** Incidentally, I co-founded OP, but have not been directly involved since 2012. It is unfortunately rotting away, but still collects good data from a large number (8k+) of users. I would love for it or an alternative to be revived for art/research like this.