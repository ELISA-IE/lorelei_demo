import argparse
import codecs
import sys
import operator
import os


def bio2rsd(bio_str):
    bio = parse_bio(bio_str)

    rsd = {}
    for d_id, sents in bio.items():
        try:
            # sort sent by its start char
            sorted_sents = sorted(sents, key=lambda x: x[0][1])

            rsd_str = ''
            prev_token_end = -1
            for s in sorted_sents:
                for i, t in enumerate(s):
                    if i == 0:
                        delimiter = '\n'
                    else:
                        delimiter = ' '
                    rsd_str += delimiter * (t[1] - prev_token_end - 1) + t[0]

                    assert rsd_str[t[1]:t[2]+1] == t[0], 'token offset error.'

                    prev_token_end = t[2]

            rsd[d_id] = rsd_str
        except AssertionError as e:
            print('bio2rsd error', d_id, e)

    return rsd


def parse_bio(bio_str):
    print('=> parsing bio string...')
    bio = {}
    num_token = 0
    for i, sent in enumerate(bio_str.split('\n\n')):
        sent = sent.strip()
        if not sent:
            continue
        tokens = []
        d_id = ''
        for t in sent.splitlines():
            word, offset = operator.itemgetter(0, 1)(t.split())
            d_id, o = offset.split(':')
            start, end = o.split('-')

            tokens.append((word, int(start), int(end)))
        try:
            bio[d_id].append(tokens)
        except KeyError:
            bio[d_id] = [tokens]

        num_token += len(tokens)

        sys.stdout.write('%d sentences, %d tokens parsed.\r' % (i, num_token))
        sys.stdout.flush()

    sys.stdout.write('%d sentences, %d tokens parsed.\n' %
                     (len(bio_str.split('\n\n')), num_token))

    return bio


def write2file(rsd_str, rsd_dir):
    for d_id, rsd_str in rsd.items():
        with codecs.open(os.path.join(rsd_dir, d_id+'.rsd.txt'),
                         'w', 'utf-8') as f:
            f.write(rsd_str)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('bio_file')
    parser.add_argument('rsd_dir')
    args = parser.parse_args()

    bio_str = codecs.open(args.bio_file, 'r', 'utf-8').read()

    rsd = bio2rsd(bio_str)

    write2file(rsd, args.rsd_dir)
