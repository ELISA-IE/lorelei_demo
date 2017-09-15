import os
import sys
import re
from collections import defaultdict
import itertools
import logging
import argparse
import ujson as json
import urllib
from urllib.request import urlopen
import functools


logger = logging.getLogger()
logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s')
logging.root.setLevel(level=logging.INFO)

API_DATASET = {
    'il5': 'Tigrinya_Dictionary',
    'il6': 'Oromo_Dictionary',
}
API = 'http://blender03.cs.rpi.edu:8086/resource/lexicon?' \
      'dataset=%s&morph=true&query=%s'

pdes_il6 = '/nas/data/m1/panx2/lorelei/data/dict/il6/designator.gaz'
designators_il6 = set()
designators_eng = set()
with open(pdes_il6, 'r') as f:
    for line in f:
        tmp = line.rstrip('\n').split('\t')
        if tmp[1] == 'GPE':
            designators_il6.add(tmp[0])
            designators_eng.add(tmp[3].lower())


@functools.lru_cache(maxsize=None)
def trans_api(query, lang):
    query = query.replace('@', '').replace('#', '')
    url = API % (API_DATASET[lang], urllib.parse.quote_plus(query))
    res = json.loads(urlopen(url).read().decode('utf-8'))
    trans = defaultdict(int)
    for i in res:
        if '_GIZA' in i['lexicon']:
            continue

        if 'Clean_816' in i['lexicon']:
            priority = 5 * i['priority']
        elif 'clean' in i['lexicon'].lower():
            priority = 2 * i['priority']
        elif i['lexicon'] == 'Oromia_regions':
            priority = 2 * i['priority']
        else:
            priority = 1 * i['priority']

        trans[i['gloss']] += priority
    return [i for i, c in sorted(trans.items(),
                                 key=lambda x: x[1], reverse=True)]


def main(tab, lang, outpath=None):
    count = {
        'tol': 0,
        'trans': 0
    }

    for i, line in enumerate(tab):
        if not line:
            continue
        tmp = line.rstrip('\n').split('\t')
        mention = tmp[2]
        trans = trans_api(mention, lang)

        if not trans and lang == 'il6':
            toks = tmp[2].split(' ')
            if toks[0] in designators_il6:
                mention = ' '.join(toks[1:])
                trans = trans_api(mention, lang)

        if not trans:
            trans = 'NULL'
        else:
            trans = '|'.join(trans)
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
    parser = argparse.ArgumentParser()
    parser.add_argument('ptab', type=str, help='path to tab')
    parser.add_argument('outpath', type=str, help='output path')
    parser.add_argument('lang', type=str, help='lang')
    args = parser.parse_args()
    tab = open(args.ptab, 'r').read().split('\n')
    main(tab, args.lang, args.outpath)
