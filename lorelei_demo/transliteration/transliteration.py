import json
from collections import defaultdict, namedtuple

import re
import logging
import unidecode
import distance
import requests

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

# Transliteration parameters
MAX_PAIR_GRAM_NUM = 5
BEAM_SIZE = 100
FINAL_STATE_NUM = 10
BEST_STATE_NUM = 20
MAX_ENTITY_NUM = 10
LINK_NUMBER_THRESHOLD = 3
LINK_SCORE_THRESHOLD = .6
SIMILARITY_THRESHOLD = .7

# Special characters
SEGMENT_DELIMITER = '\u2063'
PAIR_DELIMITER = '\u2064'
START_SYMBOL = '\u2045'
END_SYMBOL = '\u2046'
VOID_TRANSLITERATION = '\u2060'
START_UNIT = '\u2e28'
END_UNIT = '\u2e29'
SPACE_SYMBOL = '◊'
TOKEN_SEPARATORS = ['-', '－', ' ', ',', '•', '·', '_', '·', ':', '(', ')', '.', '．', '・']
TOKEN_SEP_PATTERN = re.compile('[' + '\\'.join(TOKEN_SEPARATORS) + ']')

# Jelinek-Mercer smoothing
JM_LAMBDA_MIN = .5
JM_LAMBDA_MAX = 1.0
JM_LAMBDA_DIFF = JM_LAMBDA_MAX - JM_LAMBDA_MIN
JM_LAMBDA_THRES = 10

SCORE_BIAS = .3


LINKING_URL = 'http://blender02.cs.rpi.edu:2201/linking'

Phrase = namedtuple('Phrase', ['text', 'tokens', 'attributes'])
Token = namedtuple('Token', ['text', 'attributes'])


def load_model(path, ignore_case=False):
    """Load model from file.

    :param path: Path to the model file.
    :param ignore_case: Lower-case source and target word case (default=False).
    :return: candidate map, pair transition probability map and pair frequency map
    """
    total_pair_num = 0
    total_seg_num = 0
    src_unit_set = set()
    tgt_unit_set = set()
    candidates = defaultdict(set)
    pair_gram_count = defaultdict(int)

    with open(path, 'r', encoding='utf-8') as r:
        for line in r:
            if ignore_case:
                line = line.lower()
            src, tgt = line.rstrip().replace(':', '').split('\t')
            src_segs = src.split('|')
            tgt_segs = tgt.split('|')
            if len(src_segs) != len(tgt_segs):
                logger.warning('source length != target length')
                continue
            total_pair_num += 1
            total_seg_num += len(src_segs)

            src_unit_set.update(src_segs)
            tgt_unit_set.update(tgt_segs)
            for src_seg, tgt_seg in zip(src_segs, tgt_segs):
                candidates[src_seg].add(tgt_seg)

            # append start and end symbols
            src_segs = [START_SYMBOL] + src_segs + [END_SYMBOL]
            tgt_segs = [START_SYMBOL] + tgt_segs + [END_SYMBOL]
            seg_num = len(src_segs)

            for gram_len in range(1, MAX_PAIR_GRAM_NUM + 1):
                for begin_idx in range(seg_num - gram_len):
                    gram = SEGMENT_DELIMITER.join(
                        ['{}{}{}'.format(src_seg, PAIR_DELIMITER, tgt_seg)
                         for src_seg, tgt_seg
                         in zip(src_segs[begin_idx:begin_idx + gram_len],
                                tgt_segs[begin_idx:begin_idx + gram_len])])
                    pair_gram_count[gram] += 1
    logger.info('#source unit: {}'.format(len(src_unit_set)))
    logger.info('#target unit: {}'.format(len(tgt_unit_set)))

    # calculate transition probabilities
    pair_model = {}
    factor  = 1.0 / total_seg_num
    for gram, count in pair_gram_count.items():
        if SEGMENT_DELIMITER in gram:
            pre_gram = gram[:gram.rfind(SEGMENT_DELIMITER)]
            prob = count / pair_gram_count[pre_gram]
            pair_model[gram] = prob
        else:
            pair_model[gram] = factor * count
    pair_model[START_SYMBOL + PAIR_DELIMITER + START_SYMBOL] = 1.0
    pair_model[END_SYMBOL + PAIR_DELIMITER + END_SYMBOL] = 1.0
    candidates[START_SYMBOL] = {START_SYMBOL}
    candidates[END_SYMBOL] = {END_SYMBOL}

    return candidates, pair_model, pair_gram_count


def calc_state_score(segs, pair_trans_prob, pair_freq):
    """Calculate the score of a sequence of transliteration unit pairs.

    :param segs: A sequence of transliteration unit pairs.
    :param pair_trans_prob: Transliteration unit pair transition probabilities.
    :param pair_freq: Transliteration unit pair frequency.
    :return: State score.
    """
    score = 1.0
    for i in range(1, len(segs)):
        scores = [0.0] * MAX_PAIR_GRAM_NUM
        freqs = [0] * MAX_PAIR_GRAM_NUM
        actual_gram_num = i + 1 if i < MAX_PAIR_GRAM_NUM else MAX_PAIR_GRAM_NUM
        for j in range(actual_gram_num):
            gram = SEGMENT_DELIMITER.join([
                '{}{}{}'.format(segs[k][0], PAIR_DELIMITER, segs[k][1])
                for k in range(i - j, i + 1)
            ])
            scores[j] = pair_trans_prob.get(gram, 1e-6)
            freqs[j] = pair_freq.get(gram, 0)
        for j in range(1, actual_gram_num):
            jm_lambda = 0 if freqs[j] == 0 \
                else JM_LAMBDA_MAX if freqs[j] >= JM_LAMBDA_THRES \
                else JM_LAMBDA_MIN + (freqs[j] / JM_LAMBDA_THRES) * JM_LAMBDA_DIFF
            scores[j] = jm_lambda * scores[j] + (1.0 - jm_lambda) * scores[j - 1]
        score *= scores[actual_gram_num - 1]
    return score


def jscm(query, candidate_map, pair_trans_prob, pair_freq,
         final_state_num=FINAL_STATE_NUM):
    """Transliterate a query using JSCM.

    :param query: The query string.
    :param candidate_map:
    :param pair_trans_prob:
    :param pair_freq:
    :param final_state_num: Number of final states (default=FINAL_STATE_NUM)
    :return: A list of transliteration candidates with score.
    """
    try:
        query = query.strip()
        if not query:
            return None
    except:
        return None

    query += END_SYMBOL

    end_idx = len(query) - 1
    states = [(-1, [[START_SYMBOL, START_SYMBOL]])]
    while True:
        finish = True
        for cur_idx, segs in states:
            if cur_idx != end_idx:
                finish = False
                break
        if finish:
            break

        tmp_states = []
        for cur_idx, segs in states:
            # skip finished states
            if cur_idx == end_idx:
                tmp_states.append((cur_idx, segs))

            rest = end_idx - cur_idx
            for i in range(min(rest, MAX_PAIR_GRAM_NUM)):
                # prevent combining the end symbol with other unit
                if cur_idx != end_idx - 1 and cur_idx + i + 1 >= end_idx:
                    break
                seg = query[cur_idx + 1:cur_idx + i + 2]
                cur_idx_ = cur_idx + i + 1
                if seg in candidate_map:
                    trans_set = candidate_map[seg]
                elif len(seg) == 1:
                    trans_set = {VOID_TRANSLITERATION}
                else:
                    continue
                for trans in trans_set:
                    segs_ = segs + [[seg, trans]]
                    tmp_states.append((cur_idx_, segs_))

        if len(tmp_states) < BEAM_SIZE:
            states = tmp_states
        else:
            tmp_states.sort(
                key=lambda x: calc_state_score(x[1], pair_trans_prob, pair_freq),
                reverse=True)
            states = tmp_states[:BEAM_SIZE]
    states.sort(key=lambda x: calc_state_score(x[1], pair_trans_prob, pair_freq),
                reverse=True)

    trans_list = []
    for i in range(min(len(states), final_state_num)):
        trans = ''.join([
            states[i][1][j][1] for j in range(1, len(states[i][1]) - 1)
        ])
        score = calc_state_score(states[i][1], pair_trans_prob, pair_freq)
        trans_list.append((
            trans.replace(VOID_TRANSLITERATION, '').replace(SPACE_SYMBOL, ' '),
            score))
    return trans_list


def transliterate(query,
                  candidate_map,
                  pair_trans_prob,
                  pair_freq,
                  candidate_num,
                  ignore_case=False
                  ):
    try:
        rst = {'jscm': [], 'joint': [], 'entity': []}

        query = query.strip()
        if not query:
            return rst
        if ignore_case:
            query = query.lower()

        # Segment the query
        tokens = [t for t in re.split(TOKEN_SEP_PATTERN, query) if t]
        if len(tokens) == 0:
            return rst
        phrase = Phrase(query, [Token(t, {}) for t in tokens], {})

        # run JSCM
        phrase_trans_list = []
        for token in phrase.tokens:
            trans_list = jscm(token.text,
                              candidate_map,
                              pair_trans_prob,
                              pair_freq,
                              candidate_num
                              )
            if trans_list:
                token.attributes['trans_list'] = trans_list
                if len(phrase_trans_list) == 0:
                    phrase_trans_list = trans_list.copy()
                else:
                    phrase_trans_list = [
                        (i1[0] + i2[0], i1[1] * i2[1])
                        for i1 in phrase_trans_list for i2 in trans_list
                    ]
        phrase_trans_list.sort(key=lambda x: x[1], reverse=True)
        phrase_trans_list = phrase_trans_list[:BEST_STATE_NUM]

        if len(phrase_trans_list) == 1 and len(phrase_trans_list[0][0].strip()) == 0:
            return rst

        # response
        rst['jscm'] = phrase_trans_list
        return rst
    except:
        return {'jscm': [], 'joint': [], 'entity': []}

if __name__ == "__main__":
    candidates, pair_trans_prob, pair_freq = load_model(
        '/Users/limteng/Projects/old_transliterator/data/model/hebrew/hebrew_english.x2y4.0001.joint.tc.model.txt',
        ignore_case=True
    )

    transliterate('פארמנידס', candidates, pair_trans_prob, pair_freq, 10)
    transliterate('טוקימונה', candidates, pair_trans_prob, pair_freq, 10)
    transliterate("שבצ'נקו", candidates, pair_trans_prob, pair_freq, 10)