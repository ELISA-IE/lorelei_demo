import os
import codecs
import itertools

from fb_intern import fb_intern_root
from fb_intern.utils.ie_model.io_ import parse_bio


def load_fb_dict():
    fb_dict_file = os.path.join(fb_intern_root, 'data/gaz/ep_file')

    res = []
    for line in codecs.open(fb_dict_file, 'r', 'utf-8'):
        line = line.strip()
        if not line:
            continue

        mention = line.split('\t')[0]

        res.append(mention)

    return set(res)


def generate_features(bio_file):
    documents = parse_bio(codecs.open(bio_file, 'r', 'utf-8').read(), offset_column=1, kb_id_column=2, pred_tag=False)

    fb_dict = load_fb_dict()

    for doc in documents:
        for sent in doc.sentences:
            for token in sent.tokens:
                #
                # fb mention dictionary features
                #
                feat = feat_fbdict(token, fb_dict)
                token.external_features.append(feat)

                #
                # # feature
                #
                feat = feat_hashtag(token)
                token.external_features.append(feat)

                #
                # @ feature
                #
                feat = feat_at(token)
                token.external_features.append(feat)

    res = '\n\n'.join([doc.to_bio() for doc in documents])

    return res


def feat_fbdict(token, fb_dict, stemming=False):
    # if len(token.text) < 5:
    #     return 'O'

    context_window = 2
    token_index = token.index

    if token_index - context_window < 0:
        context_tokens = token.sent.tokens[0:token_index + context_window + 1]
    else:
        context_tokens = token.sent.tokens[token_index - context_window:token_index + context_window + 1]

    valid_context_tokens = []

    # if len(token.text) >= 5:
    #     start = 2
    # else:
    #     start = 2

    min_token_len = 2

    for i in range(min_token_len, len(context_tokens) + 1):
        combinations = list(itertools.combinations(context_tokens, i))
        for c in combinations:
            # make sure the combination is a sublist and contains the token.
            if token in c and \
                    any(c == context_tokens[i:i+len(c)] for i in range(len(context_tokens))):
                valid_context_tokens.append(c)

    contexts = []
    for c in valid_context_tokens:
        contexts.append(' '.join([t.text for t in c]))

    # sort context by length
    sorted_contexts = sorted(contexts, key=len, reverse=True)

    for c in sorted_contexts:
        if c in fb_dict:
            if c.strip().startswith(token.text):
                return 'B'
            else:
                return 'I'

    return 'O'


def feat_hashtag(token):
    if token.prev and token.prev.text == '#':
        return '#_1'

    return '#_0'


def feat_at(token):
    if token.prev and token.prev.text == '@':
        return '@_1'

    return '@_0'


if __name__ == "__main__":
    # bio_file = os.path.join(fb_intern_root, 'data/ner/v4/v4_test_tok_seg.bio')
    # bio_file = os.path.join(fb_intern_root, 'data/ner/v4/v4_train_tok_seg.bio')
    # bio_file = os.path.join(fb_intern_root, 'data/ner/v2/v2_test_cleaned.bio')
    bio_file = os.path.join(fb_intern_root, 'data/ner/v5/bio/v5_test.bio')

    bio_with_feat = generate_features(bio_file)

    out_file = bio_file.replace('.bio', '_feat.bio')

    with codecs.open(out_file, 'w', 'utf-8') as f:
        f.write(bio_with_feat)


