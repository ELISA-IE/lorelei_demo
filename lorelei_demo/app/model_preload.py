#!/usr/bin/env python

import torch
import os
import sys
import time
import codecs
import numpy as np

# add name tagger module path to PATH
import lorelei_demo.name_tagger.theano
import lorelei_demo.name_tagger.dnn_pytorch
theano_tagger_path = os.path.dirname(lorelei_demo.name_tagger.theano.__file__)
pytorch_tagger_path = os.path.dirname(lorelei_demo.name_tagger.dnn_pytorch.__file__)
sys.path.insert(0, theano_tagger_path)
sys.path.insert(0, pytorch_tagger_path)

from lorelei_demo.name_tagger.theano.loader import prepare_sentence, load_sentences
from lorelei_demo.name_tagger.theano.utils import create_input, iobes_iob
from lorelei_demo.name_tagger.theano.external_feats.generate_features import generate_features

from lorelei_demo.name_tagger.dnn_pytorch.dnn_pytorch.seq_labeling.nn import SeqLabeling
from lorelei_demo.name_tagger.dnn_pytorch.dnn_pytorch.seq_labeling.loader import prepare_dataset, load_sentences
from lorelei_demo.name_tagger.dnn_pytorch.dnn_pytorch.seq_labeling.utils import create_input, iobes_iob

from lorelei_demo.transliteration.transliteration import load_model

from lorelei_demo.app import lorelei_demo_dir


#
# pytorch taggers
#
def pytorch_preload(status):
    models = {}

    for lang_code, s in list(status.items())[:]:
        # if lang_code not in ['ar', 'am', 'fa', 'ha', 'hu', 'so', 'tr', 'uz', 'vi', 'yo', 'ti', 'om']:
        #     continue
        if s[1] == 'online':
            model_dir = os.path.join(
                lorelei_demo_dir,
                'data/name_tagger/pytorch_models/%s/' % lang_code
            )
            model_path = None
            for root, d, f in os.walk(model_dir):
                if 'best_model.pth.tar' in f:
                    model_path = os.path.join(root, 'best_model.pth.tar')
                    break
            assert model_path, '%s model path not exists' % lang_code

            print("=> Preloading model for %s" % lang_code)
            models[lang_code] = pytorch_load_model(model_path)

    print('%d models are preloaded:' % len(models))
    print(', '.join(list(models.keys())))
    return models


def pytorch_load_model(model_path):
    # Load existing model
    state = torch.load(model_path, map_location=lambda storage, loc: storage)

    parameters = state['parameters']
    mappings = state['mappings']

    # Load reverse mappings
    word_to_id, char_to_id, tag_to_id = [
        {v: k for k, v in x.items()}
        for x in [mappings['id_to_word'], mappings['id_to_char'],
                  mappings['id_to_tag']]
        ]
    feat_to_id_list = [
        {v: k for k, v in id_to_feat.items()}
        for id_to_feat in mappings['id_to_feat_list']
        ]

    mappings.update(
        {'word_to_id': word_to_id,
         'char_to_id': char_to_id,
         'tag_to_id': tag_to_id,
         'feat_to_id_list': feat_to_id_list}
    )

    # initialize model
    model = SeqLabeling(parameters)
    model.load_state_dict(state['state_dict'])
    model.train(False)

    return model, parameters, mappings


def pytorch_tag(input, output, model, parameters, mappings):
    word_to_id = mappings['word_to_id']
    char_to_id = mappings['char_to_id']
    tag_to_id = mappings['tag_to_id']
    id_to_tag = mappings['id_to_tag']
    feat_to_id_list = mappings['feat_to_id_list']

    # eval sentences
    eval_sentences = load_sentences(
        input,
        parameters['lower'],
        parameters['zeros']
    )

    eval_dataset = prepare_dataset(
        eval_sentences, parameters['feat_column'],
        word_to_id, char_to_id, tag_to_id, feat_to_id_list, parameters['lower'],
        is_train=False
    )

    # tagging
    since = time.time()
    batch_size = parameters['batch_size']
    f_output = open(output, 'w')

    # Iterate over data.
    print('tagging...')
    for i in range(0, len(eval_dataset), batch_size):
        inputs = create_input(eval_dataset[i:i + batch_size], parameters,
                              add_label=False)

        # forward
        outputs, loss = model.forward(inputs)

        seq_index_mapping = inputs['seq_index_mapping']
        seq_len = inputs['seq_len']
        if parameters['crf']:
            preds = [outputs[seq_index_mapping[j]].data
                     for j in range(len(outputs))]
        else:
            _, _preds = torch.max(outputs.data, 2)

            preds = [
                _preds[seq_index_mapping[j]][:seq_len[seq_index_mapping[j]]]
                for j in range(len(seq_index_mapping))
                ]
        for j, pred in enumerate(preds):
            pred = [id_to_tag[p] for p in pred]
            # Output tags in the IOB2 format
            if parameters['tag_scheme'] == 'iobes':
                pred = iobes_iob(pred)
            # Write tags
            assert len(pred) == len(eval_sentences[i + j])
            f_output.write('%s\n\n' % '\n'.join('%s%s%s' % (' '.join(w), ' ', z)
                                                for w, z in
                                                zip(eval_sentences[i + j],
                                                    pred)))
            if (i + j + 1) % 500 == 0:
                print(i + j + 1)

    end = time.time()  # epoch end time
    print('time elapssed: %f seconds' % round(
        (end - since), 2))


def transliteration_preload():
    preloaded_models = dict()
    model_dir = os.path.join(
        lorelei_demo_dir, 'lorelei_demo/transliteration/data/model/'
    )
    for lang in os.listdir(model_dir):
        preloaded_models[lang] = trans_preload(lang)

    return preloaded_models


def trans_preload(lang):
    model_dir = os.path.join(
        lorelei_demo_dir, 'lorelei_demo/transliteration/data/model/', lang
    )
    if not os.path.exists(model_dir):
        return None
    for file in os.listdir(model_dir):
        if not file.endswith('.model.txt'):
            continue
        model_path = os.path.join(model_dir, file)
        candidates, pair_trans_prob, pair_freq = load_model(
            model_path, ignore_case=True
        )
        return (candidates, pair_trans_prob, pair_freq)


#
# theano taggers
#
# def preload_models():
#     status = get_status()
#
#     models = {}
#
#     for lang_code, s in list(status.items())[:]:
#         # if lang_code not in ['ar', 'am', 'fa', 'ha', 'hu', 'so', 'tr', 'uz', 'vi', 'yo', 'ti', 'om']:
#         #     continue
#         if s[1] == 'online':
#             model_dir = os.path.join(
#                 lorelei_demo_dir,
#                 'data/name_tagger/models/%s/model/' % lang_code
#             )
#
#             # Check parameters validity
#             assert os.path.isdir(model_dir)
#
#             # Load existing model
#             print("=> Preloading model for %s" % lang_code)
#             model = Model(model_path=model_dir)
#             parameters = model.parameters
#
#             # compatible to previously trained model
#             if 'feat_dim' not in parameters: parameters['feat_dim'] = 0
#             if 'comb_method' not in parameters: parameters['comb_method'] = ''
#             if 'upenn_stem' not in parameters: parameters['upenn_stem'] = ''
#             if 'pos_model' not in parameters: parameters['pos_model'] = ''
#             if 'brown_cluster' not in parameters: parameters[
#                 'brown_cluster'] = ''
#             if 'ying_stem' not in parameters: parameters['ying_stem'] = ''
#             if 'gaz' not in parameters: parameters['gaz'] = ''
#             if 'conv' not in parameters: parameters['conv'] = 0
#
#             # Load reverse mappings
#             word_to_id, char_to_id, tag_to_id = [
#                 {v: k for k, v in x.items()}
#                 for x in [model.id_to_word, model.id_to_char, model.id_to_tag]
#                 ]
#             feat_to_id_list = [
#                 {v: k for k, v in id_to_feat.items()}
#                 for id_to_feat in model.id_to_feat_list
#                 ]
#
#             # Load the model
#             _, f_eval = model.build(training=False, **parameters)
#             model.reload()
#
#             mapping = {'word_to_id': word_to_id,
#                        'char_to_id': char_to_id,
#                        'tag_to_id': tag_to_id,
#                        'id_to_tag': model.id_to_tag,
#                        'feat_to_id_list': feat_to_id_list}
#
#             models[lang_code] = (f_eval, parameters, mapping)
#
#     print('%d models are preloaded:' % len(models))
#     print(', '.join(list(models.keys())))
#     return models


def inference(input, output, f_eval, parameters, mappping):
    word_to_id = mappping['word_to_id']
    char_to_id = mappping['char_to_id']
    id_to_tag = mappping['id_to_tag']
    feat_to_id_list = mappping['feat_to_id_list']

    # eval sentences
    eval_sentences = load_sentences(input,
                                    parameters['lower'],
                                    parameters['zeros'])

    # generate features
    eval_feats, eval_stem = generate_features(eval_sentences, parameters)

    f_output = codecs.open(output, 'w', 'utf-8')
    start = time.time()

    #
    # input is bio formatted file
    #
    print('Tagging...')
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

        y_preds = [id_to_tag[y_pred] for y_pred in y_preds]
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
