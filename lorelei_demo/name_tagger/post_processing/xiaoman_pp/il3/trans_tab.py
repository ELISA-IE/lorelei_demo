import os
import sys
import re
from collections import defaultdict
import itertools
import logging
import argparse


logger = logging.getLogger()
logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s')
logging.root.setLevel(level=logging.INFO)


def read_dic(pdic):
    RE_STRIP = r' \([^)]*\)|\<[^)]*\>|,|"|\.|\'|:|-'
    res = defaultdict(lambda : defaultdict(int))
    with open(pdic, 'r') as f:
        for line in f:
            src, trg = line.rstrip('\n').split('\t')
            # trg = ' '.join(re.sub(RE_STRIP, '', trg).strip().split())
            res[src][trg] += 1
    for i in res:
        res[i] = [x for x, y in sorted(res[i].items(),
                                       key=lambda x: x[1], reverse=True)]
    return res


def isListEmpty(inList):
    if isinstance(inList, list):
        return all(map(isListEmpty, inList))
    return False


def partial_trans(mention, dic):
    res = []
    trans_toks = []
    for tok in mention.split(' '):
        if tok in dic:
            trans_toks.append([list(dic[tok])[0]])
        else:
            trans_toks.append([])

    if not isListEmpty(trans_toks):
        for n in range(len(trans_toks)):
            if not trans_toks[n]:
                trans_toks[n] = ['NULL']
        for i in list(itertools.product(*trans_toks)):
            res.append(' '.join(i))
        return '*' + '|'.join(res)
    return None


def main(pdic, tab, outpath=None, match='partial'):
    logger.info('loading dict...')
    dic = read_dic(pdic)
    logger.info('dict size: %s' % len(dic))

    count = {
        'tol': 0,
        'trans': 0
    }

    for i, line in enumerate(tab):
        if not line:
            continue
        tmp = line.rstrip('\n').split('\t')
        mention = tmp[2]
        trans = None
        if mention in dic:
            trans = '|'.join(dic[mention])
        elif match != 'exact':
            trans = partial_trans(mention, dic)
            if match == 'tok_exact':
                if trans and 'NULL' in trans:
                    trans = None
        if not trans:
            trans = 'NULL'
        else:
            count['trans'] += 1
        count['tol'] += 1

        tmp.append(trans)
        tab[i] = '\t'.join(tmp)

    logger.info('# of translated mentions: %s' % count['trans'])
    logger.info('# of total mentions: %s' % count['tol'])

    if outpath:
        with open(outpath, 'w') as fw:
            fw.write('\n'.join(tab))
    else:
        return tab


if __name__ == '__main__':
    matches = ['partial', 'tok_exact', 'exact']
    parser = argparse.ArgumentParser()
    parser.add_argument('pdic', type=str, help='path to dict')
    parser.add_argument('ptab', type=str, help='path to tab')
    parser.add_argument('outpath', type=str, help='output path')
    parser.add_argument('--match', type=str,
                        help='match approach: %s' % matches,
                        default='partial')
    args = parser.parse_args()
    if args.match not in matches:
        print('unrecognizeed match approach: %s' % args.match)
        exit()
    tab = open(args.ptab, 'r').read().split('\n')
    main(args.pdic, tab, args.outpath, match=args.match)
