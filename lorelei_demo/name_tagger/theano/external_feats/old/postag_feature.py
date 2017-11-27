import argparse
import codecs
import sys
import subprocess
import os
import tempfile


def postag_feature(postag_model, bio_input):
    print('=> running postagger...')
    tagger_script = '/nas/data/m1/zhangb8/ml/theano/wrapper/dnn_tagger.py'
    print('tagger script: %s' % tagger_script)
    tmp_output = tempfile.mktemp()

    cmd = ['python', tagger_script, bio_input, tmp_output, postag_model, '-b',
           '--core_num', '5']
    print('command: %s' % ' '.join(cmd))
    subprocess.call(cmd)

    # parse pos-tagger output
    res = []
    for line in open(tmp_output):
        line = line.strip()
        if not line:
            res.append(line)
            continue
        items = line.split()
        if len(items) == 2 and ':' not in items[1]:
            items = [items[0], 'no_offset', items[1]]
        res.append(' '.join(items[:2] + [items[-1]] + items[2:-1]))

    return '\n'.join(res)


def write2file(output_str, output):
    with codecs.open(output, 'w', 'utf-8') as f:
        f.write(output_str)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('postag_model')
    parser.add_argument('bio_input')
    parser.add_argument('bio_output')
    args = parser.parse_args()

    postag_model = args.postag_model
    bio_input = args.bio_input

    output = postag_feature(postag_model, bio_input)

    write2file(output, args.bio_output)

