## NER Tagger

This NER Tagger follows the implementation of Guillaume Lample's work of http://arxiv.org/abs/1603.01360

New features:
* adding external features
* Multi-thread support
* Batch support

## Initial setup

To use the tagger, you need Python 2.7, with Numpy and Theano installed.


## Tag sentences

Please see the example at: ```example/tag.sh```

## Train a model

Please see the example at: ```example/train.sh```

To train your own model, you need to use the train.py script and provide the location of the training, development and testing set.

The training script will automatically give a name to the model and store it in the model path you give.
There are many parameters you can tune (CRF, dropout rate, embedding dimension, LSTM hidden layer size, etc). To see all parameters, simply run:

```
./train.py --help
```

Input files for the training script have to follow the same format than the CoNLL2003 sharing task: each word has to be on a separate line, and there must be an empty line after each sentence. A line must contain at least 2 columns, the first one being the word itself, the last one being the named entity. It does not matter if there are extra columns that contain tags or chunks in between. Tags have to be given in the IOB format (it can be IOB1 or IOB2).
