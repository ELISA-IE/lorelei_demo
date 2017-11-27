# this script merge the tags of gold bio and system bio
import argparse


def merge_bio(gold_bio, sys_bio):
    gold_bio = parse_bio(open(gold_bio).read())
    sys_bio = parse_bio(open(sys_bio).read())

    sys_labels = {w[1]: w[-1] for sent in sys_bio for w in sent}

    out_bio = []
    missing_tokens = 0
    for sent in gold_bio:
        for i, w in enumerate(sent):
            if w[1] not in sys_labels:
                missing_tokens += 1
                sent[i].append('O')
            else:
                sent[i].append(sys_labels[w[1]])
        out_bio.append(sent)

    out_bio_str = '\n\n'.join(
        ['\n'.join([' '.join(w) for w in sent]) for sent in out_bio]
    )

    print('%d tokens in gold bio are not found in sys bio' % missing_tokens)
    return out_bio_str


def parse_bio(bio_str):
    bio = []
    for sent in bio_str.split('\n\n'):
        sent = sent.strip()
        if not sent:
            continue
        words = [w.split() for w in sent.splitlines()]
        bio.append(words)

    return bio


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('gold_bio')
    parser.add_argument('sys_bio')
    parser.add_argument('out_path')
    args = parser.parse_args()

    merged_bio_str = merge_bio(args.gold_bio, args.sys_bio)

    with open(args.out_path, 'w') as f:
        f.write(merged_bio_str)

