import re
import sys
import logging
import argparse
import util
from util import TacTab
from collections import defaultdict


logger = logging.getLogger()
logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s')
logging.root.setLevel(level=logging.INFO)


def process(tab, prule, outpath=None, verbose=True):
    new_tab = []
    count = defaultdict(int)
    histories = defaultdict(int)
    logger.info('--- APPLYING RULES ---')
    rule = util.read_rule(prule)
    for i in tab:
        rm = False
        if i.mention in rule and i.etype in rule[i.mention]:
            op = rule[i.mention][i.etype]
            if op[0] == 'mv':
                his = '%s: %s | %s -> %s' % (op[0], i.mention,
                                            i.etype, ' | '.join(op[1]))
                i.etype = op[1][0]
            elif op[0] == 'rm':
                rm = True
                his = '%s: %s | %s | %s' % (op[0], i.mention,
                                            i.etype, ' | '.join(op[1]))
            count[op[0]] += 1
            histories[his] += 1
        if not rm:
            new_tab.append(i)

    for i in count:
        logger.info('# of %s: %s' % (i, count[i]))
    if verbose:
        for i, c in sorted(histories.items(), key=lambda x: x[1], reverse=True):
            logger.info('%s | %s' % (i, c))
    tab = new_tab
    if outpath:
        with open(outpath, 'w') as fw:
            fw.write('\n'.join([str(i) for i in tab]))
    else:
        return tab


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('ptab', type=str, help='path to tab')
    parser.add_argument('prule', type=str, help='path to rules file')
    parser.add_argument('outpath', type=str, help='output path')
    args = parser.parse_args()

    tab = util.read_tab(args.ptab)
    process(tab, args.prule, outpath=args.outpath)
