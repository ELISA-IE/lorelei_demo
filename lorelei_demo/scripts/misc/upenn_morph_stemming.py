import logging
import re
import sys


def read_upenn_morph(pdata):
    upenn_morph = {}
    with open(pdata, 'r') as f:
        for line in f:
            tmp = line.rstrip('\n').split('\t')
            word = tmp[0]
            morphemes = tmp[1]
            if not tmp[2]:
                continue

            try:
                assert word not in upenn_morph
            except AssertionError:
                pass
                # logger.info("duplicate: %s" % word)

            m = re.search('(\S+) \$ \$', tmp[2])
            if m:
                root = m.group(1)
            else:
                logger.info('unexpected error: %s'  % str(sys.exc_info()))
                logger.info(repr(line))
                exit()

            upenn_morph[word] = root
    return upenn_morph


def process(pum, pbio, outpath):
    logger.info('loading upenn morph...')
    upenn_morph = read_upenn_morph(pum)
    logger.info('done.')

    count = {
        'tol': 0,
        'match': 0,
        'stem': 0
    }
    out = open(outpath, 'w')
    with open(pbio, 'r') as f:
        for line in f:
            tmp = line.rstrip('\n').split(' ')
            word = tmp[0]
            if word in upenn_morph:
                count['match'] += 1
                stem = upenn_morph[word]
                if stem != word:
                    count['stem'] += 1
                    tmp[0] = stem
            out.write('%s\n' % (' '.join(tmp)))
            count['tol'] += 1

    logger.info('Total token: %s' % count['tol'])
    logger.info('Matched token: %s' % count['match'])
    logger.info('Stemmed token: %s' % count['stem'])


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print('USAGE: <path to upenn morph> <path to input bio> <output path>')
        exit()

    logger = logging.getLogger()
    logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s')
    logging.root.setLevel(level=logging.INFO)

    process(sys.argv[1], sys.argv[2], sys.argv[3])
