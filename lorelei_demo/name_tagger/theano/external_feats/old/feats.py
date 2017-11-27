#encoding=utf-8
import itertools
import sys
import io
import os
import operator
import codecs

from multiprocessing import Pool
from functools import partial
from fb_intern import fb_intern_root

def generate_external_feats(documents):
    sys.setrecursionlimit(10000)
    mention_dict = load_dict()
    gaz_distribution = generate_type_distribution(gaz)
    # gaz_distribution = dict()
    res = []
    for doc in documents:
        print doc.id
        sentences = doc.sentences

        # multiprocessing
        # core_num = 4
        # n = len(sentences) / core_num + 1
        # args = [sentences[i:i+n] for i in xrange(0, len(sentences), n)]
        #
        # p = Pool(core_num)
        # func = partial(generate_sent_gaz_feats, gaz, gaz_distribution)
        # feats = p.map(func, args)
        # feats = list(itertools.chain(*feats))

        # single core
        feats = generate_sent_gaz_feats(gaz, gaz_distribution, sentences)

        res += feats

    return res


def load_dict():
    dict_file = os.path.join(fb_intern_root, 'data/gaz/mentions_file')

    mention_set = []
    for line in codecs.open(dict_file, 'r', 'utf-8'):
        mention, = line.split('\t')
        mention_set.append(mention)

    return set(mention_set)


def measure_gaz_quality(ltf_documents, il, output_dp=None):
    sys.setrecursionlimit(10000)
    multicore = True

    feats_analysis = dict()
    gaz = load_gaz(il, combined=False)
    for doc in ltf_documents:
        print doc.id
        sentences = doc.sentences

        if multicore:
            # multiprocessing
            core_num = 4
            n = len(sentences) / core_num + 1
            args = [sentences[i:i+n] for i in xrange(0, len(sentences), n)]

            p = Pool(core_num)
            func = partial(measure_gaz_coverage, gaz, il)
            f_analysis = p.map(func, args)
        else:
            # single core
            f_analysis = [measure_gaz_coverage(gaz, il, sentences)]

        # merge results
        for fa in f_analysis:
            for gaz_type, value in fa.items():
                if gaz_type not in feats_analysis:
                    feats_analysis[gaz_type] = value
                else:
                    feats_analysis[gaz_type]['correct'] += value['correct']
                    feats_analysis[gaz_type]['incorrect'] += value['incorrect']

    # output feature analysis
    for gaz_type, analysis_by_gaz_type in sorted(feats_analysis.items()):
        for tag, analysis_by_tag in analysis_by_gaz_type.items():
            if tag == 'incorrect':
                incorrect_match = len(analysis_by_tag)
            elif tag == 'correct':
                correct_match = len(analysis_by_tag)

            if output_dp:
                f = io.open(os.path.join(output_dp, '%s.%s.txt' % (gaz_type, tag)), 'w', -1, 'utf-8')
                if analysis_by_tag:
                    f.write('\n'.join(analysis_by_tag))
                f.close()

        if correct_match+incorrect_match == 0:
            correct_ratio = 0
            incorrect_ratio = 0
        else:
            correct_ratio = float(correct_match)/(correct_match+incorrect_match)*100
            incorrect_ratio = float(incorrect_match)/(correct_match+incorrect_match)*100
        print '{:50s} => {:15s}: {:4d} ({:6.2f}%) {:15s}: {:4d} ({:6.2f}%)'. \
            format(gaz_type,
                   'correct_match', correct_match, correct_ratio,
                   'incorrect_match', incorrect_match, incorrect_ratio)


def generate_sent_gaz_feats(gaz, gaz_type_distribution, sentences):
    res = []

    all_gaz_set = set()
    for gaz_type, names in gaz.items():
        all_gaz_set = all_gaz_set.union(names)

    for sent in sentences:
        sent_res = []
        for token in sent.tokens:
            # token_count += 1
            token_res = []

            # check gazetteer coverage
            # for gaz_type, gaz_set in gaz.items():
            #     token_res.append(is_il_type(token, gaz, gaz_type))
            #
            # for gaz_type, gaz_set in gaz.items():
            #     token_res.append(is_context_type(token, gaz, gaz_type))

            # generate numeric gaz features
            token_res = generate_type_distribution_feat(token, all_gaz_set, gaz_type_distribution)

            sent_res.append(token_res)

        res.append(sent_res)

    return res


def measure_gaz_coverage(gaz, il, sentences):
    feats_analysis = dict()

    for sent in sentences:
        for token in sent.tokens:
            # check gazetteer coverage
            for gaz_type, gaz_set in gaz.items():

                # check is_in_gaz
                if gaz_type not in feats_analysis:
                    feats_analysis[gaz_type] = {'correct': [],
                                                'incorrect': []}
                token_gaz_tag = is_in_gaz(token, gaz, gaz_type)

                if token_gaz_tag != 'O':
                    message = '%s %s (%s) => %s-%s' % (token_gaz_tag, token.text, gaz_type, token.tag, token.type)
                    if token.tag == token_gaz_tag:
                        if token.type and token.type in gaz_type:
                            feats_analysis[gaz_type]['correct'].append(message)
                        else:
                            feats_analysis[gaz_type]['incorrect'].append(message)
                    else:
                        feats_analysis[gaz_type]['incorrect'].append(message)

                # check is_context_in_gaz
                if 'context_' + gaz_type not in feats_analysis:
                    feats_analysis['context_' + gaz_type] = {'correct': [],
                                                             'incorrect': []}
                token_context_gaz_tag, context = is_context_in_gaz(token, gaz, gaz_type, il)

                if token_context_gaz_tag != 'O':
                    context_message = '%s %s (%s, %s) => %s-%s' % (token_context_gaz_tag, token.text, context, gaz_type,
                                                                    token.tag, token.type)
                    if token.tag == token_context_gaz_tag:
                        if token.type and token.type in gaz_type:
                            feats_analysis['context_' + gaz_type]['correct'].append(context_message)
                        else:
                            feats_analysis['context_' + gaz_type]['incorrect'].append(context_message)
                    else:
                        feats_analysis['context_' + gaz_type]['incorrect'].append(context_message)

    return feats_analysis


# def is_il_type(token, gaz, gaz_type):
#     global feats_analysis
#     if gaz_type not in feats_analysis:
#         feats_analysis[gaz_type] = {'correct': [],
#                                     'incorrect': []}
#
#     if len(token.text) < 2:  # too short token can't be a name
#         return False
#     if token.text in gaz[gaz_type]:
#
#         message = 'B %s => %s (%s-%s)' % (token.text, gaz_type, token.tag, token.type)
#         if token.tag in ['O', '']:
#             feats_analysis[gaz_type]['incorrect'].append(message)
#         else:
#             if token.type.lower() in gaz_type:
#                 feats_analysis[gaz_type]['correct'].append(message)
#             else:
#                 feats_analysis[gaz_type]['incorrect'].append(message)
#
#         return True
#
#     return False


def is_in_gaz(token, gaz, gaz_type):
    if len(token.text) < 2:  # too short token can't be a name
        return 'O'

    if token.text in gaz[gaz_type]:
        return 'B'

    return 'O'


def generate_type_distribution(gaz):
    tokens = list()
    token_set = set()
    tokenized_gaz = dict()
    for gaz_type, names in gaz.items():
        for item in names:
            tokenized_item = item.split()
            token_set = token_set.union(set(tokenized_item))
            tokens += tokenized_item
            try:
                tokenized_gaz[gaz_type].append(tokenized_item)
            except KeyError:
                tokenized_gaz[gaz_type] = [tokenized_item]

    gaz_type_distribution = dict()
    for token in token_set:
        gaz_type_distribution[token] = dict()
        token_frequency = tokens.count(token)
        for gaz_type, names in tokenized_gaz.items():
            B_count = 0
            I_count = 0
            for n in names:
                if n[0] == token:
                    B_count += 1
                elif token in n[1:]:
                    I_count += 1
            gaz_type_distribution[token]['B-'+gaz_type] = B_count / float(token_frequency)
            gaz_type_distribution[token]['I-'+gaz_type] = I_count / float(token_frequency)
        # assert sum(gaz_type_distribution[token].values()) == 1
        gaz_type_distribution[token] = sorted(gaz_type_distribution[token].items(), key=operator.itemgetter(0))

    return gaz_type_distribution


def generate_type_distribution_feat(token, all_gaz_set, gaz_type_distribution):
    context_window = 3
    token_index = token.index

    if token_index-context_window < 0:
        context_tokens = token.sent.tokens[0:token_index+context_window+1]
    else:
        context_tokens = token.sent.tokens[token_index-context_window:token_index+context_window+1]

    valid_context_tokens = []
    for i in xrange(1, len(context_tokens)+1):
        combinations = list(itertools.combinations(context_tokens, i))
        for c in combinations:
            if token in c:
                valid_context_tokens.append(c)

    contexts = []
    for c in valid_context_tokens:
        contexts.append(' '.join([t.text for t in c]))

    # sort context by length
    sorted_contexts = sorted(contexts, key=len, reverse=True)

    for c in sorted_contexts:
        suffix_threshold = 2
        c_to_compare = []
        for i in xrange(suffix_threshold):
            if len(c)-i > 0:
                c_to_compare.append(c[:len(c)-i])

        for item in c_to_compare:
            if item in all_gaz_set and ' ' not in c.replace(item, ''):
                if token.text in item.split():
                    return [item[1] for item in gaz_type_distribution[token.text]]
                else:
                    return [item[1] for item in gaz_type_distribution[item.split()[-1]]]

    return [0] * len(gaz_type_distribution.values()[0])


# ======= feature generation ======= #
# manually cleaned gaz
def is_il_per(token, gaz):
    return is_il_type(token, gaz, 'il_per')


def is_il_org(token, gaz):
    return is_il_type(token, gaz, 'il_org')


def is_il_gpe(token, gaz):
    return is_il_type(token, gaz, 'il_gpe')


def is_il_loc(token, gaz):
    return is_il_type(token, gaz, 'il_loc')


# wiki uig gaz
def is_il_per_wiki(token, gaz):
    return is_il_type(token, gaz, 'il_per_wiki')


def is_il_org_wiki(token, gaz):
    return is_il_type(token, gaz, 'il_org_wiki')


def is_il_gpe_wiki(token, gaz):
    return is_il_type(token, gaz, 'il_gpe_wiki')


def is_il_loc_wiki(token, gaz):
    return is_il_type(token, gaz, 'il_loc_wiki')


# low quality gaz
def is_il_per_low_quality(token, gaz):
    return is_il_type(token, gaz, 'il_per_low_quality')


def is_il_gpe_low_quality(token, gaz):
    return is_il_type(token, gaz, 'il_gpe_low_quality')


# manually cleaned gaz
def is_context_per(token, gaz):
    return is_context_type(token, gaz, 'il_per')


def is_context_org(token, gaz):
    return is_context_type(token, gaz, 'il_org')


def is_context_gpe(token, gaz):
    return is_context_type(token, gaz, 'il_gpe')


def is_context_loc(token, gaz):
    return is_context_type(token, gaz, 'il_loc')


# wiki uig gaz
def is_context_per_wiki(token, gaz):
    return is_context_type(token, gaz, 'il_per_wiki')


def is_context_org_wiki(token, gaz):
    return is_context_type(token, gaz, 'il_org_wiki')


def is_context_gpe_wiki(token, gaz):
    return is_context_type(token, gaz, 'il_gpe_wiki')


def is_context_loc_wiki(token, gaz):
    return is_context_type(token, gaz, 'il_loc_wiki')


# low quality gaz
def is_context_per_low_quality(token, gaz):
    return is_context_type(token, gaz, 'il_per_low_quality')


def is_context_gpe_low_quality(token, gaz):
    return is_context_type(token, gaz, 'il_gpe_low_quality')


# def is_context_type(token, gaz, gaz_type):
#     global feats_analysis
#     if 'context_'+gaz_type not in feats_analysis:
#         feats_analysis['context_'+gaz_type] = {'incorrect': [],
#                                                'correct': []}
#
#     context_window = 3
#     token_index = token.index
#
#     if token_index-context_window < 0:
#         context_tokens = token.sent.tokens[0:token_index+context_window+1]
#     else:
#         context_tokens = token.sent.tokens[token_index-context_window:token_index+context_window+1]
#
#     valid_context_tokens = []
#     for i in xrange(1, len(context_tokens)+1):
#         combinations = list(itertools.combinations(context_tokens, i))
#         for c in combinations:
#             if token in c:
#                 valid_context_tokens.append(c)
#
#     contexts = []
#     for c in valid_context_tokens:
#         # contexts.append(' '.join([t.text for t in c]))
#         contexts.append(''.join([t.text for t in c]))  # for Chinese only
#
#     # sort context by length
#     sorted_contexts = sorted(contexts, key=len, reverse=True)
#
#     for c in sorted_contexts:
#         # stemming word by removing suffix
#         suffix_threshold = 2
#         c_to_compare = []
#         for i in xrange(suffix_threshold):
#             if len(c)-i > 0:
#                 c_to_compare.append(c[:len(c)-i])
#
#         c_to_compare = [c]  # for Chinese only
#
#         for item in c_to_compare:
#             if item in gaz[gaz_type] and ' ' not in c.replace(item, ''):
#                 # if len(c) != len(item):
#                 #     print '%s ==> %s' % (c, item)
#                 if item.split()[0] == token.text or item.strip().startswith(token.text):
#
#                     message = 'B %s (%s) => %s (%s-%s)' % (item, token.text, gaz_type, token.tag, token.type)
#                     if token.tag in ['O', '']:
#                         feats_analysis['context_'+gaz_type]['incorrect'].append(message)
#                     else:
#                         if token.type.lower() in gaz_type:
#                             feats_analysis['context_'+gaz_type]['correct'].append(message)
#                         else:
#                             feats_analysis['context_'+gaz_type]['incorrect'].append(message)
#
#                     return 'B'
#
#                 else:
#                     message = 'I %s (%s) => %s (%s-%s)' % (item, token.text, gaz_type, token.tag, token.type)
#                     if token.tag in ['O', '']:
#                         feats_analysis['context_'+gaz_type]['incorrect'].append(message)
#                     else:
#                         if token.type.lower() in gaz_type:
#                             feats_analysis['context_'+gaz_type]['correct'].append(message)
#                         else:
#                             feats_analysis['context_'+gaz_type]['incorrect'].append(message)
#
#                     return 'I'
#
#                     # for item in gaz[gaz_type]:
#                     #     if c.startswith(item) and len(c)-len(item) < 5 and ' ' not in c.replace(item, ''):
#                     #         if len(c) != len(item):
#                     #             print '%s ==> %s' % (c, item)
#                     #             suffix = c.replace(item, '')
#                     #             if suffix in gaz['noun_suffix']:
#                     #                 global in_suffix
#                     #                 in_suffix += 1
#                     #             else:
#                     #                 global out_suffix
#                     #                 out_suffix += 1
#                     #         return True
#
#     return 'O'


def is_context_in_gaz(token, gaz, gaz_type, il, stemming=False):
    context_window = 2
    token_index = token.index

    if token_index-context_window < 0:
        context_tokens = token.sent.tokens[0:token_index+context_window+1]
    else:
        context_tokens = token.sent.tokens[token_index-context_window:token_index+context_window+1]

    valid_context_tokens = []
    for i in xrange(1, len(context_tokens)+1):
        combinations = list(itertools.combinations(context_tokens, i))
        for c in combinations:
            if token in c:
                valid_context_tokens.append(c)

    contexts = []
    for c in valid_context_tokens:
        if il in ['cmn']:
            contexts.append(''.join([t.text for t in c]))  # for Chinese only
        else:
            contexts.append(' '.join([t.text for t in c]))

    # sort context by length
    sorted_contexts = sorted(contexts, key=len, reverse=True)

    for c in sorted_contexts:
        if stemming:
            # stemming word by removing suffix
            suffix_threshold = 2
            c_to_compare = []
            for i in xrange(suffix_threshold):
                if len(c)-i > 0:
                    c_to_compare.append(c[:len(c)-i])
        else:
            c_to_compare = [c]  # for Chinese only

        for item in c_to_compare:
            if item in gaz[gaz_type] and ' ' not in c.replace(item, ''):
                if item.strip().startswith(token.text):
                    return 'B', item
                else:
                    return 'I', item

    return 'O', ''


def is_il_non_name(token, gaz):
    if len(token.text) < 2:  # too short token can't be a name
        return False
    if token.text in gaz['il_non_name']:
        return True

    return False


def is_il_per_designator(token, gaz):
    if len(token.text) < 2:  # too short token can't be a name
        return False
    if token.text in gaz['il_per_designator']:
        return True

    return False


def is_il_org_designator(token, gaz):
    if len(token.text) < 2:  # too short token can't be a name
        return False
    if token.text in gaz['il_org_designator']:
        return True

    return False


def is_il_gpe_designator(token, gaz):
    if len(token.text) < 2:  # too short token can't be a name
        return False
    if token.text in gaz['il_gpe_designator']:
        return True

    return False


def is_il_loc_designator(token, gaz):
    if len(token.text) < 2:  # too short token can't be a name
        return False
    if token.text in gaz['il_loc_designator']:
        return True

    return False


def has_verb_suffix(token, gaz):
    if len(token.text) < 2:
        return 'no_suffix'
    for suffix in gaz['verb_suffix']:
        if token.text.endswith(suffix):
            return suffix

    return 'no_suffix'


def has_noun_suffix(token, gaz):
    if len(token.text) < 2:
        return 'no_suffix'
    for suffix in gaz['noun_suffix']:
        if token.text.endswith(suffix):
            return suffix

    return 'no_suffix'


def has_possessive_suffix(token, gaz):
    if len(token.text) < 2:
        return 'no_suffix'
    for suffix in gaz['possessive_suffix']:
        if token.text.endswith(suffix):
            return suffix

    return 'no_suffix'


if __name__ == "__main__":
    il = 'cmn'
    bio_fp = '/Users/boliangzhang/Documents/Phd/LORELEI/data/naacl15/il_annotation/cmn/bio/train.bio'
    bio_fp = '/Users/boliangzhang/Documents/Phd/LORELEI/data/naacl15/il_annotation/cmn/bio/test.bio'
    ltf_docs = [parse_bio(bio_fp)]
    measure_gaz_quality(ltf_docs, 'cmn')