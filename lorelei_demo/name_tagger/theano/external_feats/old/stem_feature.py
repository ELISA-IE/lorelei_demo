import argparse
import codecs
import sys


def stem_feature(upenn_morph_str, input_str):
    #
    # parse upenn morph str
    #
    upenn_morph = dict()
    num_pair_loaded = 0
    for line in upenn_morph_str.splitlines():
        if not line:
            continue
        word, morph, suffix = line.split('\t')

        # select the longest portion as stem
        affix = morph.split(' ')
        stem = sorted(affix, key=lambda x: len(x), reverse=True)[0]
        stem_index = affix.index(stem)
        prefix = affix[:stem_index]
        suffix = affix[stem_index+1:]
        if word != stem and stem.strip():
            upenn_morph[word] = [stem,
                                 ''.join(prefix) if prefix else 'no_prefix',
                                 ''.join(suffix) if suffix else 'no_suffix']
            num_pair_loaded += 1
            sys.stdout.write("%d morph-stem pairs loaded.\r" % num_pair_loaded)
            sys.stdout.flush()
    print('=> %d morph-stem pairs loaded in total.' % len(upenn_morph))

    #
    # bio str input
    #
    res = []
    num_stem = 0
    num_stem_label = 0
    num_label = 0
    for i, line in enumerate(input_str.splitlines()):
        sys.stdout.write('%d tokens in bio processed.\r' % i)
        sys.stdout.flush()

        if not line:
            res.append(line)
            continue

        line = line.split()
        if len(line) == 2 and ':' not in line[1]:
            line = [line[0], 'no_offset', line[1]]
        text = line[0]
        label = line[-1]
        if label != 'O':
            num_label += 1

        if text in upenn_morph:
            stem, prefix, suffix = upenn_morph[text]
            num_stem += 1
            if label != 'O':
                num_stem_label += 1
        else:
            stem, prefix, suffix = text, 'no_prefix', 'no_suffix'

        line = line[:2] + [stem, prefix, suffix] + line[2:]

        res.append(' '.join(line))

    print('=> %.2f%% (%d/%d) tokens stemmed in bio.' % (
        num_stem / len(res) * 100, num_stem, len(res)
    ))
    print('=> %.2f%% (%d/%d) tokens with label are stemmed in bio.' %
          (num_stem_label/num_label*100, num_stem_label, num_label))
    res = '\n'.join(res)

    return res


def write2file(output_str, output):
    with codecs.open(output, 'w', 'utf-8') as f:
        f.write(output_str)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('upenn_morph_seg')
    parser.add_argument('bio_input')
    parser.add_argument('bio_output')
    args = parser.parse_args()

    print('=> loading morph str: %s' % args.upenn_morph_seg)
    upenn_morph_str = codecs.open(args.upenn_morph_seg, 'r', 'utf-8').read()
    bio_input = codecs.open(args.bio_input, 'r', 'utf-8').read()

    output = stem_feature(upenn_morph_str, bio_input)

    write2file(output, args.bio_output)

