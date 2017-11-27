# this script counts term frequency in plain text. It uses space as delimiter.
# term frequency is used for morphology analysis

import argparse
import codecs
import sys


def count(plain_text):
    term_frequency = dict()
    num_lines_processed = 0
    for line in codecs.open(plain_text, 'r', 'utf-8'):
        terms = line.strip().split(' ')
        for t in terms:
            try:
                term_frequency[t] += 1
            except KeyError:
                term_frequency[t] = 1

        num_lines_processed += 1

        sys.stdout.write('%d lines processed.\r' % num_lines_processed)
        sys.stdout.flush()

    print('totally %d lines processed.' % num_lines_processed)

    return term_frequency


def write2file(term_frequency, output):
    sorted_term_frequency = sorted(term_frequency.items(),
                                   key=lambda x: x[1],
                                   reverse=True)
    with codecs.open(output, 'w', 'utf-8') as f:
        for term, frequency in sorted_term_frequency:
            f.write('%s %d\n' % (term, frequency))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('plain_text')
    parser.add_argument('output')
    args = parser.parse_args()

    term_frequency = count(args.plain_text)

    write2file(term_frequency, args.output)
