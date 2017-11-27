import argparse
import codecs
import os


def split_tab(tab_str):
    tabs = dict()
    lines = tab_str.strip().splitlines()
    for i, line in enumerate(lines):
        if not line:
            continue
        line_doc_id = line.split('\t')[3].split(':')[0]
        try:
            tabs[line_doc_id].append(line)
        except KeyError:
            tabs[line_doc_id] = [line]

    assert sum([len(t) for _, t in tabs.items()]) == len(lines)

    print('%d lines in tab processed.' % len(lines))
    print('%d documents split.' % len(tabs))

    return tabs


def write2file(tabs, ouput_dir):
    for doc_id, tab in tabs.items():
        with codecs.open(os.path.join(ouput_dir, doc_id+'.tab'),
                         'w', 'utf-8') as f:
            f.write('\n'.join(tab))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('input_tab_fp', type=str,
                        help='tab file path')
    parser.add_argument('output_dir', type=str,
                        help='split tab files dir')

    args = parser.parse_args()

    tabs = split_tab(open(args.input_tab_fp).read())

    try:
        os.mkdir(args.output_dir)
    except FileExistsError:
        pass

    write2file(tabs, args.output_dir)
