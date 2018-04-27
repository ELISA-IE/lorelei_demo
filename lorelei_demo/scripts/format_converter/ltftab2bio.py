import argparse
import codecs
import xml
import xml.etree.ElementTree as ET
import os


def ltftab2bio(ltf_root, tab_str):
    res = []
    doc_tokens, doc_text, doc_id = load_ltf(ltf_root)
    labels = parse_label(tab_str)

    # check label offset
    for l in labels:
        try:
            mention, start_char, end_char, mention_type, kbid = l
            assert doc_text[start_char:end_char+1] == mention, \
                "mention offset error in %s %s" % (doc_id, l)
        except AssertionError as e:
            counter['mention_offset_error'] += 1
            print(e)

    # create annotation mapping table
    label_offset_mapping = dict()
    for l in labels:
        start_char = l[1]
        end_char = l[2]
        for i in range(start_char, end_char + 1):
            label_offset_mapping[i] = l

    #
    # add label to bio
    #
    b_tags = set()
    for i, sent_tokens in enumerate(doc_tokens):
        sent_res = []

        retok_sent_tokens = []

        # re-tokenize token based on labels in tab
        for token in sent_tokens:
            t_text = token[0]
            t_start_char = int(token[1])
            t_end_char = int(token[2])

            char_labels = []
            for t_char in range(t_start_char, t_end_char + 1):
                if t_char not in label_offset_mapping:
                    char_labels.append('O')
                if t_char in label_offset_mapping:
                    char_labels.append(label_offset_mapping[t_char])

            char_index = []
            current_char_index = []
            current_label = None
            for j, char_label in enumerate(char_labels):
                if char_label != current_label:
                    if current_char_index:
                        char_index.append(current_char_index)
                    current_char_index = [j]
                    current_label = char_label
                elif char_label == current_label:
                    current_char_index.append(j)
                if j == len(char_labels)-1:
                    char_index.append(current_char_index)

            retok_tokens = []
            for index in char_index:
                start = t_start_char + index[0]
                end = t_start_char + index[-1]
                text = t_text[start-t_start_char:end-t_start_char+1]
                assert doc_text[start:end+1] == text, 'retok token offset error'
                retok_tokens.append((text, start, end))

            assert ''.join([item[0] for item in retok_tokens]) == t_text, \
                'join of retok tokens not match original text in %s-%d' % \
                (doc_id, i)

            retok_sent_tokens += retok_tokens

            if len(char_index) > 1:
                counter['num_retok_token'] += 1

        # add label to bio
        for j, token in enumerate(retok_sent_tokens):
            t_text = token[0]
            t_start_char = int(token[1])
            t_end_char = int(token[2])

            # get token bio tag
            if t_start_char in label_offset_mapping.keys():
                entity_type = label_offset_mapping[t_start_char][3]
                kbid = label_offset_mapping[t_start_char][4]
                if t_start_char == label_offset_mapping[t_start_char][1] or j == 0:
                    tag = '%s-%s' % ('B', entity_type)
                    b_tags.add(t_start_char)
                else:
                    tag = '%s-%s' % ('I', entity_type)
            else:
                tag = 'O'
                kbid = 'O'
            sent_res.append(' '.join([t_text,
                                      '%s:%d-%d' % (doc_id,
                                                    t_start_char,
                                                    t_end_char),
                                      kbid,
                                      tag]))

        res.append('\n'.join(sent_res))

    if len(b_tags) != len(labels):
        print('number of B tags and number of labels do not match in %s (%d/%d)'
              % (doc_id, len(b_tags), len(labels)))
        for l in labels:
            start = l[1]
            if start not in b_tags:
                print('  %s %d-%d' % (l[0], l[1], l[2]))

    counter['num_b_tag'] += len(b_tags)

    return '\n\n'.join(res)


def write2file(bio_str, bio_file):
    with codecs.open(bio_file, 'w', 'utf-8') as f:
        f.write(bio_str+'\n')


def load_ltf(ltf_root):
    doc_tokens = []
    doc_id = ltf_root.find('DOC').get('id')
    doc_text = ''
    prev_seg_end = -1
    for seg in ltf_root.find('DOC').find('TEXT').findall('SEG'):
        sent_tokens = []
        seg_text = seg.find('ORIGINAL_TEXT').text
        # ignore empty sentence
        if not seg_text:
            continue
        seg_start = int(seg.get('start_char'))
        seg_end = int(seg.get('end_char'))
        seg_id = seg.get('id')

        doc_text += '\n' * (seg_start - prev_seg_end - 1) + seg_text
        prev_seg_end = seg_end
        assert doc_text[seg_start:seg_end+1] == seg_text, \
            'seg offset error in %s-%s' % (doc_id, seg_id)

        for token in seg.findall('TOKEN'):
            token_id = token.get('id')
            token_text = token.text
            if not token_text.strip():
                continue
            start_char = int(token.get('start_char'))
            end_char = int(token.get('end_char'))

            assert doc_text[start_char:end_char + 1] == token_text, \
                "token offset assertion error in %s-%s" % (doc_id, token_id)

            sent_tokens.append((token_text, start_char, end_char))
        doc_tokens.append(sent_tokens)

    return doc_tokens, doc_text, doc_id


def parse_label(tab_str):
    labels = []
    if not tab_str:
        return labels

    num_overlap_label = 0
    doc_id = ''
    char_offset = set()
    for line in tab_str.splitlines():
        try:
            line = line.strip()
            if not line:
                continue
            line = line.split('\t')
            mention = line[2]
            doc_id, offset = line[3].split(':')
            start_char, end_char = offset.split("-")
            start_char, end_char = int(start_char), int(end_char)
            mention_type = line[5]
            kbid = line[4]

            # check overlap labels
            overlapped_chars = char_offset.intersection(
                set(range(start_char, end_char + 1))
            )

            # pick the longest name if there are overlapped labels.
            if overlapped_chars:
                num_overlap_label += 1
                for i, l in enumerate(labels):
                    if not set(range(l[1], l[2]+1)).intersection(overlapped_chars):
                        continue
                    if l[2]-l[1]+1 < end_char-start_char+1:
                        tmp = (mention, start_char, end_char, mention_type, kbid)
                        labels[i] = tmp
                        char_offset = char_offset.union(set(range(start_char,
                                                                  end_char+1)))
                continue
            else:
                char_offset = char_offset.union(set(range(start_char,
                                                          end_char+1)))

            labels.append((mention, start_char, end_char, mention_type, kbid))

            counter['num_labels'] += 1
        except Exception as e:
            print(e, "; parse label error in %s" % line)

    if num_overlap_label:
        print('%d overlapped labels found in %s' % (num_overlap_label, doc_id))

    # make sure each entry is unique
    labels = set(labels)

    # check overlap labels again
    assert len(set([l[1] for l in labels])) == len(labels), \
        'overlap name found in parsed names.'

    return labels


counter = dict()
counter['num_labels'] = 0
counter['num_b_tag'] = 0
counter['num_retok_token'] = 0
counter['mention_offset_error'] = 0
counter['num_doc_added'] = 0
counter['num_ltf_files'] = 0
counter['num_tab_files'] = 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("ltf")
    parser.add_argument("tab")
    parser.add_argument("bio_file")
    parser.add_argument("-d", action="store_true", default=False,
                        help="process directory")

    args = parser.parse_args()

    if args.d:
        combined_bio = []
        for fn in os.listdir(args.ltf):
            try:
                if not fn.endswith(".ltf.xml"):
                    continue

                ltf_file = os.path.join(args.ltf, fn)
                tab_file = os.path.join(args.tab,
                                        fn.replace(".ltf.xml", '.tab'))
                if not os.path.exists(ltf_file) or not os.path.exists(tab_file):
                    continue

                ltf_root = ET.parse(ltf_file)
                tab_str = codecs.open(tab_file, 'r', 'utf-8').read()

                bio_str = ltftab2bio(ltf_root, tab_str)

                combined_bio.append(bio_str)

                counter['num_doc_added'] += 1
            except AssertionError as e:
                print('ERROR:', ltf_file, e)
            except xml.etree.ElementTree.ParseError as e:
                print('ERROR: ', ltf_file, e)

        write2file('\n\n'.join(combined_bio), args.bio_file)

        counter['num_ltf_files'] = len([fn for fn in os.listdir(args.ltf)
                                        if fn.endswith('.ltf.xml')])
        counter['num_tab_files'] = len([fn for fn in os.listdir(args.tab)
                                        if fn.endswith('.tab')])

    else:
        ltf_root = ET.parse(args.ltf)
        tab_str = codecs.open(args.tab, 'r', 'utf-8').read()

        bio_str = ltftab2bio(ltf_root, tab_str)

        write2file(bio_str, args.bio_file)

        counter['num_doc_added'] = 1
        counter['num_ltf_files'] = 1
        counter['num_tab_files'] = 1

    print('\n=> ltftab2bio stats:')
    print('%d ltf files parsed.' % counter['num_ltf_files'])
    print('%d tab files parsed.' % counter['num_tab_files'])
    print('%d documents added to bio.' % counter['num_doc_added'])
    print('%d names parsed in tab file.' % counter['num_labels'])
    print('%d B tags added to bio.' % counter['num_b_tag'])
    print('%d tokens re-tokenized.' % counter['num_retok_token'])
    print('%d mention offset errors.' % counter['mention_offset_error'])
