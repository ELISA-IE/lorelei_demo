import os
import codecs
import itertools

from fb_intern import fb_intern_root
from fb_intern.utils.ie_model.io_ import parse_bio


class FeatureGenerator(object):
    def __init__(self, parameters=None):
        if not parameters:
            self.parameters = dict()
        else:
            self.parameters = parameters
        self.gaz = dict()
        self.documents = []

    def load_fb_dict(self, fb_dict_file):
        print('=> loading fb dictionary...')
        res = []
        res_lower = []
        for line in codecs.open(fb_dict_file, 'r', 'utf-8'):
            line = line.strip()
            if not line:
                continue

            mention = line.split('\t')[0]

            res.append(mention)
            res_lower.append(mention.lower())

        res = set(res)
        res_lower = set(res_lower)

        self.gaz['fb_entity'] = res
        self.gaz['fb_entity_lower'] = res_lower

    def load_bio(self, bio_file):
        print('=> loading bio file')
        self.documents = parse_bio(codecs.open(bio_file, 'r', 'utf-8').read(), offset_column=1, kb_id_column=2, pred_tag=False)

    def generate_features(self):
        if not self.documents:
            raise ValueError('not Document object found.')

        print('=>generating features')
        for doc in self.documents:
            for sent in doc.sentences:
                for token in sent.tokens:
                    #
                    # fb mention dictionary features (with case)
                    #
                    feat = self.feat_fbdict(token, self.gaz['fb_entity'])
                    token.external_features.append(feat)

                    #
                    # fb mention dictionary features (all lower case)
                    #
                    feat = self.feat_fbdict(token, self.gaz['fb_entity_lower'], lower=True)
                    token.external_features.append(feat)

                    #
                    # # feature
                    #
                    feat = self.feat_hashtag(token)
                    token.external_features.append(feat)

                    #
                    # @ feature
                    #
                    feat = self.feat_at(token)
                    token.external_features.append(feat)

    def output_documents(self, out_file, output_params=True):
        if output_params:
            param = ','.join(['%s=%s' % (key, value) for key, value in self.parameters.items()])
            out_file = out_file.replace('.bio', '.%s.bio' % param)
        res = '\n\n'.join([doc.to_bio() for doc in self.documents])
        with codecs.open(out_file, 'w', 'utf-8') as f:
            f.write(res)

    #
    # functions to generate features for single token
    #
    def feat_fbdict(self, token, fb_dict, stemming=False, lower=False):
        # if len(token.text) < 5:
        #     return 'O'

        context_window = 2
        token_index = token.index

        if token_index - context_window < 0:
            context_tokens = token.sent.tokens[0:token_index + context_window + 1]
        else:
            context_tokens = token.sent.tokens[token_index - context_window:token_index + context_window + 1]

        valid_context_tokens = []

        if len(token.text) >= 5:
            min_context_len = 1
        else:
            min_context_len = 2

        # min_context_len = 2

        for i in range(min_context_len, len(context_tokens) + 1):
            combinations = list(itertools.combinations(context_tokens, i))
            for c in combinations:
                # make sure the combination is a sublist and contains the token.
                if token in c and \
                        any(list(c) == context_tokens[j:j+len(c)] for j in range(len(context_tokens))):
                    valid_context_tokens.append(c)

        contexts = []
        for c in valid_context_tokens:
            contexts.append(' '.join([t.text for t in c]))

        # sort context by length
        sorted_contexts = sorted(contexts, key=len, reverse=True)

        if lower:
            for c in sorted_contexts:
                if c.lower() in fb_dict:
                    if c.lower().strip().startswith(token.text.lower()):
                        return 'B'
                    else:
                        return 'I'
        else:
            for c in sorted_contexts:
                if c in fb_dict:
                    if c.strip().startswith(token.text):
                        return 'B'
                    else:
                        return 'I'

        return 'O'

    def feat_hashtag(self, token):
        if token.prev and token.prev.text == '#':
            return '#_1'

        return '#_0'

    def feat_at(self, token):
        if token.prev and token.prev.text == '@':
            return '@_1'

        return '@_0'


if __name__ == "__main__":
    fb_dict_file = os.path.join(fb_intern_root, 'data/gaz/ep_file')

    # bio_file = os.path.join(fb_intern_root, 'data/ner/v4/bio/v4_test_sample.bio')
    # bio_file = os.path.join(fb_intern_root, 'data/ner/v4/bio/v4_test.bio')
    # bio_file = os.path.join(fb_intern_root, 'data/ner/v4/bio/v4_train.bio')
    bio_file = os.path.join(fb_intern_root, 'data/ner/v2/v2_test_cleaned.bio')
    # bio_file = os.path.join(fb_intern_root, 'data/ner/v5/bio/v5_test.bio')

    feature_generator = FeatureGenerator()
    feature_generator.load_bio(bio_file)
    feature_generator.load_fb_dict(fb_dict_file)
    feature_generator.generate_features()

    out_file = bio_file.replace('.bio', '_feat.bio')
    feature_generator.output_documents(out_file, output_params=False)

