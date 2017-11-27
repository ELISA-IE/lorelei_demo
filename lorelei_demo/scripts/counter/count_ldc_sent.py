# this script counts the number of IL5 and IL6 sentences in bio file.
import argparse


def count_ldc_sent(input_bio):
    ldc_sent = 0
    num_sent = 0
    for sent in open(input_bio).read().split('\n\n'):
        sent = sent.strip()
        if not sent:
            continue
        num_sent += 1
        offset = sent.split()[1]
        if 'IL5' in offset or 'IL6' in offset:
            ldc_sent += 1
    print('%d sentences in total.' % num_sent)
    print('%d are ldc sentences.' % ldc_sent)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('input_bio')
    args = parser.parse_args()

    count_ldc_sent(args.input_bio)