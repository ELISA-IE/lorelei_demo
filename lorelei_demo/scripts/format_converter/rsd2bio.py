#encoding=utf-8
import os
import argparse
import sys
import itertools
import codecs

# dirty import from current dir
script_dirname = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dirname)
from tokenizer import Tokenizer


def rsd2bio(rsd_str, doc_id,
            seg_option='linebreak',
            tok_option='unitok',
            re_segment=False):
    tokenizer = Tokenizer(seg_option, tok_option)

    if re_segment:
        # running segmentation and tokenization, then re-segment the tokenized
        # sentences (use space to concatenate tokens. this solves segmentation
        # problem, e.g. How are you?I'm fine.).
        sents = tokenizer.run_segmenter(rsd_str)
        raw_tokens = tokenizer.run_tokenizer(sents)

        # re-segment tokenized sentence
        num_sent_reseg = 0
        tokens = []
        for i, t in enumerate(raw_tokens):
            reseg = [item.split() for item in tokenizer.run_segmenter(' '.join(t))]
            if len(reseg) > 1:
                num_sent_reseg += 1

            tokens += reseg

        # compute offset for each token
        indexer = 0
        token_offset = []
        for i, t in enumerate(itertools.chain(*tokens)):
            while not rsd_str[indexer:].startswith(t) and \
                            indexer < len(rsd_str):
                indexer += 1
            if indexer < len(rsd_str):
                t_start = indexer
                t_end = t_start + len(t) - 1
                assert rsd_str[t_start:t_end + 1] == t, \
                    "re_segment token offset not match %s-%d" % (doc_id, i)
                token_offset.append((t_start, t_end))
                indexer = t_end + 1

        assert len(token_offset) == len(list(itertools.chain(*tokens))), \
            "re_segment tokenization offset error in: %s" % doc_id

        # recover sent using tokens
        sents = []
        prev_token_end = token_offset[0][0]-1
        token_index = 0
        for i, t in enumerate(tokens):
            sent = ''
            for j, item in enumerate(t):
                if j == 0:
                    prev_token_end = token_offset[token_index][0] - 1

                sent += ' ' * (token_offset[token_index][0] - prev_token_end - 1) + item

                prev_token_end = token_offset[token_index][1]

                token_index += 1

            assert sent in rsd_str, \
                're_segment sentence offset error.'

            sents.append(sent)

    else:
        # running segmentation and tokenization
        sents = tokenizer.run_segmenter(rsd_str)
        tokens = tokenizer.run_tokenizer(sents)

    # generate offset for sentences and tokens
    indexer = 0
    sent_offset = []
    for i, s in enumerate(sents):
        while not rsd_str[indexer:].startswith(s) and indexer < len(rsd_str):
            indexer += 1
        if indexer < len(rsd_str):
            sent_start = indexer
            sent_end = sent_start + len(s) - 1
            assert rsd_str[sent_start:sent_end+1] == s, \
                "sentence offset not match %s-%d" % (doc_id, i)
            sent_offset.append((sent_start, sent_end))
            indexer = sent_end + 1

    assert len(sent_offset) == len(sents), \
        "sentence segmentation offset error in: %s" % doc_id

    token_offsets = []
    for i, tok in enumerate(tokens):
        sent_text = sents[i]
        indexer = 0
        t_offset = []
        for j, t in enumerate(tok):
            while not sent_text[indexer:].startswith(t) and \
                            indexer < len(sent_text):
                indexer += 1
            if indexer < len(sent_text):
                t_start = indexer
                t_end = t_start + len(t) - 1
                assert sent_text[t_start:t_end+1] == t, \
                    "token offset not match %s-%d-%d" % (doc_id, i, j)
                t_offset.append((t_start, t_end))
                indexer = t_end + 1
        token_offsets.append(t_offset)

        assert len(t_offset) == len(tok), \
            "tokenization offset error in: %s-%d" % (doc_id, i)

    # convert seg/tok result to ltf
    bio_sents = []

    for i in range(len(sents)):
        seg_start_char = sent_offset[i][0]
        sent = []
        for j in range(len(tokens[i])):
            tok_text = tokens[i][j]
            if not tok_text:
                continue
            tok_start_char = int(token_offsets[i][j][0]) + seg_start_char
            tok_end_char = int(token_offsets[i][j][1]) + seg_start_char

            assert rsd_str[tok_start_char:tok_end_char+1] == tok_text

            sent.append('%s %s:%d-%d' % (tok_text,
                                         doc_id,
                                         tok_start_char,
                                         tok_end_char))
        bio_sents.append('\n'.join(sent))

    return '\n\n'.join(bio_sents)


def write2file(bio_results, bio_file):
    with open(bio_file, 'w') as f:
        f.write('\n\n'.join(bio_results))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('rsd_input', type=str,
                        help='input rsd file path or directory.')
    parser.add_argument('bio_file', type=str,
                        help='output ltf file path or directory.')
    t = Tokenizer()
    parser.add_argument('--seg_option', default='linebreak',
                        help="segmentation options: %s (default is linebreak)" %
                             ', '.join(t.segmenters.keys()))
    parser.add_argument('--tok_option', default='unitok',
                        help="tokenization options: %s (default is unitok)" %
                             ', '.join(t.tokenizers.keys()))
    parser.add_argument('--extension', default='.rsd.txt',
                        help="extension of rsd file")
    parser.add_argument('--re_segment', action='store_true', default=False,
                        help='first run tokenizaiton, and then segmentation.')

    args = parser.parse_args()

    input_rsd = args.rsd_input
    bio_file = args.bio_file
    seg_option = args.seg_option
    tok_option = args.tok_option
    extension = args.extension
    re_segment = args.re_segment

    rsd_files = []
    if os.path.isdir(input_rsd):
        for fn in os.listdir(input_rsd):
            if extension not in fn:
                continue
            rsd_files.append(os.path.join(input_rsd, fn))
    else:
        rsd_files = [input_rsd]

    bio_results = []
    for k, rsd_f in enumerate(rsd_files):
        try:
            rsd_str = codecs.open(rsd_f, 'r', 'utf-8').read()

            doc_id = os.path.basename(rsd_f).replace(extension, '')

            bio_str = rsd2bio(rsd_str, doc_id, seg_option, tok_option,
                              re_segment)

            bio_results.append(bio_str)

        except AssertionError as e:
            print(e)

        sys.stdout.write('%d files processed.\r' % k)
        sys.stdout.flush()

    write2file(bio_results, bio_file)
    sys.stdout.write('%d files processed.' % len(rsd_files))
