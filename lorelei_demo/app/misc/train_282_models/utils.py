import os
import io
import shutil
import tempfile
import subprocess
import re
import json
import logging
from collections import defaultdict

import sys
import requests
from lorelei_demo.app import lorelei_demo_dir

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


def generate_gold_ann_path():
    logging.info('#')
    logging.info('# Generating gold annotation paths...')
    logging.info('#')
    gold_annotations =defaultdict(dict)

    # ldc gold annotations
    ldc_gold_dir = '/nas/data/m1/zhangb8/lorelei/data/reference/ldc'
    ldc_gold_lang = []
    for lang_code in os.listdir(ldc_gold_dir):
        if lang_code == 'old':  # skioverallp the "old" directory
            continue
        if lang_code == 'ug':
            train = '/nas/data/m1/zhangb8/lorelei/data/reference/ldc/ug/bio/human_ann/combs/all_merged_cleaned_niadju_onlyname.bio'
            dev = '/nas/data/m1/zhangb8/lorelei/data/reference/ldc/ug/bio/unsequestered/unsequestered.bio'
            test = '/nas/data/m1/zhangb8/lorelei/data/reference/ldc/ug/bio/unsequestered/unsequestered.bio'
        else:
            train = os.path.join(ldc_gold_dir, lang_code, 'bio/ldc.train.bio')
            dev = os.path.join(ldc_gold_dir, lang_code, 'bio/ldc.test.bio')
            test = os.path.join(ldc_gold_dir, lang_code, 'bio/ldc.test.bio')

        gold_annotations[lang_code] = {'train': train, 'dev': dev, 'test': test}

        ldc_gold_lang.append(lang_code)
    logging.info('* LDC gold annotations: %s' % ', '.join(ldc_gold_lang))

    # trilingual gold annotations
    zh_train = '/nas/data/m1/zhangb8/kbp_edl/data/edl17/trilingual/cmn/train/edl15_eval+edl15_train+ontonotes.bio'
    zh_dev = '/nas/data/m1/zhangb8/kbp_edl/data/edl17/trilingual/cmn/dev/cmn_edl16_eval_clean.bio'
    zh_test = '/nas/data/m1/zhangb8/kbp_edl/data/edl17/trilingual/cmn/test/eval.gold.bio'
    en_train = '/nas/data/m1/zhangb8/kbp_edl/data/edl17/trilingual/eng/train/old/edl15_eval+edl15_train+ontonotes.bio'
    en_dev = '/nas/data/m1/zhangb8/kbp_edl/data/edl17/trilingual/eng/dev/edl16.eval.nam.bio'
    en_test = '/nas/data/m1/zhangb8/kbp_edl/data/edl17/trilingual/eng/test/edl17.eval.nam.bio'
    es_train = '/nas/data/m1/zhangb8/kbp_edl/data/edl17/trilingual/spa/train/edl15_eval+edl15_train+conll02+lrlp.bio'
    es_dev = '/nas/data/m1/zhangb8/kbp_edl/data/edl17/trilingual/spa/dev/spa_edl16_eval_clean.bio'
    es_test = '/nas/data/m1/zhangb8/kbp_edl/data/edl17/trilingual/spa/test/eval.gold.bio'
    gold_annotations['zh'] = {'train': zh_train, 'dev': zh_dev, 'test': zh_test}
    gold_annotations['en'] = {'train': en_train, 'dev': en_dev, 'test': en_test}
    gold_annotations['es'] = {'train': es_train, 'dev': es_dev, 'test': es_test}
    logging.info('* Trilingual gold annotations: %s' % ', '.join(gold_annotations))

    # annotation tool gold annotations
    ann_tool_gold_dir = '/nas/data/m1/zhangb8/lorelei/data/reference/ann_tool/archived'
    ann_tool_gold_lang = []
    for lang_code in os.listdir(ann_tool_gold_dir):
        train = os.path.join(ann_tool_gold_dir, lang_code, 'train.bio')
        dev = os.path.join(ann_tool_gold_dir, lang_code, 'test.bio')
        test = os.path.join(ann_tool_gold_dir, lang_code, 'test.bio')

        gold_annotations[lang_code] = {'train': train, 'dev': dev, 'test': test}

        ann_tool_gold_lang.append(lang_code)

    logging.info('* Trilingual gold annotations: %s' % ', '.join(ann_tool_gold_lang))

    # assert all paths exist
    for lang_code, ann in gold_annotations.items():
        for k, path in ann.items():
            assert os.path.exists(path), 'file not exists: %s, %s, %s' % (lang_code, k, path)

    logging.info('= Overall %d languages have gold annotations.' % len(gold_annotations))

    return gold_annotations


def generate_wikiann_ann_path():
    wikiann_dir = os.path.join(lorelei_demo_dir, 'data/app/elisa_ie/il_annotation_300')
    wikiann_annotation = defaultdict(dict)
    for lang_code in os.listdir(wikiann_dir):
        if lang_code.startswith('.'):
            continue
        train = os.path.join(wikiann_dir, lang_code, 'bio/train.bio')
        dev = os.path.join(wikiann_dir, lang_code, 'bio/dev.bio')
        test = os.path.join(wikiann_dir, lang_code, 'bio/test.bio')
        wikiann_annotation[lang_code] = {'train': train, 'dev': dev, 'test': test}

    # assert all paths exist
    for lang_code, ann in wikiann_annotation.items():
        for k, path in ann.items():
            assert os.path.exists(path), 'file not exists: %s, %s, %s' % (
                lang_code, k, path)

    return wikiann_annotation


def generate_pretrained_embedding_path():
    logging.info('#')
    logging.info('# generating pre-trained word embedding paths...')
    logging.info('#')

    emb_path = dict()

    # ldc word embeddings
    ldc_word_emb_dir = '/nas/data/m1/zhangb8/lorelei/data/word_embedding'
    ldc_word_emb = []
    for lang_code in os.listdir(ldc_word_emb_dir):
        if lang_code in emb_path:
            continue
        emb_path[lang_code] = (
        os.path.join(ldc_word_emb_dir, lang_code, 'ldc.emb'), 100)
        ldc_word_emb.append(lang_code)
    logging.info('* ldc word embeddings: %s' % ', '.join(ldc_word_emb))

    # fasttext pre-trained word embeddings
    fasttext_emb_dir = '/nas/data/m1/zhangb8/data/fasttext_emb'
    fasttext_emb = []
    for f_name in os.listdir(fasttext_emb_dir):
        lang_code = f_name.split('.')[1]
        f_path = os.path.join(fasttext_emb_dir, f_name)
        emb_path[lang_code] = (f_path, 300)
        fasttext_emb.append(lang_code)
    logging.info('* fastText word embeddings: %s' % ', '.join(fasttext_emb))

    # trilingual word embeddings
    emb_path['zh'] = ('/nas/data/m1/zhangb8/lorelei/data/word_embedding/zh/cmn.emb', 100)
    emb_path['en'] = ('/nas/data/m1/zhangb8/lorelei/data/word_embedding/en/glove/glove.6B.100d.txt', 100)
    emb_path['es'] = ('/nas/data/m1/zhangb8/lorelei/data/word_embedding/es/spa.emb', 100)
    logging.info('* trilingual word embeddings: %s' % ', '.join(['zh', 'en', 'es']))

    # assert all paths exist
    for lang_code, p in emb_path.items():
        assert os.path.exists(p[0]), 'file not exists: %s, %s' % (lang_code, p)

    logging.info('= Overall %d languages have pre-trained word embeddings.' % len(emb_path))

    return emb_path


def download_fasttext_word_emb():
    logging.info('#')
    logging.info('# Downoading fastText multilingual word embeddings...')
    logging.info('#')
    # load wikipedia language code
    wiki_lang_mapping_fp = os.path.join(
        lorelei_demo_dir, 'data/app/elisa_ie/wikilang_mapping.txt'
    )
    f_wikilang = open(wiki_lang_mapping_fp, encoding="utf8").read().strip()
    wiki_lang_code = set()

    for line in f_wikilang.splitlines():
        line = line.split('\t')
        lang_code = line[0]

        wiki_lang_code.add(lang_code)

    emb_base_url = 'https://s3-us-west-1.amazonaws.com/fasttext-vectors/word-vectors-v2/'

    fasttext_emb_dir = '/nas/data/m1/zhangb8/data/fasttext_emb'
    for lang_code in wiki_lang_code:
        emb_url = os.path.join(emb_base_url, 'cc.%s.300.vec.gz' % lang_code)

        request = requests.head(emb_url)
        if request.status_code != 200:
            continue

        logging.info('downloading %s' % lang_code)

        file_name = os.path.join(fasttext_emb_dir, 'cc.%s.300.vec.gz' % lang_code)
        with open(file_name, "wb") as file:
            # get request
            response = requests.get(emb_url)
            # write to file
            file.write(response.content)


# def validate_model(model_dp):
#     num_of_file = len(os.listdir(model_dp))
#     if num_of_file != 12:
#         error_message = 'ERROR: %s\nnumber of files in the model not equal to 12' % model_dp
#         return error_message, False
#     else:
#         return '', True
#
#
# def copy_model(language):
#     """
#     change model name to 'model' for testing
#     :param language:
#     :return:
#     """
#     model_dp = os.path.join(elisa_ie_root, 'data/name_taggers/dnn/models/%s' % language)
#
#     src_model_name = 'tag_scheme=iob,lower=False,zeros=False,char_dim=50,char_lstm_dim=25,char_bidirect=True,' \
#                      'word_dim=100,word_lstm_dim=100,word_bidirect=True,pre_emb=,all_emb=False,cap_dim=0,crf=True,' \
#                      'dropout=0.5,lr_method=sgd-lr_.01'
#     trg_model_name = 'model'
#
#     src_model_dp = os.path.join(model_dp, src_model_name)
#     trg_model_dp = os.path.join(model_dp, trg_model_name)
#
#     if not os.path.exists(src_model_dp):
#         return
#
#     error_msg, is_valid = validate_model(src_model_dp)
#     if not is_valid:
#         print error_msg
#         return
#
#     if os.path.exists(trg_model_dp):
#         shutil.rmtree(trg_model_dp)
#
#     shutil.copytree(src_model_dp, trg_model_dp)
#
#
# def retrieve_training_log(lang, out_dp):
#     train_log_fp = os.path.join(elisa_ie_root,
#                                 'data/name_taggers/dnn/models/%s/model/training_log.txt' % lang)
#     out_train_log_fp = os.path.join(out_dp, '%s_training_log.txt' % lang)
#
#     shutil.copy(train_log_fp, out_train_log_fp)
#
#
# def retrieve_data_stat(lang, out_dp):
#     data_stat_fp = os.path.join(elisa_ie_root,
#                                 'data/naacl15/il_annotation_300/%s/bio/bio_log.txt' % lang)
#     out_data_stat_fp = os.path.join(out_dp, '%s_bio_log.txt' % lang)
#
#     shutil.copy(data_stat_fp, out_data_stat_fp)
#
#
# def evaluate_model(lang, score_out_dir):
#     bio_test_path = os.path.join(elisa_ie_root, 'data/naacl15/il_annotation_300/%s/bio/test.bio' % lang)
#
#     # bio to tokenized plain text (required by LSTMs input)
#     lines = io.open(bio_test_path, 'r', -1, 'utf-8').read().split('\n\n')
#     res = []
#     for line in lines:
#         res.append(' '.join([item.split(' ')[0] for item in line.splitlines()]))
#
#     tmp_dir = tempfile.mkdtemp()
#     tokenized_test_path = os.path.join(tmp_dir, 'test.tok')
#     f = io.open(tokenized_test_path, 'w', -1, 'utf-8')
#     if res:
#         f.write('\n'.join(res))
#     else:
#         f.write('\n')
#     f.close()
#
#     # LSTMs name tagger path
#     tagger_path = os.path.join(elisa_ie_root, 'src/name_taggers/dnn/tagger.py')
#
#     model_dir = os.path.join(elisa_ie_root, 'data/name_taggers/dnn/models/%s/model' % lang)
#
#     if not os.path.exists(model_dir):
#         print '%s model not exists. exit' % lang
#         return
#
#     # output path
#     out_path = os.path.join(tmp_dir, 'test.out')
#
#     # LSTMs tagger command
#     cmd = ['python', tagger_path, '--model', model_dir, '--input', tokenized_test_path, '--output', out_path,
#            '--language', lang]
#     print ' '.join(cmd)
#     subprocess.call(cmd)
#
#     # parse gold
#     gold = dict()
#     for i, line in enumerate(io.open(bio_test_path, 'r', -1, 'utf-8').read().split('\n\n')):
#         gold[i] = dict()
#         if not line.strip():
#             continue
#         for j, token in enumerate(line.split('\n')):
#             token_text, token_tag = token.split()
#             gold[i][j] = token_tag
#
#     # convert lstm tagger output to bio
#     res = []
#     for i, line in enumerate(io.open(out_path, 'r', -1, 'utf-8').read().splitlines()):
#         if not line.strip():
#             continue
#         sent = []
#         tokens = line.split(' ')
#         for j, token in enumerate(tokens):
#             token_text, token_tag = token.split('__')
#             sent.append(' '.join([token_text, gold[i][j], token_tag]))
#         res.append('\n'.join(sent))
#
#     sys_out_path = os.path.join(tmp_dir, 'score.txt')
#     f_out = io.open(sys_out_path, 'w', -1, 'utf-8')
#     f_out.write('\n\n'.join(res))
#     f_out.close()
#
#     # evaluate
#     score_out_path = os.path.join(score_out_dir, '%s.txt' % lang)
#     eval_script = os.path.join(elisa_ie_root, 'src/name_taggers/dnn/evaluation/conlleval')
#     os.system("%s < %s > %s" % (eval_script, sys_out_path, score_out_path))
#
#
# def fill_wikiann_stat_score(languages, score_out_fp):
#     #
#     # generate score output file
#     #
#     score_dir = './scores'
#     res = []
#     for lang in languages:
#         score_fp = os.path.join(score_dir, '%s.txt' % lang)
#         if not os.path.exists(score_fp):
#             print 'score file for %s not exists' % score_fp
#             res.append(lang)
#             continue
#         line = open(score_fp).read().splitlines()[1]
#         s = re.findall("\d+\.\d+", line)
#         precision = s[1]
#         recall = s[2]
#         f1 = s[3]
#
#         res.append('\t'.join([lang, precision, recall, f1]))
#
#     f = open(score_out_fp, 'w')
#     f.write('\n'.join(res))
#     f.close()
#
#
# def fill_wikiann_stat_data(languages, data_stat_out_fp):
#     #
#     # generate data stat output file
#     #
#     res = []
#     data_dir = os.path.join(elisa_ie_root, 'data/naacl15/il_annotation_300')
#     for lang in languages:
#         data_stat_fp = os.path.join(data_dir, lang, 'bio/bio_log.json')
#         if not os.path.exists(data_stat_fp):
#             data_stat_fp = os.path.join(data_dir, lang, 'bio/bio_log.txt')
#         if not os.path.exists(data_stat_fp):
#             print 'data log file for %s not exists' % data_stat_fp
#             res.append(lang)
#             continue
#         data_stat = json.load(open(data_stat_fp))
#         train_sent_num = data_stat['train_sentences']
#         test_sent_num = data_stat['test_sentences']
#         res.append('\t'.join([lang, str(train_sent_num), str(test_sent_num)]))
#
#     f = open(data_stat_out_fp, 'w')
#     f.write('\n'.join(res))
#     f.close()


if __name__ == "__main__":
    # download_fasttext_word_emb()

    generate_gold_ann_path()

    generate_pretrained_embedding_path()

    # il_languages = open(os.path.join(elisa_ie_root,
    #                                  'src/name_taggers/name_tagger_300/languages.txt')).read().splitlines()
    # # il_languages = ['bg', 'bn']
    #
    # errors = []
    # for lang in il_languages:
    #     #
    #     # copy trained model to "model" dir
    #     #
    #     copy_model(lang)
    #
    #     #
    #     # retrieve training log from model directory
    #     #
    #     # retrieve_training_log(lang, './training_log/')
    #
    #     #
    #     # retrieve wikiann, training and test data statistics
    #     #
    #     # retrieve_data_stat(lang, './data_stats')
    #
    #     #
    #     # evaluate model on test.bio for all languages. this function generate a 'scores' directory
    #     #
    #     # try:
    #     #     evaluate_model(lang, './scores')
    #     # except:
    #     #     print '%s evaluation error.' % lang
    #     #     errors.append(lang)
    #     #     continue
    #     # evaluate_model(lang, './scores')
    #
    #     pass
    #
    # #
    # # fill out wikiann_stats form with model performance scores and data stats
    # #
    # # wikiann_stats_lang = open('wikiann_stats_lang.txt').read().strip().splitlines()
    # #
    # # score_out_fp = 'wikiann_stats_scores.txt'
    # # fill_wikiann_stat_score(wikiann_stats_lang, score_out_fp)
    # #
    # # data_stat_out_fp = 'wikiann_stats_data.txt'
    # # fill_wikiann_stat_data(wikiann_stats_lang, data_stat_out_fp)
    #
    # print 'error languages: %s' % ', '.join(errors)
