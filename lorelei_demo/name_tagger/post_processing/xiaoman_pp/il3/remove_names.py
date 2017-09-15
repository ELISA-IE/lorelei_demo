import re
import sys
import logging
import string
import argparse
import util
from collections import defaultdict


logger = logging.getLogger()
logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s')
logging.root.setLevel(level=logging.INFO)
LONG_NAME_THRES = 15


def process(tab, outpath=None, ppsm=None, verbose=True):
    new_tab = []
    histories = defaultdict(int)
    psm = None
    if ppsm:
        psm = util.read_psm(ppsm)

    logger.info('--- REMOVING NAMES ---')
    for i in tab:
        remove = False

        # 1. Is digits
        if i.mention.isdigit():
            if psm and i.docid in psm and i.mention in psm[i.docid]:
                pass
            elif 'SN_' in i.docid:
                pass
            else:
                his = 'IS_DIGITS %s | %s' % (i.mention, i.etype)
                histories[his] += 1
                remove = True
                continue

        # 2. Is punctuation
        translation = str.maketrans('', '', string.punctuation);
        s = i.mention.translate(translation)
        if s == '':
            his = 'IS_PUNCT %s | %s' % (i.mention, i.etype)
            histories[his] += 1
            remove = True
            continue

        # 3. Contains HTTP
        if re.search('http', i.mention):
            his = 'HAS_HTTP %s | %s' % (i.mention, i.etype)
            histories[his] += 1
            remove = True
            continue

        # 4. Contains digits
        if re.search('\d+', i.mention):
            if psm and i.docid in psm and i.mention in psm[i.docid]:
                pass
            elif 'SN_' in i.docid:
                pass
            else:
                his = 'HAS_DIGITS %s | %s' % (i.mention, i.etype)
                histories[his] += 1
                remove = True
                continue

        # 5. Long names
        if len(i.mention.split()) >= LONG_NAME_THRES:
            his = 'IS_LONG(%s) %s | %s' % (LONG_NAME_THRES, i.mention, i.etype)
            histories[his] += 1
            remove = True
            continue

        # 0. Rules
        if re.search('\d+\:\d+|\d+\:\d+\:\d+', i.mention):
            his = 'RULE %s | %s' % (i.mention, i.etype)
            histories[his] += 1
            remove = True
        if re.search('.+\.jpg', i.mention):
            his = 'RULE %s | %s' % (i.mention, i.etype)
            histories[his] += 1
            remove = True

        if not remove:
            new_tab.append(i)

    if verbose:
        logger.info('%s names are removed' % len(histories))
        for i, c in sorted(histories.items(), key=lambda x: x[1], reverse=True):
            logger.info('  %s | %s' % (c, i))

    if outpath:
        with open(outpath, 'w') as fw:
            fw.write('\n'.join([str(i) for i in new_tab]))
    else:
        return new_tab


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('ptab', type=str, help='path to tab')
    parser.add_argument('outpath', type=str, help='output path')
    parser.add_argument('--ppsm', type=str, help='path to psm')
    args = parser.parse_args()

    tab = util.read_tab(args.ptab)
    process(tab, outpath=args.outpath, ppsm=args.ppsm)
