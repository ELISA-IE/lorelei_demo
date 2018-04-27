import re
import sys
import argparse
import logging
import os
from collections import defaultdict


def read_tab(ptab):
    res = {}
    with open(ptab, 'r') as f:
        for line in f:
            tmp = line.rstrip('\n').split('\t')
            mention = tmp[2]
            mention = mention.replace('"', '')
            kbid = tmp[4]
            etype = tmp[5]
            mtype = tmp[6]
            m = re.match('(.+):(\d+)-(\d+)', tmp[3])
            docid = m.group(1)
            beg = int(m.group(2))
            end = int(m.group(3))
            if docid not in res:
                res[docid] = list()
            res[docid].append((mention, kbid, etype, beg, end))
    return res


def count(tab):
    n = 0
    for docid in tab:
        n += len(tab[docid])
    return n


def read_tab_m2(ptab):
    m2type = defaultdict(lambda: defaultdict(int))
    m2kbid = defaultdict(lambda: defaultdict(int))
    m2trans = {}
    kbid2m = defaultdict(lambda: defaultdict(int))
    with open(ptab, 'r') as f:
        for line in f:
            tmp = line.rstrip('\n').split('\t')
            mention = tmp[2]
            mention = mention.replace('"', '')
            kbid = tmp[4]
            etype = tmp[5]
            mtype = tmp[6]
            m = re.match('(.+):(\d+)-(\d+)', tmp[3])
            docid = m.group(1)
            beg = int(m.group(2))
            end = int(m.group(3))
            trans = tmp[-1]

            m2type[mention][etype] += 1
            m2kbid[mention][kbid] += 1
            m2trans[mention] = trans
            kbid2m[kbid][mention] += 1
    return m2type, m2kbid, m2trans, kbid2m


def count_mention(mention):
    n = 0
    for t in mention:
        n += mention[t]
    return n


if __name__ == '__main__':
    logger = logging.getLogger()
    logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s')
    logging.root.setLevel(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument('pa', type=str, help='path to tab a')
    parser.add_argument('pb', type=str, help='path to tab b')
    parser.add_argument('outdir', type=str, help='output dir')
    args = parser.parse_args()

    logger.info('COMPARING TABS...')
    try:
        os.mkdir(args.outdir)
    except FileExistsError:
        pass

    tab_a = read_tab(args.pa)
    tab_b = read_tab(args.pb)

    logger.info('a: %s' % args.pa)
    logger.info('b: %s' % args.pb)
    logger.info('# docs:')
    logger.info('a: %s' % len(tab_a))
    logger.info('b: %s' % len(tab_b))
    logger.info('# tagged names:')
    logger.info('a: %s' % count(tab_a))
    logger.info('b: %s' % count(tab_b))

    m2type_a, m2kbid_a, m2trans_a, kbid2m_a = read_tab_m2(args.pa)
    m2type_b, m2kbid_b, m2trans_b, kbid2m_b = read_tab_m2(args.pb)
    names_a = set(m2type_a.keys())
    names_b = set(m2type_b.keys())

    with open('%s/a-b' % args.outdir, 'w') as fw:
        fw.write('a - b: %s\n' % len(names_a - names_b))
        for i in sorted(names_a - names_b,
                        key=lambda x: count_mention(m2type_a[x]),
                        reverse=True):
            fw.write('%s\t%s\t%s\n' % (i, dict(m2type_a[i]), m2trans_a[i]))

    with open('%s/b-a' % args.outdir, 'w') as fw:
        fw.write('b - a: %s\n' % len(names_b - names_a))
        for i in sorted(names_b - names_a,
                        key=lambda x: count_mention(m2type_b[x]),
                        reverse=True):
            fw.write('%s\t%s\t%s\n' % (i, dict(m2type_b[i]), m2trans_b[i]))

    with open('%s/a' % args.outdir, 'w') as fw:
        for i in sorted(m2type_a,
                        key=lambda x: count_mention(m2type_a[x]),
                        reverse=True):
            fw.write('%s\t%s\t%s\t%s\t%s\t%s\n' % (i,
                                                 count_mention(m2type_a[i]),
                                                 dict(m2type_a[i]),
                                                 count_mention(m2kbid_a[i]),
                                                 dict(m2kbid_a[i]),
                                                 m2trans_a[i]))

    with open('%s/a_kbid' % args.outdir, 'w') as fw:
        for i in sorted(kbid2m_a,
                        key=lambda x: count_mention(kbid2m_a[x]),
                        reverse=True):
            fw.write('%s\t%s\n' % (i, count_mention(kbid2m_a[i])))
            for j, c in sorted(kbid2m_a[i].items(),
                               key=lambda x: x[1], reverse=True):
                fw.write('\t%s\t%s\t%s\n' % (j,
                                             dict(m2type_a[j]),
                                             m2trans_a[j]))

    with open('%s/b' % args.outdir, 'w') as fw:
        for i in sorted(m2type_b,
                        key=lambda x: count_mention(m2type_b[x]),
                        reverse=True):
            fw.write('%s\t%s\t%s\t%s\t%s\t%s\n' % (i,
                                                   count_mention(m2type_b[i]),
                                                   dict(m2type_b[i]),
                                                   count_mention(m2kbid_b[i]),
                                                   dict(m2kbid_b[i]),
                                                   m2trans_b[i]))

    for i in m2type_a:
        if i not in m2type_b:
            m2type_b[i] = {}
    for i in m2type_b:
        if i not in m2type_a:
            m2type_a[i] = {}
    with open('%s/ab' % args.outdir, 'w') as fw:
        fw.write('mention\ta\tb\n')
        for i in sorted(m2type_a,
                        key=lambda x: \
                        count_mention(m2type_a[x])+count_mention(m2type_b[x]),
                        reverse=True):
            if dict(m2kbid_a[i]) == dict(m2kbid_b[i]):
                continue
            allnil = True
            for k in m2kbid_a[i]:
                if not k.startswith('NIL'):
                    allnil = False
            for k in m2kbid_b[i]:
                if not k.startswith('NIL'):
                    allnil = False
            if allnil:
                continue
            fw.write('%s\t%s\t%s\t%s\t%s\n' % \
                     (i, dict(m2type_a[i]), dict(m2type_b[i]),
                      dict(m2kbid_a[i]), dict(m2kbid_b[i])))
