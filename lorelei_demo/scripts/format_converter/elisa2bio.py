import argparse
import xml.etree.ElementTree as ET
import gzip
import sys


def elisa2bio(elisa_root):
    doc_num = 0
    #
    # generate bio
    #
    print("=> elisa2bio generating bio...")
    bio_results = []
    for doc in elisa_root.findall('DOCUMENT'):
        doc_num += 1
        doc_id = doc.get('id')
        bio_resut = []
        for seg in doc.findall('SEGMENT'):
            try:
                seg_src = seg.find('SOURCE')
                seg_src_start_char = int(seg_src.get('start_char'))
                seg_src_end_char = int(seg_src.get('end_char'))
                seg_src_orig_raw = seg_src.find('ORIG_RAW_SOURCE').text
                # use orig_raw as tokenized text if not tokenization founds
                if seg_src.find('LRLP_TOKENIZED_SOURCE') is None:
                    seg_src_tokenized = seg_src_orig_raw
                else:
                    seg_src_tokenized = seg_src.find('LRLP_TOKENIZED_SOURCE').text
                # ignore empty token here
                seg_src_tokenized = [item
                                     for item in seg_src_tokenized.split(' ')
                                     if item]
                seg_src_id = seg_src.get('id')

                sent_indexer = 0
                token_offset = []
                for i in range(len(seg_src_tokenized)):
                    token = seg_src_tokenized[i]

                    while not seg_src_orig_raw[sent_indexer:].startswith(token) \
                            and sent_indexer < len(seg_src_orig_raw):
                        sent_indexer += 1

                    token_start_char = sent_indexer
                    token_end_char = token_start_char + len(token) - 1
                    assert seg_src_orig_raw[token_start_char:token_end_char+1] == token, \
                        'token offset error.'

                    token_offset.append((seg_src_start_char+token_start_char,
                                         seg_src_start_char+token_end_char))
                    sent_indexer = token_end_char + 1

                assert len(seg_src_tokenized) == len(token_offset), \
                    'tokenization error.'
                bio_resut.append('\n'.join(['%s %s:%d-%d' %
                                            (seg_src_tokenized[i],
                                             doc_id,
                                             token_offset[i][0],
                                             token_offset[i][1])
                                            for i in range(len(token_offset))]))
            except (AssertionError, AttributeError) as e:
                print('\t%s in %s: ' % (seg_src_id, doc_id), e)
                continue

        bio_results.append('\n\n'.join(bio_resut))

        sys.stdout.write('%d documents processed.\r' % doc_num)
        sys.stdout.flush()

    print("%d documents processed in total." % doc_num)

    bio_str = '\n\n'.join(bio_results)+'\n'

    return bio_str


def write2file(bio_str, output_file):
    with open(output_file, 'w') as f:
        f.write(bio_str)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('elisa_file', type=str,
                        help='input elisa file path')
    parser.add_argument('output_file', type=str,
                        help='output bio file')

    args = parser.parse_args()

    #
    # parse elisa file
    #
    elisa_file = args.elisa_file
    print("=> parsing elisa file..."),
    if elisa_file.endswith('.gz'):
        with gzip.open(elisa_file, 'rb') as f:
            elisa_file_content = f.read()
        root = ET.fromstring(elisa_file_content)
    else:
        root = ET.parse(elisa_file)
    print("done")

    bio_str = elisa2bio(root)

    write2file(bio_str, args.output_file)
