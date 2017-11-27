import sys
import re
import logging
from collections import defaultdict


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('USAGE: <path to bio>')
        exit()

    logger = logging.getLogger()
    logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s')
    logging.root.setLevel(level=logging.INFO)

    inpath = sys.argv[1]
    data = re.split('\n\s*\n', open(inpath).read())
    tag_count = defaultdict(int)
    mention_count = defaultdict(int)
    docids = set()
    for i in data:
        prev_beg = -1
        prev_end = -1
        sent = i.split('\n')
        sent_mentions = []
        sent_context = []
        curr_mention = []
        for i, line in enumerate(sent):
            if not line:
                continue
            try:
                assert not line.startswith(' ')
            except AssertionError:
                logger.error('line starts with space:')
                logger.error(repr(line))

            ann = line.split(' ')
            try:
                assert len(ann) >= 2
            except AssertionError:
                logger.error('line is less than two columns')
                logger.error(repr(line))
            tok = ann[0]
            tag = ann[-1]


            if ann[-1] == 'O':
                bio_tag, etype = ('O', None)
            else:
                bio_tag, etype = ann[-1].split('-')
            if bio_tag == 'O':
                if curr_mention:
                    sent_mentions.append(curr_mention)
                    curr_mention = []
            elif bio_tag ==  'B':
                if curr_mention:
                    sent_mentions.append(curr_mention)
                curr_mention = [(tok, etype)]
            elif bio_tag == 'I':
                try:
                    assert curr_mention != []
                except AssertionError:
                    logger.warning('missing B-')
                    logger.warning(repr(line))
                curr_mention.append((tok, etype))
            if i == len(sent) - 1 and curr_mention:
                sent_mentions.append(curr_mention)
            sent_context.append(tok)


            if len(ann) > 2:
                offset = ann[1]
                m = re.match('(.+):(\d+)-(\d+)', offset)
                docid = m.group(1)
                docids.add(docid)
                beg = int(m.group(2))
                end = int(m.group(3))
                try:
                    assert end >= beg
                except AssertionError:
                    logger.error('end is less than beg')
                    logger.error(repr(line))

                try:
                    assert beg > prev_end
                except AssertionError:
                    logger.error('beg is less than the previous end')
                    logger.error(repr(line))
            tag_count[tag] += 1


    logger.info('# of docs: %s' % (len(docids)))
    logger.info('# of sentences: %s' % (len(data)))
    logger.info('tag stats:')
    for t, c in sorted(tag_count.items(), key=lambda x: x[0], reverse=True):
        logger.info('    %s: %s' % (t, c))
    logger.info('done.')
