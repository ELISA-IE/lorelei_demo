import os
import re
import argparse
from collections import defaultdict


def split_bio(pdata, outdir):
    res = defaultdict(list)
    data = re.split('\n\s*\n', open(pdata, 'r').read())
    for d in data:
        if not d:
            continue
        sent_docid = None
        for line in d.split('\n'):
            if not line:
                continue
            if line.startswith(' '):
                continue
            ann = line.split(' ')
            assert len(ann) >= 2
            tok = ann[0]
            offset = ann[1]
            docid, beg, end = re.match('(.+):(\d+)-(\d+)', offset).group(1,2,3)
            if sent_docid:
                assert sent_docid == docid
            sent_docid = docid
        res[sent_docid].append(d)

    count = {}
    count['docs'] = len(res)
    count['sents'] = 0
    for docid in res:
        count['sents'] += len(res[docid])
        with open('%s/%s.bio' % (outdir, docid), 'w') as fw:
            fw.write('\n\n'.join(res[docid]))
    print(count)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input_bio_fp', type=str, help='path to bio file')
    parser.add_argument('output_dir', type=str, help='output dir')
    args = parser.parse_args()

    try:
        os.mkdir(args.output_dir)
    except FileExistsError:
        pass

    split_bio(args.input_bio_fp, args.output_dir)
