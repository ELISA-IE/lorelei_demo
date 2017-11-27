import argparse
import codecs
import sys
import collections


def clustering_feature(cluster_path_str, input_str):
    #
    # parse cluster path
    #
    cluster_path = dict()
    num_lines_loaded = 0
    path_len = 0
    for line in cluster_path_str.splitlines():
        if not line:
            continue
        cluster, word, frequency = line.split('\t')

        cluster_path[word] = cluster

        if len(cluster) > path_len:
            path_len = len(cluster)

        num_lines_loaded += 1
        if num_lines_loaded % 50 == 0:
            sys.stdout.write("%d word paths loaded.\r" % num_lines_loaded )
            sys.stdout.flush()

    # padding short paths
    for k, v in cluster_path.items():
        v += '0' * (path_len - len(v))
        cluster_path[k] = v

    print('=> %d words with cluster path are loaded in total.' %
          len(cluster_path))
    print('max path len is %d' % path_len)

    #
    # bio str input
    #
    res = []
    unk_cluster_path = ['0' * int(0.4*path_len),
                        '0' * int(0.6*path_len),
                        '0' * int(0.8*path_len),
                        '0' * path_len]
    cluster_coverage = collections.defaultdict(int)
    token_count = collections.defaultdict(int)
    token_with_labels = collections.defaultdict(int)
    token_with_labels_covered = collections.defaultdict(int)
    for i, line in enumerate(input_str.split('\n\n')):
        sys.stdout.write('%d sentences in bio processed.\r' % i)
        sys.stdout.flush()

        line = line.strip()
        if not line:
            res.append(line)
            continue

        s_cluster_path = []
        tokens = []
        for token in line.splitlines():
            token = token.split()
            if len(token) == 2 and ':' not in token[1]:
                token = [token[0], 'no_offset', token[1]]
            tokens.append(token)
            text = token[0]
            label = token[-1]

            token_count[text] += 1
            if label != 'O':
                token_with_labels[text] += 1
            if text in cluster_path:
                c_path = cluster_path[text]
                cluster_coverage[text] += 1
                if label != 'O':
                    token_with_labels_covered[text] += 1
            else:
                c_path = '0' * path_len

            s_cluster_path.append([c_path[:int(0.4*path_len)],
                                   c_path[:int(0.6*path_len)],
                                   c_path[:int(0.8*path_len)],
                                   c_path])

        s = []
        # add prev and next word cluster path
        for j in range(len(s_cluster_path)):
            if j == 0:
                prev_cp = unk_cluster_path
            else:
                prev_cp = s_cluster_path[j-1]
            if j == len(s_cluster_path)-1:
                next_cp = unk_cluster_path
            else:
                next_cp = s_cluster_path[j+1]
            tokens[j] = tokens[j][:2] + prev_cp + s_cluster_path[j] + \
                        next_cp + tokens[j][2:]

            s.append(' '.join(tokens[j]))

        res.append('\n'.join(s))

    res = '\n\n'.join(res)

    print('%d / %d (%.2f) tokens have clusters.' % (sum(cluster_coverage.values()),
                                                    sum(token_count.values()),
                                                    sum(cluster_coverage.values()) / sum(token_count.values())))
    print('%d / %d (%.2f) unique tokens have clusters.' % (len(cluster_coverage),
                                                           len(token_count),
                                                           len(cluster_coverage) / len(token_count)))

    print('%d / %d (%.2f) labeled tokens have clusters.' % (
        sum(token_with_labels_covered.values()),
        sum(token_with_labels.values()),
        sum(token_with_labels_covered.values()) / sum(token_with_labels.values())
    ))
    print('%d / %d (%.2f) labeled unique tokens have clusters.' % (
        len(token_with_labels_covered),
        len(token_with_labels),
        len(token_with_labels_covered) / len(token_with_labels)
    ))

    return res


def write2file(output_str, output):
    with codecs.open(output, 'w', 'utf-8') as f:
        f.write(output_str)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('cluster_path')
    parser.add_argument('bio_input')
    parser.add_argument('bio_output')
    args = parser.parse_args()

    print('=> loading cluster path str: %s' % args.cluster_path)
    cluster_path_str = codecs.open(args.cluster_path, 'r', 'utf-8').read()
    bio_input = codecs.open(args.bio_input, 'r', 'utf-8').read()

    output = clustering_feature(cluster_path_str, bio_input)

    write2file(output, args.bio_output)

