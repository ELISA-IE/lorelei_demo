#!/usr/bin/env python

import os
import numpy as np
import argparse
import itertools
import time
import sys
from collections import OrderedDict
from utils import create_input, Tee
import loader

# from utils import models_path, evaluate, eval_script, eval_temp
from utils import evaluate, eval_script, eval_temp  # Boliang: use arg model path
from loader import word_mapping, char_mapping, tag_mapping, feats_mapping
from loader import update_tag_scheme, prepare_dataset
from loader import augment_with_pretrained
from model import Model

# external features
from external_feats.generate_features import generate_features


# Read parameters from command line
parser = argparse.ArgumentParser()
parser.add_argument(
    "-T", "--train", default="",
    help="Train set location"
)
parser.add_argument(
    "-d", "--dev", default="",
    help="Dev set location"
)
parser.add_argument(
    "-t", "--test", default="",
    help="Test set location"
)
parser.add_argument(
    "-m", "--model_dp", default="",
    help="model directory path"
)
parser.add_argument(
    "-s", "--tag_scheme", default="iobes",
    help="Tagging scheme (IOB or IOBES)"
)
parser.add_argument(
    "-l", "--lower", default='0',
    type=int, help="Lowercase words (this will not affect character inputs)"
)
parser.add_argument(
    "-z", "--zeros", default="0",
    type=int, help="Replace digits with 0"
)
parser.add_argument(
    "-c", "--char_dim", default="25",
    type=int, help="Char embedding dimension"
)
parser.add_argument(
    "-C", "--char_lstm_dim", default="25",
    type=int, help="Char LSTM hidden layer size"
)
parser.add_argument(
    "-b", "--char_bidirect", default="1",
    type=int, help="Use a bidirectional LSTM for chars"
)
parser.add_argument(
    "-w", "--word_dim", default="100",
    type=int, help="Token embedding dimension"
)
parser.add_argument(
    "-W", "--word_lstm_dim", default="100",
    type=int, help="Token LSTM hidden layer size"
)
parser.add_argument(
    "-B", "--word_bidirect", default="1",
    type=int, help="Use a bidirectional LSTM for words"
)
parser.add_argument(
    "-p", "--pre_emb", default="",
    help="Location of pretrained embeddings"
)
parser.add_argument(
    "-A", "--all_emb", default="0",
    type=int, help="Load all embeddings"
)
parser.add_argument(
    "-a", "--cap_dim", default="0",
    type=int, help="Capitalization feature dimension (0 to disable)"
)
parser.add_argument(
    "-f", "--crf", default="1",
    type=int, help="Use CRF (0 to disable)"
)
parser.add_argument(
    "-V", "--conv", default="1",
    type=int, help="Use CNN to generate character embeddings. (0 to disable)"
)
parser.add_argument(
    "-D", "--dropout", default="0.5",
    type=float, help="Droupout on the input (0 = no dropout)"
)
parser.add_argument(
    "-L", "--lr_method", default="sgd-lr_.005",
    help="Learning method (SGD, Adadelta, Adam..)"
)
parser.add_argument(
    "-r", "--reload", default="0",
    type=int, help="Reload the last saved model"
)
#
# external features
#
parser.add_argument(
    "--feat_dim", default="0",
    type=int, help="dimension for each feature."
)
parser.add_argument(
    "--comb_method", default="0",
    type=int, help="combination method. (1, 2, 3 or 4)"
)
parser.add_argument(
    "--upenn_stem", default="",
    help="path of upenn morphology analysis result."
)
parser.add_argument(
    "--pos_model", default="",
    help="path of pos tagger model."
)
parser.add_argument(
    "--brown_cluster", default="",
    help="path of brown cluster paths."
)
parser.add_argument(
    "--ying_stem", default="",
    help="path of Ying's stemming result."
)
parser.add_argument(
    "--gaz", default="", nargs="+",
    help="gazetteers paths."
)

args = parser.parse_args()

# Parse parameters
parameters = OrderedDict()
parameters['tag_scheme'] = args.tag_scheme
parameters['lower'] = args.lower == 1
parameters['zeros'] = args.zeros == 1
parameters['char_dim'] = args.char_dim
parameters['char_lstm_dim'] = args.char_lstm_dim
parameters['char_bidirect'] = args.char_bidirect == 1
parameters['word_dim'] = args.word_dim
parameters['word_lstm_dim'] = args.word_lstm_dim
parameters['word_bidirect'] = args.word_bidirect == 1
parameters['pre_emb'] = args.pre_emb
parameters['all_emb'] = args.all_emb == 1
parameters['cap_dim'] = args.cap_dim
parameters['crf'] = args.crf == 1
parameters['conv'] = args.conv == 1
parameters['dropout'] = args.dropout
parameters['lr_method'] = args.lr_method
# external features
parameters['feat_dim'] = args.feat_dim
parameters['comb_method'] = args.comb_method
parameters['upenn_stem'] = args.upenn_stem
parameters['pos_model'] = args.pos_model
parameters['brown_cluster'] = args.brown_cluster
parameters['ying_stem'] = args.ying_stem
parameters['gaz'] = args.gaz

# Check parameters validity
assert os.path.isfile(args.train)
assert os.path.isfile(args.dev)
assert os.path.isfile(args.test)
assert parameters['char_dim'] > 0 or parameters['word_dim'] > 0 or parameters['exp_feat_dim'] > 0
assert 0. <= parameters['dropout'] < 1.0
assert parameters['tag_scheme'] in ['iob', 'iobes', 'classification']
assert not parameters['all_emb'] or parameters['pre_emb']
assert not parameters['pre_emb'] or parameters['word_dim'] > 0
assert not parameters['pre_emb'] or os.path.isfile(parameters['pre_emb'])
if parameters['upenn_stem']:
    assert os.path.exists(parameters['upenn_stem']) and \
           parameters['comb_method'] != 0
if parameters['pos_model']:
    assert os.path.exists(parameters['pos_model']) and \
           parameters['comb_method'] != 0
if parameters['brown_cluster']:
    assert os.path.exists(parameters['brown_cluster']) and \
           parameters['comb_method'] != 0
if parameters['ying_stem']:
    assert os.path.exists(parameters['ying_stem']) and \
           parameters['comb_method'] != 0

# Boliang: use arg model path
models_path = args.model_dp

# Check evaluation script / folders
if not os.path.isfile(eval_script):
    raise Exception('CoNLL evaluation script not found at "%s"' % eval_script)
if not os.path.exists(eval_temp):
    os.makedirs(eval_temp)
if not os.path.exists(models_path):
    os.makedirs(models_path)

# Initialize model
model = Model(parameters=parameters, models_path=models_path)

# register logger to save print(messages to both stdout and disk)
training_log_path = os.path.join(model.model_path, 'training_log.txt')
if os.path.exists(training_log_path):
    os.remove(training_log_path)
f = open(training_log_path, 'w')
sys.stdout = Tee(sys.stdout, f)

print('Training data: %s' % args.train)
print('Dev data: %s' % args.dev)
print('Test data: %s' % args.test)
print("Model location: %s" % model.model_path)
print('Model parameters:')
for k, v in parameters.items():
    print('%s=%s' % (k, v))

# Data parameters
lower = parameters['lower']
zeros = parameters['zeros']
tag_scheme = parameters['tag_scheme']

# Load sentences
train_sentences = loader.load_sentences(args.train, lower, zeros)
dev_sentences = loader.load_sentences(args.dev, lower, zeros)
test_sentences = loader.load_sentences(args.test, lower, zeros)

train_sentences = train_sentences[:]
dev_sentences = dev_sentences[:]
test_sentences = test_sentences[:]

# Use selected tagging scheme (IOB / IOBES), also check tagging scheme
update_tag_scheme(train_sentences, tag_scheme)
update_tag_scheme(dev_sentences, tag_scheme)
update_tag_scheme(test_sentences, tag_scheme)

#
# generate external features
#
train_feats, train_stem = generate_features(train_sentences, parameters)
dev_feats, dev_stem = generate_features(dev_sentences, parameters)
test_feats, test_stem = generate_features(test_sentences, parameters)

# Create a dictionary / mapping of words
# If we use pretrained embeddings, we add them to the dictionary.
if parameters['pre_emb']:
    dico_words_train = word_mapping(train_sentences, lower)[0]
    dico_words, word_to_id, id_to_word = augment_with_pretrained(
        dico_words_train.copy(),
        parameters['pre_emb'],
        list(itertools.chain.from_iterable(
            [[w[0] for w in s] for s in dev_sentences + test_sentences])
        ) if not parameters['all_emb'] else None
    )
else:
    dico_words, word_to_id, id_to_word = word_mapping(train_sentences, lower)
    dico_words_train = dico_words

# Create a dictionary and a mapping for words / POS tags / tags
dico_chars, char_to_id, id_to_char = char_mapping(train_sentences)
dico_tags, tag_to_id, id_to_tag = tag_mapping(train_sentences)

# create a dictionary and a mapping for each feature
dico_feats_list, feat_to_id_list, id_to_feat_list = feats_mapping(train_feats)

# Index data
train_data = prepare_dataset(
    train_sentences,
    train_feats, train_stem,
    word_to_id, char_to_id, tag_to_id, feat_to_id_list, lower
)
dev_data = prepare_dataset(
    dev_sentences,
    dev_feats, dev_stem,
    word_to_id, char_to_id, tag_to_id, feat_to_id_list, lower
)
test_data = prepare_dataset(
    test_sentences,
    test_feats, test_stem,
    word_to_id, char_to_id, tag_to_id, feat_to_id_list, lower
)

print("%i / %i / %i sentences in train / dev / test." % (
    len(train_data), len(dev_data), len(test_data)))

# Save the mappings to disk
print('Saving the mappings to disk...')
model.save_mappings(id_to_word, id_to_char, id_to_tag, id_to_feat_list)

# Build the model
f_train, f_eval = model.build(**parameters)

# Reload previous model values
if args.reload:
    print('Reloading previous model...')
    model.reload()

#
# Train network
#
singletons = set([word_to_id[k] for k, v
                  in dico_words_train.items() if v == 1])
n_epochs = 100  # number of epochs over the training set
# n_epochs = 200
freq_eval = 10000  # evaluate on dev every freq_eval steps
if freq_eval > len(train_data):
    freq_eval = len(train_data)

# freq_eval = 5000
best_dev = -np.inf
best_test = -np.inf
best_dev_acc = -np.inf
best_test_acc = -np.inf
count = 0
for epoch in range(n_epochs):
    epoch_costs = []
    print("Starting epoch %i..." % epoch)
    time_epoch_start = time.time()  # epoch start time
    # for i, index in enumerate(np.random.permutation(len(train_data))):
    for i, index in enumerate(np.random.permutation(len(train_data))):
        count += 1
        input = create_input(train_data[index], parameters, True, singletons)
        new_cost = f_train(*input)
        epoch_costs.append(new_cost)

        sys.stdout.write("%i, cost average: %f\r" % (i+1, np.mean(epoch_costs)))
        sys.stdout.flush()

        if count % freq_eval == 0:
            dev_score, dev_acc = evaluate(parameters, f_eval, dev_sentences,
                                          dev_data, id_to_tag, dico_tags,
                                          eval_out_dir=model.model_path)
            test_score, test_acc = evaluate(parameters, f_eval, test_sentences,
                                            test_data, id_to_tag, dico_tags,
                                            eval_out_dir=model.model_path)

            #
            # save model based on dev f1 score
            #
            print("Score on dev: %.5f" % dev_score)
            # print("Score on test: %.5f" % test_score)
            if dev_score > best_dev:
                best_dev = dev_score
                print("New best score on dev.")
                print("Saving model to disk...")
                model.save()
            if test_score > best_test:
                best_test = test_score
                print("New best score on test.")

                #
                # save model based on dev accuracy
                #
                # print("Accuracy on dev: %.5f" % dev_acc)
                # print("Accuracy on test: %.5f" % test_acc)
                # if dev_acc > best_dev_acc:
                #     best_dev_acc = dev_acc
                #     print("New best accuracy on dev.")
                #     print("Saving model to disk...")
                #     model.save()
                # if test_score > best_test_acc:
                #     best_test_acc = test_score
                #     print("New best accuracy on test.")

    print("Epoch %i done. Average cost: %f" % (epoch, np.mean(epoch_costs)))
    time_epoch_end = time.time()  # epoch end time
    print('epoch training time: %f seconds' % round((time_epoch_end - time_epoch_start), 2))

print('DNN training is finished.')
