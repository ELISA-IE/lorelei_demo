import os
import re
import io
import sys
import codecs
import numpy as np
import theano
import itertools

try:
    import _pickle as cPickle
except ImportError:
    import cPickle

models_path = "./models"
eval_path = os.path.join(os.path.dirname(__file__), "./evaluation")
eval_temp = os.path.join(eval_path, "temp")
eval_script = os.path.join(eval_path, "conlleval")


def get_name(parameters):
    """
    Generate a model name from its parameters.
    """
    l = []
    for k, v in parameters.items():
        if type(v) is str and "/" in v:
            v = v[::-1][:v[::-1].index('/')][::-1]
            if len(v) > 10:
                v = 'long_path'
            l.append((k, v))
        elif type(v) is list:
            l.append((k, 'long_path'))
        else:
            l.append((k, v))
    name = ",".join(["%s=%s" % (k, str(v).replace(',', '')) for k, v in l])
    return "".join(i for i in name if i not in "\/:*?<>|")


def set_values(name, param, pretrained):
    """
    Initialize a network parameter with pretrained values.
    We check that sizes are compatible.
    """
    param_value = param.get_value()
    if pretrained.size != param_value.size:
        raise Exception(
            "Size mismatch for parameter %s. Expected %i, found %i."
            % (name, param_value.size, pretrained.size)
        )
    param.set_value(np.reshape(
        pretrained, param_value.shape
    ).astype(np.float32))


def shared(shape, name):
    """
    Create a shared object of a numpy array.
    """
    if len(shape) == 1:
        value = np.zeros(shape)  # bias are initialized with zeros
    else:
        drange = np.sqrt(6. / (np.sum(shape)))
        value = drange * np.random.uniform(low=-1.0, high=1.0, size=shape)
    return theano.shared(value=value.astype(theano.config.floatX), name=name)


def create_dico(item_list):
    """
    Create a dictionary of items from a list of list of items.
    """
    assert type(item_list) is list
    dico = {}
    for items in item_list:
        for item in items:
            if item not in dico:
                dico[item] = 1
            else:
                dico[item] += 1
    return dico


def create_mapping(dico):
    """
    Create a mapping (item to ID / ID to item) from a dictionary.
    Items are ordered by decreasing frequency.
    """
    sorted_items = sorted(dico.items(), key=lambda x: (-x[1], x[0]))
    id_to_item = {i: v[0] for i, v in enumerate(sorted_items)}
    item_to_id = {v: k for k, v in id_to_item.items()}
    return item_to_id, id_to_item


def zero_digits(s):
    """
    Replace every digit in a string by a zero.
    """
    return re.sub('\d', '0', s)


def iob2(tags):
    """
    Check that tags have a valid IOB format.
    Tags in IOB1 format are converted to IOB2.
    """
    for i, tag in enumerate(tags):
        if tag == 'O':
            continue
        split = tag.split('-')
        if len(split) != 2 or split[0] not in ['I', 'B']:
            return False
        if split[0] == 'B':
            continue
        elif i == 0 or tags[i - 1] == 'O':  # conversion IOB1 to IOB2
            tags[i] = 'B' + tag[1:]
        elif tags[i - 1][1:] == tag[1:]:
            continue
        else:  # conversion IOB1 to IOB2
            tags[i] = 'B' + tag[1:]
    return True


def iob_iobes(tags):
    """
    IOB -> IOBES
    """
    new_tags = []
    for i, tag in enumerate(tags):
        if tag == 'O':
            new_tags.append(tag)
        elif tag.split('-')[0] == 'B':
            if i + 1 != len(tags) and \
                            tags[i + 1].split('-')[0] == 'I':
                new_tags.append(tag)
            else:
                new_tags.append(tag.replace('B-', 'S-'))
        elif tag.split('-')[0] == 'I':
            if i + 1 < len(tags) and \
                            tags[i + 1].split('-')[0] == 'I':
                new_tags.append(tag)
            else:
                new_tags.append(tag.replace('I-', 'E-'))
        else:
            raise Exception('Invalid IOB format!')
    return new_tags


def iobes_iob(tags):
    """
    IOBES -> IOB
    """
    new_tags = []
    for i, tag in enumerate(tags):
        if tag.split('-')[0] == 'B':
            new_tags.append(tag)
        elif tag.split('-')[0] == 'I':
            new_tags.append(tag)
        elif tag.split('-')[0] == 'S':
            new_tags.append(tag.replace('S-', 'B-'))
        elif tag.split('-')[0] == 'E':
            new_tags.append(tag.replace('E-', 'I-'))
        elif tag.split('-')[0] == 'O':
            new_tags.append(tag)
        else:
            raise Exception('Invalid format!')
    return new_tags


def insert_singletons(words, singletons, p=0.5):
    """
    Replace singletons by the unknown word with a probability p.
    """
    new_words = []
    for word in words:
        if word in singletons and np.random.uniform() < p:
            new_words.append(0)
        else:
            new_words.append(word)
    return new_words


def pad_word_chars(words):
    """
    Pad the characters of the words in a sentence.
    Input:
        - list of lists of ints (list of words, a word being a list of char indexes)
    Output:
        - padded list of lists of ints
        - padded list of lists of ints (where chars are reversed)
        - list of ints corresponding to the index of the last character of each word
    """
    # max_length = max([len(word) for word in words])
    # char_for = []
    # char_rev = []
    # char_pos = []
    # for word in words:
    #     padding = [0] * (max_length - len(word))
    #     char_for.append(word + padding)
    #     char_rev.append(word[::-1] + padding)
    #     char_pos.append(len(word) - 1)
    # return char_for, char_rev, char_pos

    max_length = 25
    char_for = []
    char_rev = []
    char_pos = []
    for word in words:
        if len(word) >= max_length:
            # print("exceed the max length ... ", len(word))
            word = word[:max_length]
            char_for.append(word)
            char_rev.append(word[::-1])
            char_pos.append(len(word) - 1)
        else:
            padding_left = [0]
            padding = [0] * (max_length - 1 - len(word))
            char_for.append(padding_left + word + padding)
            char_rev.append(padding_left + word[::-1] + padding)
            char_pos.append(len(word))
    return char_for, char_rev, char_pos


def create_input(data, parameters, add_label, singletons=None):
    """
    Take sentence data and return an input for
    the training or the evaluation function.
    """
    words = data['words']
    stems = data['stems']
    chars = data['chars']
    if singletons is not None:
        words = insert_singletons(words, singletons)
        stems = insert_singletons(stems, singletons)
    if parameters['cap_dim']:
        caps = data['caps']
    char_for, char_rev, char_pos = pad_word_chars(chars)
    input = []
    if parameters['word_dim']:
        input.append(words)
    if stems:
        input.append(stems)
    if parameters['char_dim']:
        input.append(char_for)
        if parameters['char_bidirect']:
            input.append(char_rev)
        input.append(char_pos)
    if parameters['cap_dim']:
        input.append(caps)

    # boliang: add expectation features into input
    if parameters['feat_dim']:
        feat_len = len(data['feats'][0])  # get expectation feature length
        for i in range(feat_len):
            input_feats = [token_feats[i] for token_feats in data['feats']]
            input.append(input_feats)

    # boliang: add numeric features into input
    # if parameters['numeric_feat_dim']:
    #     input.append(data['numeric_feats'])

    if add_label:
        input.append(data['tags'])
    return input


def evaluate(parameters, f_eval, raw_sentences, parsed_sentences,
             id_to_tag, dictionary_tags, eval_out_dir=None):
    """
    Evaluate current model using CoNLL script.
    """

    n_tags = len(id_to_tag)
    predictions = []
    count = np.zeros((n_tags, n_tags), dtype=np.int32)

    for raw_sentence, data in zip(raw_sentences, parsed_sentences):
        input = create_input(data, parameters, False)
        if parameters['crf']:
            y_preds = np.array(f_eval(*input))[1:-1]
        else:
            y_preds = f_eval(*input).argmax(axis=1)
        y_reals = np.array(data['tags']).astype(np.int32)
        assert len(y_preds) == len(y_reals)
        p_tags = [id_to_tag[y_pred] for y_pred in y_preds]
        r_tags = [id_to_tag[y_real] for y_real in y_reals]
        if parameters['tag_scheme'] == 'iobes':
            p_tags = iobes_iob(p_tags)
            r_tags = iobes_iob(r_tags)
        for i, (y_pred, y_real) in enumerate(zip(y_preds, y_reals)):
            new_line = " ".join(raw_sentence[i][:-1] + [r_tags[i], p_tags[i]])
            predictions.append(new_line)
            count[y_real, y_pred] += 1
        predictions.append("")

    # Write predictions to disk and run CoNLL script externally
    eval_id = np.random.randint(1000000, 2000000)
    if eval_out_dir:
        eval_temp = eval_out_dir
    output_path = os.path.join(eval_temp, "eval.%i.output" % eval_id)
    scores_path = os.path.join(eval_temp, "eval.%i.scores" % eval_id)
    with codecs.open(output_path, 'w', 'utf8') as f:
        f.write("\n".join(predictions))
    os.system("%s < %s > %s" % (eval_script, output_path, scores_path))

    # CoNLL evaluation results
    eval_lines = [l.rstrip() for l in codecs.open(scores_path, 'r', 'utf8')]
    for line in eval_lines:
        print(line)

    # Remove temp files
    # os.remove(output_path)
    # os.remove(scores_path)

    # Confusion matrix with accuracy for each tag
    # print(("{: >2}{: >7}{: >7}%s{: >9}" % ("{: >7}" * n_tags)).format(
    #     "ID", "NE", "Total",
    #     *([id_to_tag[i] for i in range(n_tags)] + ["Percent"])
    # ))
    # for i in range(n_tags):
    #     print(("{: >2}{: >7}{: >7}%s{: >9}" % ("{: >7}" * n_tags)).format(
    #         str(i), id_to_tag[i], str(count[i].sum()),
    #         *([count[i][j] for j in range(n_tags)] +
    #           ["%.3f" % (count[i][i] * 100. / max(1, count[i].sum()))])
    #     ))

    # Global accuracy
    print("%i/%i (%.5f%%)" % (
        count.trace(), count.sum(), 100. * count.trace() / max(1, count.sum())
    ))

    # F1 on all entities
    # print(eval_lines)

    # find all float numbers in string
    acc, precision, recall, f1 = re.findall("\d+\.\d+", eval_lines[1])

    return float(f1), float(acc)


########################################################################################################################
# temporal script below
#
def load_exp_feats(fp):
    bio_feats_fp = fp
    res = []
    for sent in io.open(bio_feats_fp, 'r', -1, 'utf-8').read().split('\n\n'):
        sent_feats = []
        for line in sent.splitlines():
            feats = line.split('\t')[1:]
            sent_feats.append(feats)
        res.append(sent_feats)

    return res


if __name__ == "__main__":
    # dump train/dev/test exp feats for training
    train_exp_feats = load_exp_feats('train.bio.feats')
    dev_exp_feats = load_exp_feats('dev.bio.feats')
    test_exp_feats = load_exp_feats('test.bio.feats')

    with open('exp_feats.pkl', 'wb') as f:
        exp_feats = {
            'train_exp_feats': train_exp_feats,
            'dev_exp_feats': dev_exp_feats,
            'test_exp_feats': test_exp_feats,
        }
        cPickle.dump(exp_feats, f)

    # dump only test exp feats for testing
    test_exp_feats = load_exp_feats('test.bio.feats')
    cPickle.dump(test_exp_feats, open('test_exp_feats.pkl', 'wb'))


class Tee(object):
    def __init__(self, *files):
        self.files = files

    def write(self, obj):
        for f in self.files:
            f.write(obj)
            f.flush() # If you want the output to be visible immediately

    def flush(self) :
        for f in self.files:
            f.flush()