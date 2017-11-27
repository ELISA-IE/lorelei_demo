#!/usr/bin/env python

import os
import time
import codecs
import optparse
import loader
import numpy as np
from loader import prepare_sentence
from utils import create_input, iobes_iob, zero_digits
from model import Model
from external_feats.generate_features import generate_features


optparser = optparse.OptionParser()
optparser.add_option(
    "-m", "--model", default="",
    help="Model location"
)
optparser.add_option(
    "-i", "--input", default="",
    help="Input file location"
)
optparser.add_option(
    "-o", "--output", default="",
    help="Output file location"
)
optparser.add_option(
    "-d", "--delimiter", default="__",
    help="Delimiter to separate words from their tags"
)
opts = optparser.parse_args()[0]

# Check parameters validity
assert opts.delimiter
assert os.path.isdir(opts.model)
assert os.path.isfile(opts.input)

# Load existing model
print("Loading model...")
model = Model(model_path=opts.model)
parameters = model.parameters

# compatible to previously trained model
if 'feat_dim' not in parameters: parameters['feat_dim'] = 0
if 'comb_method' not in parameters: parameters['comb_method'] = ''
if 'upenn_stem' not in parameters: parameters['upenn_stem'] = ''
if 'pos_model' not in parameters: parameters['pos_model'] = ''
if 'brown_cluster' not in parameters: parameters['brown_cluster'] = ''
if 'ying_stem' not in parameters: parameters['ying_stem'] = ''
if 'gaz' not in parameters: parameters['gaz'] = ''
if 'conv' not in parameters: parameters['conv'] = 0

# Load reverse mappings
word_to_id, char_to_id, tag_to_id = [
    {v: k for k, v in x.items()}
    for x in [model.id_to_word, model.id_to_char, model.id_to_tag]
    ]
feat_to_id_list = [
    {v: k for k, v in id_to_feat.items()}
    for id_to_feat in model.id_to_feat_list
    ]

# Load the model
_, f_eval = model.build(training=False, **parameters)
model.reload()

f_output = codecs.open(opts.output, 'w', 'utf-8')
start = time.time()

# eval sentences
eval_sentences = loader.load_sentences(opts.input,
                                       parameters['lower'],
                                       parameters['zeros'])

# generate features
eval_feats, eval_stem = generate_features(eval_sentences, parameters)

#
# input is bio formatted file
#
print('Tagging...')
with codecs.open(opts.input, 'r', 'utf-8') as f_input:
    count = 0
    for i, raw_sentence in enumerate(eval_sentences):
        # Prepare input
        if eval_feats:
            s_feat = eval_feats[i]
        else:
            s_feat = []
        if eval_stem:
            s_stem = eval_stem[i]
        else:
            s_stem = []
        sentence = prepare_sentence(raw_sentence, s_feat, s_stem,
                                    word_to_id, char_to_id, None, feat_to_id_list,
                                    lower=parameters['lower'], is_train=False)
        input = create_input(sentence, parameters, False)
        # Decoding
        if parameters['crf']:
            y_preds = np.array(f_eval(*input))[1:-1]
        else:
            y_preds = f_eval(*input).argmax(axis=1)

        y_preds = [model.id_to_tag[y_pred] for y_pred in y_preds]
        # Output tags in the IOB2 format
        if parameters['tag_scheme'] == 'iobes':
            y_preds = iobes_iob(y_preds)
        # Write tags
        assert len(y_preds) == len(sentence['words'])
        f_output.write('%s\n\n' % '\n'.join('%s%s%s' % (' '.join(w), ' ', z)
                                            for w, z in zip(raw_sentence,
                                                            y_preds)))
        count += 1
        if count % 500 == 0:
            print(count)
print('---- %i lines tagged in %.4fs ----' % (count, time.time() - start))
f_output.close()
