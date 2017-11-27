#!/usr/bin/env python3
import gzip
from lxml import etree
from collections import defaultdict
import sys
import logging


'''
 count word frequency from elisa data
'''


def process(pdata, wf):
    data = gzip.open(pdata, 'rb')
    context = etree.iterparse(data, events=('end',),
                              tag='LRLP_TOKENIZED_SOURCE')
    for event, elem in context:
        if not elem.text:
            logger.error('elem.text is None')
            continue
        toks = elem.text.split()
        for tok in toks:
            wf[tok] += 1

        elem.clear()
        while elem.getprevious() is not None:
            del elem.getparent()[0]
    del context


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('USAGE: <paths to elisa.*.xml.gz> <output path>')
        exit()

    paths = sys.argv[1:-1]
    outpath = sys.argv[-1]
    logger = logging.getLogger()
    logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s')
    logging.root.setLevel(level=logging.INFO)

    wf = defaultdict(int)
    for path in paths:
        logger.info('counting %s...' % path)
        process(path, wf)

    logger.info('writing...')
    out = open(outpath, 'w')
    for w, f in sorted(wf.items(), key=lambda x: x[1], reverse=True):
        out.write('%s\t%s\n' % (w, f))
    out.close()
