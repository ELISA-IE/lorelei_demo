# this script generates offset for bio.
# option: splits bio into document of 10 sentences
import argparse
import os
from collections import OrderedDict


def bio2bio_offset(bio_str, d_id, split=0):
    bio_offset = OrderedDict()
    if split:
        sents = [sent for sent in bio_str.strip().split('\n\n') if sent]
        bio_sents = dict()
        step = split
        for i in range(0, len(sents), step):
            bio_sents[d_id+'_%d' % (i/step)] = sents[i:i+step]
    else:
        bio_sents = {d_id: [sent for sent in bio_str.strip().split('\n\n')]}

    for d_id, sents in bio_sents.items():
        current_offset = 0
        raw_doc = ''
        bio_str = []
        for s in sents:
            sent = []
            for w in s.splitlines():
                w_items = w.split()
                raw_doc += w_items[0] + ' '
                start = current_offset
                end = start + len(w_items[0]) - 1
                assert raw_doc[start:end+1] == w_items[0]
                offset = '%s:%d-%d' % (d_id, start, end)
                sent.append(' '.join(w_items[:1] + [offset] + w_items[1:]))
                current_offset = end + 2
            bio_str.append('\n'.join(sent))
        bio_offset[d_id] = '\n\n'.join(bio_str)

    return bio_offset


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('bio')
    parser.add_argument('out_dir')
    parser.add_argument('--split', default=0, type=int,
                        help='split bio into multiple documents')

    args = parser.parse_args()

    d_id = os.path.basename(args.bio).replace('.bio', '')
    bio_offset = bio2bio_offset(open(args.bio).read(), d_id, args.split)

    for d_id, bio in bio_offset.items():
        with open(os.path.join(args.out_dir, d_id+'.bio'), 'w') as f:
            f.write(bio)


