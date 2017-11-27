import argparse
import codecs
import sys


def bio2tab(bio_str):
    print('=> bio2tab...')
    bio_sents = bio_str.split('\n\n')

    tab_result = []
    current_doc_id = ''
    label_index = 0
    b_tag_count = 0
    num_tokens = 0
    num_sents = 0
    doc_set = set()
    for sent in bio_sents:
        sent = sent.strip()
        if not sent:
            continue
        num_sents += 1
        sent_mentions = []
        tokens = sent.splitlines()
        current_mention = []
        for i, t in enumerate(tokens):
            num_tokens += 1
            t_split = t.split(' ')
            text = t_split[0]
            doc_id, offset = t_split[1].split(':')
            start_char, end_char = offset.split('-')
            pred = t_split[-1].split('-')
            if len(pred) == 2:
                pred_tag, pred_type = pred
            else:
                pred_tag, pred_type = ('O', None)

            if pred_tag == 'O':
                if current_mention:
                    sent_mentions.append(current_mention)
                    current_mention = []
            elif pred_tag == 'B':
                b_tag_count += 1
                if current_mention:
                    sent_mentions.append(current_mention)
                current_mention = [(text, doc_id, start_char,
                                    end_char, pred_type)]
            elif pred_tag == 'I' and current_mention:
                current_mention.append((text, doc_id, start_char,
                                        end_char, pred_type))
            if i == len(tokens)-1 and current_mention:
                sent_mentions.append(current_mention)

        for i, mention in enumerate(sent_mentions):
            mention_text = ''
            mention_type = ''
            mention_start_char = 0
            mention_end_char = 0
            for j, token in enumerate(mention):
                text, doc_id, start_char, end_char, pred_type = token
                if j == 0:
                    mention_text += text
                    mention_start_char = int(start_char)
                else:
                    mention_text += ' ' * (int(start_char) -
                                           int(mention_end_char)
                                           - 1) + text
                mention_end_char = int(end_char)
                mention_type = pred_type

            assert len(mention_text) == (mention_end_char -
                                         mention_start_char) + 1

            if doc_id != current_doc_id:
                current_doc_id = doc_id
                label_index = 0

            tab_line = '\t'.join(['bio2tab',
                                  '%s-%d' % (doc_id, label_index),
                                  mention_text,
                                  '%s:%s-%s' % (doc_id,
                                                mention_start_char,
                                                mention_end_char),
                                  'NIL',
                                  mention_type,
                                  'NAM',
                                  '1.0'])
            tab_result.append(tab_line)

            label_index += 1

        sys.stdout.write('%d docs, %d sentences, %d tokens processed.\r' %
                         (len(doc_set), num_sents, num_tokens))
        sys.stdout.flush()

    print('%d docs, %d sentences, %d tokens processed in total.' %
          (len(doc_set), num_sents, num_tokens))

    assert b_tag_count == len(tab_result), \
        'number of B tag in bio and tab entries does not match'

    print('Validation passed: the number of B tag in bio matches tab entries.')

    tab_str = '\n'.join(tab_result)+'\n'

    return tab_str


def write2file(tab_str, tab_file):
    with codecs.open(tab_file, 'w', 'utf-8') as f:
        f.write(tab_str)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('bio_file', type=str,
                        help='input bio file path')
    parser.add_argument('tab_file', type=str,
                        help='output tab file path')

    args = parser.parse_args()

    bio_str = codecs.open(args.bio_file, 'r', 'utf-8').read()

    tab_str = bio2tab(bio_str)

    write2file(tab_str, args.tab_file)



