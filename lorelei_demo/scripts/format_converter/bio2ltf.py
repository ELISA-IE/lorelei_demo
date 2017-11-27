import io
import argparse
import sys
import os
import operator
import xml.dom.minidom
import xml.etree.ElementTree as ET


def bio2ltf(bio_str, doc_id='', with_offset=False, delimiter=' '):
    if with_offset:
        ltf_root = bio2ltf_with_offset(bio_str)
    else:
        ltf_root = bio2ltf_no_offset(bio_str, doc_id, delimiter)

    return ltf_root


def bio2ltf_no_offset(bio_str, doc_id, delimiter):
    bio_sents = bio_str.split('\n\n')
    sents = []
    for sent in bio_sents:
        sent = sent.strip()
        if not sent:
            continue
        s = []
        for line in sent.strip().splitlines():
            token = line.split(' ')[0]
            s.append(token)
        sents.append(s)

    doc_text = '\n'.join([delimiter.join(sent) for sent in sents])

    root = ET.Element('LCTL_TEXT')
    doc_element = ET.Element('DOC', {'id': doc_id})
    text_element = ET.Element('TEXT')
    root.append(doc_element)
    doc_element.append(text_element)

    prev_seg_end = -2
    for i in range(len(sents)):
        seg_text = delimiter.join(sents[i])
        seg_start_char = prev_seg_end + 2  # '\n' between segs
        seg_end_char = seg_start_char + len(seg_text) - 1
        prev_seg_end = seg_end_char

        seg_id = '%s-%s' % (doc_id, str(i))

        seg_element = ET.Element('SEG', {'id': seg_id,
                                         'start_char': str(seg_start_char),
                                         'end_char': str(seg_end_char)})
        original_text_element = ET.Element('ORIGINAL_TEXT')
        original_text_element.text = seg_text
        seg_element.append(original_text_element)

        pre_tok_end = seg_start_char - len(delimiter) - 1
        for j in range(len(sents[i])):
            token_id = '%s-%s' % (seg_id, str(j))
            tok_text = sents[i][j]
            tok_start_char = pre_tok_end + len(delimiter) + 1
            tok_end_char = tok_start_char + len(tok_text) - 1
            pre_tok_end = tok_end_char

            assert doc_text[tok_start_char:tok_end_char+1] == tok_text

            token_element = ET.Element('TOKEN', {'id': token_id,
                                                 'start_char': str(tok_start_char),
                                                 'end_char': str(tok_end_char)})
            token_element.text = tok_text
            seg_element.append(token_element)

        text_element.append(seg_element)

    return root


def bio2ltf_with_offset(bio_str):
    print("=> generate ltf from bio with offset...")
    bio = parse_bio(bio_str)

    ltf_root = {}
    for d_id, sents in bio.items():
        # sort sent by its start char
        sorted_sents = sorted(sents, key=lambda x: x[0][1])

        root = ET.Element('LCTL_TEXT')
        doc_element = ET.Element('DOC', {'id': d_id})
        text_element = ET.Element('TEXT')
        root.append(doc_element)
        doc_element.append(text_element)

        for i, s in enumerate(sorted_sents):
            s_start = s[0][1]
            s_end = s[-1][2]

            seg_id = '%s-%s' % (d_id, str(i))

            seg_element = ET.Element('SEG',
                                     {'id': seg_id, 'start_char': str(s_start),
                                      'end_char': str(s_end)})

            sent_text = ''
            prev_token_end = -1
            for j, t in enumerate(s):
                # geneate token element
                t_start = t[1]
                t_end = t[2]

                token_id = '%s-%s' % (seg_id, str(j))
                tok_text = t[0]

                token_element = ET.Element('TOKEN', {'id': token_id,
                                                     'start_char': str(
                                                         t_start),
                                                     'end_char': str(
                                                         t_end)})
                token_element.text = tok_text
                seg_element.append(token_element)

                # generate segment text
                if j == 0:
                    delimiter = ''
                else:
                    delimiter = ' '

                sent_text += delimiter * (t[1] - prev_token_end - 1) + t[0]

                assert sent_text[t[1] - s_start:t[2] + 1 - s_start] == t[0], \
                    'bio2rsd token offset error.'

                prev_token_end = t[2]

            # add segment text to element
            original_text_element = ET.Element('ORIGINAL_TEXT')
            original_text_element.text = sent_text
            seg_element.append(original_text_element)

            text_element.append(seg_element)

        ltf_root[d_id] = root

    return ltf_root


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

        sys.stdout.write(
            '%d sentences, %d tokens parsed.\r' % (i, num_token))
        sys.stdout.flush()

    sys.stdout.write('%d docs, %d sentences, %d tokens parsed.\n' %
                     (len(bio), len(bio_str.split('\n\n')), num_token))

    return bio


def write2file(root, ltf_output):
    # pretty print xml
    root_str = ET.tostring(root, 'utf-8')
    f_xml = xml.dom.minidom.parseString(root_str)
    pretty_xml_as_string = f_xml.toprettyxml(encoding="utf-8")
    f = open(ltf_output, 'wb')
    f.write(pretty_xml_as_string)
    f.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('bio_input', type=str,
                        help='input bio path.')
    parser.add_argument('ltf_output', type=str,
                        help='output ltf path.')
    parser.add_argument('-w', '--with_offset', action='store_true',
                        default=False,
                        help='bio with offset')
    parser.add_argument('--delimiter', type=str,
                        help='delimiter used to join words when offset '
                             'is not provided. (no_space if no delimiter)')
    parser.add_argument('-d', '--dir', action='store_true', default=False,
                        help='input and output are directories')

    args = parser.parse_args()

    if not args.delimiter:
        delimiter = ' '
    elif args.delimiter == 'no_space':
        delimiter = ''
    else:
        delimiter = args.delimiter

    bio_files = []
    if args.dir:
        for f in os.listdir(args.bio_input):
            if not f.endswith('.bio'):
                continue
            f_path = os.path.join(args.bio_input, f)
            bio_files.append(f_path)
    else:
        bio_files.append(args.bio_input)

    for f in bio_files:
        bio_str = open(f).read()
        doc_id = f.split('/')[-1].replace('.bio', '')
        root = bio2ltf(bio_str, doc_id=doc_id, with_offset=args.with_offset,
                       delimiter=delimiter)
        if type(root) is dict:
            for d_id, r in root.items():
                ltf_file = os.path.join(args.ltf_output, doc_id + '.ltf.xml')
                write2file(r, ltf_file)
        else:
            write2file(root, os.path.join(args.ltf_output, doc_id + '.ltf.xml'))