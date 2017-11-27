#!/usr/bin/env python3
from lxml import etree
from collections import defaultdict
import sys
import os
import logging


'''
 count word frequency from ltf
'''


def process(pdata, wf):
    root = etree.parse(pdata)
    for seg in root.find('DOC').find('TEXT').findall('SEG'):
        for token in seg.findall('TOKEN'):
            token_id = token.get('id')
            token_text = token.text
            start_char = int(token.get('start_char'))
            end_char = int(token.get('end_char'))
            wf[token_text] += 1


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('USAGE: <paths to ltf dir> <output path>')
        exit()

    indir = sys.argv[1]
    outpath = sys.argv[2]
    logger = logging.getLogger()
    logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s')
    logging.root.setLevel(level=logging.INFO)

    wf = defaultdict(int)
    for i in os.listdir(indir):
        logger.info('counting %s' % i)
        process('%s/%s' % (indir, i), wf)

    logger.info('writing...')
    out = open(outpath, 'w')
    for w, f in sorted(wf.items(), key=lambda x: x[1], reverse=True):
        out.write('%s\t%s\n' % (w, f))
    out.close()
