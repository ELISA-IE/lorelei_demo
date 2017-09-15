import logging
import argparse
import util
import remove_names
import add_names
import rule
from collections import defaultdict


def reassign_id(tab, runid='RPI_BLENDER'):
    count = defaultdict(int)
    n = 0
    logger.info('--- REASSIGNING ID ---')
    for i in tab:
        qid = 'M_' + '{number:0{width}d}'.format(width=7,
                                                 number=n)
        i.runid = runid
        i.qid = qid
        count[i.etype] += 1
        n += 1

    logger.info('total names: %s' % len(tab))
    for i in count:
        logger.info('%s %s' % (i, count[i]))


if __name__ == '__main__':
    logger = logging.getLogger()
    logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s')
    logging.root.setLevel(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument('pbio', type=str, help='path to bio')
    parser.add_argument('ptab', type=str, help='path to tab')
    parser.add_argument('outpath', type=str, help='output path')
    parser.add_argument('--ppsm', type=str, help='path to psm')
    parser.add_argument('--pgaz', type=str, help='path to gaz')
    parser.add_argument('--psn', type=str, help='path to sn gaz')
    parser.add_argument('--pdes', type=str, help='path to des')
    parser.add_argument('--prule', type=str, help='path to rules file')
    args = parser.parse_args()

    logger.info('loading tab...')
    logger.info('%s' % args.ptab)
    tab = util.read_tab(args.ptab)
    logger.info('done.')
    tab = remove_names.process(tab, ppsm=args.ppsm)
    tab = add_names.process(tab, args.pbio,
                            ppsm=args.ppsm, pgaz=args.pgaz,
                            psn=args.psn, pdes=args.pdes)
    if args.prule:
        tab = rule.process(tab, args.prule)

    reassign_id(tab)
    with open(args.outpath, 'w') as fw:
        fw.write('\n'.join([str(i) for i in tab]))
