import io
import os
import operator
import time
import random
import multiprocessing
import json
from collections import OrderedDict

from src.name_taggers.name_tagger_300 import elisa_ie_root


def select_bio(bio_path, train_ratio, name_frqcy_thresold, max_sent_per_name, bio_size, min_sent_len, max_sent_len):
    f_bio = io.open(bio_path, 'r', -1, 'utf-8')
    f_bio = f_bio.read()

    bio_sents = f_bio.split('\n\n')
    random.shuffle(bio_sents)
    overall_stats, overall_name_frqcy = analyze_bio(bio_sents)

    # sanity check, remove invalid sentence
    valid_sents = []
    for sent in bio_sents:
        valid = True
        for token in sent.split('\n'):
            token = token.strip().split()
            if len(token) != 2:
                valid = False
                break
        if valid:
            valid_sents.append(sent)
    bio_sents = valid_sents

    if len(bio_sents) >= bio_size:
        res = []
        sent_per_name_added = dict()
        for line in bio_sents:
            # ignore too short or too long sentence
            line_len = len(line.split('\n'))
            if line_len < min_sent_len or line_len > max_sent_len:
                continue

            try:
                mentions = get_mention(line)
                for mention_text, mention_type in mentions:
                    if overall_name_frqcy[mention_text] >= name_frqcy_thresold:
                        # avoiding adding too many sentences
                        if mention_text not in sent_per_name_added or \
                                        sent_per_name_added[mention_text] <= max_sent_per_name:
                            res.append(line)
                            try:
                                sent_per_name_added[mention_text] += 1
                            except KeyError:
                                sent_per_name_added[mention_text] = 1

                            # break to process next sentence
                            break
            except:
                continue
    else:
        res = bio_sents

    res_len = len(res)
    train_res = res[:int(train_ratio*res_len)]
    test_res = res[int(train_ratio*res_len):]

    train_res_stats, train_res_name_frqcy = analyze_bio(train_res)
    test_res_stats, test_res_name_frqcy = analyze_bio(test_res)

    bio_log = OrderedDict()

    bio_log['title'] = '#####################\nbio log created on: %s_%s\n\n' % (time.strftime("%m_%d_%Y"), time.strftime("%H_%M_%S"))

    overall_sents = len(bio_sents)
    bio_log["overall_sentences"] = overall_sents
    for _type, names in sorted(overall_stats.items()):
        name_num = len(names)
        bio_log["overall_%s_names" % _type] = name_num
    for _type, names in sorted(overall_stats.items()):
        unique_name_num = len(set(names))
        bio_log["overall_unique_%s_names" % _type] = unique_name_num

    bio_log["train_sentences"] = len(train_res)
    for _type, names in sorted(train_res_stats.items()):
        name_num = len(names)
        bio_log["train_%s_names" % _type] = name_num
    for _type, names in sorted(train_res_stats.items()):
        unique_name_num = len(set(names))
        bio_log["train_unique_%s_names" % _type] = unique_name_num

    bio_log["test_sentences"] = len(test_res)
    for _type, names in sorted(test_res_stats.items()):
        name_num = len(names)
        bio_log["test_%s_names" % _type] = name_num
    for _type, names in sorted(test_res_stats.items()):
        unique_name_num = len(set(names))
        bio_log["test_unique_%s_names" % _type] = unique_name_num

    # train_sents = len(train_res)
    # bio_log += '\n==>train bio sentences #: %d\n' % train_sents
    # for _type, names in sorted(train_res_stats.items()):
    #     name_num = len(names)
    #     bio_log += '# of %s names: %d\n' % (_type, name_num)
    # for _type, names in sorted(train_res_stats.items()):
    #     unique_name_num = len(set(names))
    #     bio_log += '# of unique %s names: %d\n' % (_type, unique_name_num)
    #
    # test_sents = len(test_res)
    # bio_log += '\n==>test bio sentences #: %d\n' % test_sents
    # for _type, names in sorted(test_res_stats.items()):
    #     name_num = len(names)
    #     bio_log += '# of %s names: %d\n' % (_type, name_num)
    # for _type, names in sorted(test_res_stats.items()):
    #     unique_name_num = len(set(names))
    #     bio_log += '# of unique %s names: %d\n' % (_type, unique_name_num)

    return train_res, test_res, bio_log


def analyze_bio(bio_sent_list):
    stats = dict()
    name_frqcy = dict()
    for line in bio_sent_list:
        try:
            mentions = get_mention(line)
            for mention_text, mention_type in mentions:
                try:
                    name_frqcy[mention_text] += 1
                except KeyError:
                    name_frqcy[mention_text] = 1
                try:
                    stats[mention_type].append(mention_text)
                except KeyError:
                    stats[mention_type] = [mention_text]
        except:
            continue

    return stats, name_frqcy


def get_mention(bio_sent_str):
    # get mentions from bio line
    mentions = []
    current_mention_tok = []
    current_mention_type = ''

    bio_sents = bio_sent_str.split('\n')
    for i, item in enumerate(bio_sents):
        try:
            tok, tag = item.split(' ')[:2]
        except ValueError:
            continue
        if tag.startswith('B'):
            if current_mention_tok:
                mention_text = ' '.join(current_mention_tok)
                mentions.append((mention_text, current_mention_type))
            current_mention_tok = [tok]
            current_mention_type = tag.split('-')[1]
        elif tag.startswith('I'):
            current_mention_tok.append(tok)
        elif tag.startswith('O'):
            if current_mention_tok:
                mention_text = ' '.join(current_mention_tok)
                mentions.append((mention_text, current_mention_type))
                current_mention_tok = []

        if i == len(bio_sents) - 1 and current_mention_tok:
            mention_text = ' '.join(current_mention_tok)
            mentions.append((mention_text, current_mention_type))

    return mentions


# todo select longer sentences for training, change min and max sent length
def iterate_selection(lang, bio_path, train_ratio, name_frqcy_thresold, max_sent_per_name, bio_size,
                      min_sent_len=5, max_sent_len=100, step_size_base=10):
    print '(%s) iterating bio selection function...' % lang

    train_res, test_res, bio_log = select_bio(bio_path, train_ratio, name_frqcy_thresold, max_sent_per_name,
                                              bio_size, min_sent_len, max_sent_len)
    left_bio_size = len(train_res) + len(test_res)
    right_bio_size = left_bio_size

    if 20000 < left_bio_size < bio_size:
        return train_res, test_res, bio_log

    index = 0
    maximum_iterations = 30
    while True:
        step_size = min((left_bio_size/bio_size+1)*step_size_base,
                        (right_bio_size/bio_size+1)*step_size_base)
        print '(%s) iteration %d, left bio size: %d, right bio size: %d ' % (lang, index, left_bio_size, right_bio_size)
        if right_bio_size < bio_size:
            name_frqcy_thresold -= step_size
            right_train_res, right_test_res, right_bio_log = select_bio(bio_path, train_ratio,
                                                                        name_frqcy_thresold,
                                                                        max_sent_per_name, bio_size,
                                                                        min_sent_len, max_sent_len)
            right_bio_size = len(right_train_res) + len(right_test_res)
            if right_bio_size > bio_size or index == maximum_iterations:
                right_bio_log['name_frequency_threshold'] = name_frqcy_thresold
                # right_bio_log += '\n\nname frequency threshold: %d' % name_frqcy_thresold
                return right_train_res, right_test_res, right_bio_log
        elif left_bio_size > bio_size:
            name_frqcy_thresold += step_size
            left_train_res, left_test_res, left_bio_log = select_bio(bio_path, train_ratio,
                                                                     name_frqcy_thresold,
                                                                     max_sent_per_name, bio_size,
                                                                     min_sent_len, max_sent_len)
            left_bio_size = len(left_train_res) + len(left_test_res)
            if left_bio_size < bio_size or index == maximum_iterations:
                left_bio_log['name_frequency_threshold'] = name_frqcy_thresold
                # left_bio_log += '\n\nname frequency threshold: %d' % name_frqcy_thresold
                return left_train_res, left_test_res, left_bio_log
        index += 1


def single_core(lang):
    train_ratio = 0.8
    name_frqcy_thresold = 20
    max_sent_per_name = 20
    bio_size = 30000

    print '== (%s) starting generating training and test bio from wiki-ann ==' % lang
    # bio_path = os.path.join(elisa_ie_root, 'data/naacl15/wikiann/slavic/wikiann-%s.bio' % lang)
    # bio_path = os.path.join(elisa_ie_root, 'data/naacl15/wikiann/01162017/wikiann-%s.bio' % lang)
    # bio_path = os.path.join(elisa_ie_root, 'data/naacl15/wikiann/01222017/wikiann-%s.bio' % lang)
    bio_path = os.path.join(elisa_ie_root, 'data/naacl15/wikiann/01252017/wikiann-%s.bio' % lang)
    # bio_path = os.path.join(elisa_ie_root,
    #                         'data/naacl15/wikiann/minLen5.allO.MISC.NIL.minConf50.minDistO0/wikiann-%s.bio' % lang)

    # automatically adjust name_frqcy_thresold to make train and test size as close to the bio_size
    train_res, test_res, bio_log = iterate_selection(lang, bio_path, train_ratio,
                                                     name_frqcy_thresold, max_sent_per_name, bio_size)
    bio_log = json.dumps(bio_log,
                         indent=4, separators=(',', ': '))

    output_dir = os.path.join(elisa_ie_root, 'data/naacl15/il_annotation_300/%s/bio' % lang)
    # output_dir = os.path.join(elisa_ie_root, 'data/naacl15/il_annotation_300_linking/%s/bio' % lang)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)  # recursively make directories

    f_out = io.open(os.path.join(output_dir, 'train.bio'), 'w', -1, 'utf-8')
    if train_res:
        f_out.write('\n\n'.join(train_res))
    f_out.close()

    f_out = io.open(os.path.join(output_dir, 'test.bio'), 'w', -1, 'utf-8')
    if test_res:
        f_out.write('\n\n'.join(test_res))
    f_out.close()

    f_out = io.open(os.path.join(output_dir, 'dev.bio'), 'w', -1, 'utf-8')
    if test_res:
        f_out.write('\n\n'.join(test_res))
    f_out.close()

    f_out = open(os.path.join(output_dir, 'bio_log.json'), 'w')
    f_out.write(bio_log)
    f_out.close()

    print '(%s) training data generation is done.' % lang


if __name__ == '__main__':
    # languages = ['be-x-old', 'be', 'bg', 'bs', 'cs', 'csb', 'cu', 'dsb', 'hr', 'hsb', 'mk', 'pl', 'ru', 'rue', 'sh',
    #              'sk', 'sl', 'sr', 'szl', 'uk']

    # languages = ['vo']

    # languages = ['af', 'an', 'az', 'ba', 'bar', 'be', 'be-x-old', 'bg', 'bn', 'br', 'bs', 'bug', 'ca', 'ceb', 'ce',
    #              'cs', 'cv', 'cy', 'da', 'de', 'el', 'eo', 'es', 'et', 'eu', 'fi', 'fr', 'gl', 'he', 'hi', 'hr', 'hu',
    #              'hy', 'id', 'it', 'ka', 'kk', 'ko', 'la', 'lb', 'lmo', 'lt', 'lv', 'mg', 'mk', 'ml', 'mr', 'ms',
    #              'new', 'nl', 'nn', 'no', 'oc', 'pl', 'pt', 'ro', 'ru', 'sh', 'sk', 'sl', 'sq', 'sr', 'sv', 'ta',
    #              'tl', 'tr', 'tt', 'uk', 'uz', 'vi', 'vo', 'war']

    languages = open(os.path.join(elisa_ie_root,
                                  'src/name_taggers/name_tagger_300/languages.txt')).read().splitlines()

    # languages = languages[:5]
    # languages = ['ab']

    #
    # multi-core processing
    #
    max_cores = 20

    iterations = len(languages) / max_cores + 1

    for i in xrange(iterations):
        p = multiprocessing.Pool(max_cores)
        p.map(single_core, languages[i*max_cores:(i+1)*max_cores])

    #
    # single core processing for debugging
    #
    # for lang in languages[:1]:
    #     single_core(lang)



