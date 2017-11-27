import os
import re
import numpy as np
import scipy.io
import theano
import theano.tensor as T
import codecs

try:
    import _pickle as cPickle
except ImportError:
    import cPickle
import shutil
from loader import load_embedding
from utils import shared, set_values, get_name
from nn import HiddenLayer, EmbeddingLayer, DropoutLayer, LSTM, forward, MultiLeNetConvLayer
from optimization import Optimization


class Model(object):
    """
    Network architecture.
    """
    def __init__(self, parameters=None, models_path=None, model_path=None):
        """
        Initialize the model. We either provide the parameters and a path where
        we store the models, or the location of a trained model.
        """
        if model_path is None:
            assert parameters and models_path
            # Create a name based on the parameters
            self.parameters = parameters
            self.name = get_name(parameters)
            self.name = ','.join(self.name.split(',')[6:])
            # Model location
            model_path = os.path.join(models_path, self.name)
            self.model_path = model_path
            self.eval_out_dir = os.path.join(self.model_path, 'eval_output')
            self.parameters_path = os.path.join(model_path, 'parameters.pkl')
            self.mappings_path = os.path.join(model_path, 'mappings.pkl')
            # Create directory for the model if it does not exist
            if not os.path.exists(self.model_path):
                os.makedirs(self.model_path)
            if os.path.exists(self.eval_out_dir):
                shutil.rmtree(self.eval_out_dir)
                os.mkdir(self.eval_out_dir)
            # Save the parameters to disk
            with open(self.parameters_path, 'wb') as f:
                self.parameters = cPickle.dump(parameters, f)
        else:
            assert parameters is None and models_path is None
            # Model location
            self.model_path = model_path
            self.parameters_path = os.path.join(model_path, 'parameters.pkl')
            self.mappings_path = os.path.join(model_path, 'mappings.pkl')
            # Load the parameters and the mappings from disk
            with open(self.parameters_path, 'rb') as f:
                self.parameters = cPickle.load(f)
            self.reload_mappings()
        self.components = {}

    def save_mappings(self, id_to_word, id_to_char, id_to_tag, id_to_feat_list):
        """
        We need to save the mappings if we want to use the model later.
        """
        self.id_to_word = id_to_word
        self.id_to_char = id_to_char
        self.id_to_tag = id_to_tag
        self.id_to_feat_list = id_to_feat_list  # boliang
        with open(self.mappings_path, 'wb') as f:
            mappings = {
                'id_to_word': self.id_to_word,
                'id_to_char': self.id_to_char,
                'id_to_tag': self.id_to_tag,
                'id_to_feat_list': self.id_to_feat_list  # boliang
            }
            cPickle.dump(mappings, f)

    def reload_mappings(self):
        """
        Load mappings from disk.
        """
        with open(self.mappings_path, 'rb') as f:
            mappings = cPickle.load(f)

        # model compatible checking
        if 'id_to_feat_list' not in mappings:
            mappings['id_to_feat_list'] = dict()

        self.id_to_word = mappings['id_to_word']
        self.id_to_char = mappings['id_to_char']
        self.id_to_tag = mappings['id_to_tag']
        self.id_to_feat_list = mappings['id_to_feat_list']  # boliang

    def save_exp_feats(self, train_exp_feats, dev_exp_feats, test_exp_feats):
        """
        Boliang
        Save expectation features of train, dev and test set to disk.
        """
        with open(os.path.join(self.model_path, 'exp_feats.pkl'), 'wb') as f:
            exp_feats = {
                'train_exp_feats': train_exp_feats,
                'dev_exp_feats': dev_exp_feats,
                'test_exp_feats': test_exp_feats,
            }
            cPickle.dump(exp_feats, f)

    def save_numeric_feats(self, train_numeric_feats, dev_numeric_feats, test_numeric_feats):
        """
        Boliang
        Save numeric features of train, dev and test set to disk.
        """
        with open(os.path.join(self.model_path, 'numeric_feats.pkl'), 'wb') as f:
            numeric_feats = {
                'train_numeric_feats': train_numeric_feats,
                'dev_numeric_feats': dev_numeric_feats,
                'test_numeric_feats': test_numeric_feats,
            }
            cPickle.dump(numeric_feats, f)

    def save_additional_feats(self, train_additional_feats, dev_additional_feats, test_additional_feats):
        """
        Boliang
        Save additional features of train, dev and test set to disk.
        """
        with open(os.path.join(self.model_path, 'additional_feats.pkl'), 'wb') as f:
            additional_feats = {
                'train_additional_feats': train_additional_feats,
                'dev_additional_feats': dev_additional_feats,
                'test_additional_feats': test_additional_feats,
            }
            cPickle.dump(additional_feats, f)

    def reload_exp_feats(self):
        """
        Boliang
        Reload expectation features of train, dev and test set from disk.
        """
        with open(os.path.join(self.model_path, 'exp_feats.pkl'), 'rb') as f:
            exp_feats = cPickle.load(f)
        return exp_feats['train_exp_feats'], exp_feats['dev_exp_feats'], exp_feats['test_exp_feats']

    def reload_numeric_feats(self):
        """
        Boliang
        Reload numeric features of train, dev and test set from disk.
        """
        with open(os.path.join(self.model_path, 'numeric_feats.pkl'), 'rb') as f:
            numeric_feats = cPickle.load(f)
        return numeric_feats['train_numeric_feats'], numeric_feats['dev_numeric_feats'], \
               numeric_feats['test_numeric_feats']

    def add_component(self, param):
        """
        Add a new parameter to the network.
        """
        if param.name in self.components:
            raise Exception('The network already has a parameter "%s"!'
                            % param.name)
        self.components[param.name] = param

    def save(self):
        """
        Write components values to disk.
        """
        for name, param in self.components.items():
            param_path = os.path.join(self.model_path, "%s.mat" % name)
            if hasattr(param, 'params'):
                param_values = {p.name: p.get_value() for p in param.params}
            else:
                param_values = {name: param.get_value()}
            scipy.io.savemat(param_path, param_values)

    def reload(self):
        """
        Load components values from disk.
        """
        for name, param in self.components.items():
            param_path = os.path.join(self.model_path, "%s.mat" % name)
            param_values = scipy.io.loadmat(param_path)
            if hasattr(param, 'params'):
                for p in param.params:
                    set_values(p.name, p, param_values[p.name])
            else:
                set_values(name, param, param_values[name])

    def build(self,
              dropout,
              char_dim,
              char_lstm_dim,
              char_bidirect,
              word_dim,
              word_lstm_dim,
              word_bidirect,
              lr_method,
              pre_emb,
              crf,
              cap_dim,
              conv,
              upenn_stem,
              ying_stem,
              feat_dim,
              comb_method,
              training=True,
              **kwargs
              ):
        """
        Build the network.
        """
        # Training parameters
        n_words = len(self.id_to_word)
        n_chars = len(self.id_to_char)
        n_tags = len(self.id_to_tag)

        # Number of capitalization features
        if cap_dim:
            n_cap = 4

        # boliang: list of expectation features
        if feat_dim:
            feat_len = [len(id_to_feat) for id_to_feat in self.id_to_feat_list]

        # Network variables
        is_train = T.iscalar('is_train')
        word_ids = T.ivector(name='word_ids')
        stem_ids = T.ivector(name='stem_ids')
        char_for_ids = T.imatrix(name='char_for_ids')
        char_rev_ids = T.imatrix(name='char_rev_ids')
        char_pos_ids = T.ivector(name='char_pos_ids')
        tag_ids = T.ivector(name='tag_ids')
        if cap_dim:
            cap_ids = T.ivector(name='cap_ids')
        # boliang
        if feat_dim:
            feat_ids_list = []
            for i in range(len(self.id_to_feat_list)):
                feat_ids_list.append(T.ivector(name='feat_%d_ids' % i))

        # Sentence length
        if word_dim:
            s_len = word_ids.shape[0]
        elif char_dim:
            s_len = char_pos_ids.shape[0]

        # Final input (all word features)
        input_dim = 0
        inputs = []

        #
        # Word inputs
        #
        if word_dim:
            input_dim += word_dim
            word_layer = EmbeddingLayer(n_words, word_dim, name='word_layer')
            word_input = word_layer.link(word_ids)
            inputs.append(word_input)
            # Initialize with pretrained embeddings
            if pre_emb and training:
                new_weights = word_layer.embeddings.get_value()
                print('Loading pretrained embeddings from %s...' % pre_emb)
                pretrained = {}
                emb_invalid = 0
                for i, line in enumerate(load_embedding(pre_emb)):
                    if type(line) == bytes:
                        try:
                            line = str(line, 'utf-8')
                        except UnicodeDecodeError:
                            continue
                    line = line.rstrip().split()
                    if len(line) == word_dim + 1:
                        pretrained[line[0]] = np.array(
                            [float(x) for x in line[1:]]
                        ).astype(np.float32)
                    else:
                        emb_invalid += 1
                if emb_invalid > 0:
                    print('WARNING: %i invalid lines' % emb_invalid)
                c_found = 0
                c_lower = 0
                c_zeros = 0
                # Lookup table initialization
                for i in range(n_words):
                    word = self.id_to_word[i]
                    if word in pretrained:
                        new_weights[i] = pretrained[word]
                        c_found += 1
                    elif word.lower() in pretrained:
                        new_weights[i] = pretrained[word.lower()]
                        c_lower += 1
                    elif re.sub('\d', '0', word.lower()) in pretrained:
                        new_weights[i] = pretrained[
                            re.sub('\d', '0', word.lower())
                        ]
                        c_zeros += 1
                word_layer.embeddings.set_value(new_weights)
                print('Loaded %i pretrained embeddings.' % len(pretrained))
                print('%i / %i (%.4f%%) words have been initialized with '
                      'pretrained embeddings.' % (
                          c_found + c_lower + c_zeros, n_words,
                          100. * (c_found + c_lower + c_zeros) / n_words
                      ))
                print('%i found directly, %i after lowercasing, '
                      '%i after lowercasing + zero.' % (
                          c_found, c_lower, c_zeros
                      ))

        #
        # stem embedding input
        #
        if upenn_stem or ying_stem:
            input_dim += word_dim
            stem_input = word_layer.link(stem_ids)
            inputs.append(stem_input)

        #
        # Chars inputs
        #
        if char_dim:
            input_dim += char_lstm_dim
            char_layer = EmbeddingLayer(n_chars, char_dim, name='char_layer')

            char_lstm_for = LSTM(char_dim, char_lstm_dim, with_batch=True,
                                 name='char_lstm_for')
            char_lstm_rev = LSTM(char_dim, char_lstm_dim, with_batch=True,
                                 name='char_lstm_rev')

            char_lstm_for.link(char_layer.link(char_for_ids))
            char_lstm_rev.link(char_layer.link(char_rev_ids))

            char_for_output = char_lstm_for.h.dimshuffle((1, 0, 2))[
                T.arange(s_len), char_pos_ids
            ]
            char_rev_output = char_lstm_rev.h.dimshuffle((1, 0, 2))[
                T.arange(s_len), char_pos_ids
            ]

            inputs.append(char_for_output)
            if char_bidirect:
                inputs.append(char_rev_output)
                input_dim += char_lstm_dim

            if conv:
                # conv layer
                filters = 50
                filter_shapes = []
                filter_shapes.append((filters, 1, 2, char_dim))
                filter_shapes.append((filters, 1, 3, char_dim))
                filter_shapes.append((filters, 1, 4, char_dim))

                pool_sizes = []
                max_length = 25
                pool_sizes.append((max_length - 2 + 1, 1))
                pool_sizes.append((max_length - 3 + 1, 1))
                pool_sizes.append((max_length - 4 + 1, 1))

                char_input_emb = char_layer.link(char_for_ids)
                char_input_emb = char_input_emb.reshape(
                    (char_input_emb.shape[0],
                     1,
                     char_input_emb.shape[1],
                     char_input_emb.shape[2])
                )
                conv_layer = MultiLeNetConvLayer(char_input_emb, filter_shapes,
                                                 pool_sizes, name='conv_layer')
                conv_layer_output = conv_layer.output
                inputs.append(conv_layer_output)
                input_dim += filters * len(filter_shapes)

        #
        # Capitalization feature
        #
        if cap_dim:
            input_dim += cap_dim
            cap_layer = EmbeddingLayer(n_cap, cap_dim, name='cap_layer')
            inputs.append(cap_layer.link(cap_ids))

        #
        # boliang: expectation features
        #
        if feat_dim:
            # create exp_feat embedding layer
            feat_input = []
            feat_list_len = len(self.id_to_feat_list)
            feat_layers = []
            for i in range(feat_list_len):
                feat_layer = EmbeddingLayer(feat_len[i], feat_dim, name='exp_feat_layer_%d' % i)
                feat_layers.append(feat_layer)
                feat_input.append(feat_layer.link(feat_ids_list[i]))

            ################################
            # feat insertion strategy 1:
            # add features into the word LSTMs input layer.
            ################################
            if comb_method == 1:
                input_dim += feat_dim * len(feat_layers)
                inputs.extend(feat_input)

        # Prepare final input
        if inputs and len(inputs) != 0:
            inputs = T.concatenate(inputs, axis=1)

        #
        # Dropout on final input
        #
        if inputs and dropout:
            dropout_layer = DropoutLayer(p=dropout)
            input_train = dropout_layer.link(inputs)
            input_test = (1 - dropout) * inputs
            inputs = T.switch(T.neq(is_train, 0), input_train, input_test)

        #
        # boliang: numeric feat strategy 1
        #
        # if numeric_feat_strategy == 1:
        #     input_dim += numeric_feat_dim
        #     inputs = T.concatenate([inputs, numeric_feat], axis=1)

        ######################
        # Create final output
        final_output = []
        final_output_dim = 0

        if word_lstm_dim:
            # LSTM for words
            word_lstm_for = LSTM(input_dim, word_lstm_dim, with_batch=False,
                                 name='word_lstm_for')
            word_lstm_rev = LSTM(input_dim, word_lstm_dim, with_batch=False,
                                 name='word_lstm_rev')
            word_lstm_for.link(inputs)
            word_lstm_rev.link(inputs[::-1, :])
            word_for_output = word_lstm_for.h
            word_rev_output = word_lstm_rev.h[::-1, :]
            if word_bidirect:
                word_lstm_output = T.concatenate(
                    [word_for_output, word_rev_output],
                    axis=1
                )
                tanh_layer = HiddenLayer(2 * word_lstm_dim, word_lstm_dim,
                                         name='tanh_layer', activation='tanh')
                word_lstm_output = tanh_layer.link(word_lstm_output)
                final_output.append(word_lstm_output)
            else:
                final_output.append(word_for_output)

            final_output_dim += word_lstm_dim

        if feat_dim:
            feat_input = T.concatenate(feat_input, axis=1)
            #
            # exp feat input dropout
            #
            if dropout:
                dropout_layer = DropoutLayer(p=dropout)
                input_train = dropout_layer.link(feat_input)
                input_test = (1 - dropout) * feat_input
                feat_input = T.switch(T.neq(is_train, 0), input_train, input_test)

            ################################
            #  exp_feat insertion strategy 2:
            # add expectation features to the final layer (before CRF or softmax)
            ################################
            if comb_method == 2:
                final_output.append(feat_input)
                final_output_dim += feat_dim * len(feat_layers)

            ################################
            #  exp_feat insertion strategy 3:
            # add a hidden layer h on top of expectation features and then add h to final layer (before CRFs or softmax)
            ################################
            if comb_method == 3:
                feat_hidden_layer_input_dim = feat_dim * len(feat_layers)
                feat_hidden_layer_dim = 30
                feat_hidden_layer = HiddenLayer(feat_hidden_layer_input_dim, feat_hidden_layer_dim,
                                                name='exp_feat_hidden_layer', activation='tanh')
                final_output.append(feat_hidden_layer.link(feat_input))
                final_output_dim += feat_hidden_layer_dim

            ################################
            # exp_feat insertion strategy 4:
            # add a Bi-LSTMs layer LSTM-h on top of expectation features and then add LSTM-h to
            # final layer (before CRFs or softmax)
            ################################
            if comb_method == 4:
                feat_input_dim = feat_dim * len(feat_layers)
                feat_lstm_layer_dim = feat_input_dim
                feat_lstm_for = LSTM(feat_input_dim, feat_lstm_layer_dim, with_batch=False,
                                     name='feat_lstm_for')
                feat_lstm_rev = LSTM(feat_input_dim, feat_lstm_layer_dim, with_batch=False,
                                     name='feat_lstm_rev')
                feat_lstm_for.link(feat_input)
                feat_lstm_rev.link(feat_input[::-1, :])
                feat_lstm_for_output = feat_lstm_for.h
                feat_lstm_rev_output = feat_lstm_rev.h[::-1, :]
                feat_lstm_output = T.concatenate(
                    [feat_lstm_for_output, feat_lstm_rev_output],
                    axis=1
                )
                feat_tanh_layer = HiddenLayer(2 * feat_lstm_layer_dim, feat_lstm_layer_dim,
                                              name='feat_tanh_layer', activation='tanh')
                feat_lstm_output = feat_tanh_layer.link(feat_lstm_output)
                final_output.append(feat_lstm_output)
                final_output_dim += feat_lstm_layer_dim

        #
        # boliang: numeric feat strategy 2 and 4
        #
        # if numeric_feat_strategy == 2:
        #     final_output.append(numeric_feat)
        #     final_output_dim += numeric_feat_dim
        #
        # if numeric_feat_strategy == 4:
        #     numeric_feat_lstm_layer_dim = numeric_feat_dim
        #     # numeric_feat_lstm_layer_dim = 10
        #     numeric_feat_lstm_for = LSTM(numeric_feat_dim, numeric_feat_lstm_layer_dim, with_batch=False,
        #                                  name='numeric_feat_lstm_for')
        #     numeric_feat_lstm_rev = LSTM(numeric_feat_dim, numeric_feat_lstm_layer_dim, with_batch=False,
        #                                  name='numeric_feat_lstm_rev')
        #     numeric_feat_lstm_for.link(numeric_feat)
        #     numeric_feat_lstm_rev.link(numeric_feat[::-1, :])
        #     numeric_feat_lstm_for_output = numeric_feat_lstm_for.h
        #     numeric_feat_lstm_rev_output = numeric_feat_lstm_rev.h[::-1, :]
        #     numeric_feat_lstm_output = T.concatenate(
        #         [numeric_feat_lstm_for_output, numeric_feat_lstm_rev_output],
        #         axis=1
        #     )
        #     numeric_feat_tanh_layer = HiddenLayer(2 * numeric_feat_lstm_layer_dim, numeric_feat_lstm_layer_dim,
        #                                           name='numeric_feat_tanh_layer', activation='tanh')
        #     numeric_feat_lstm_output = numeric_feat_tanh_layer.link(numeric_feat_lstm_output)
        #     final_output.append(numeric_feat_lstm_output)
        #     final_output_dim += numeric_feat_lstm_layer_dim

        final_output = T.concatenate(final_output, axis=1)

        ###########################
        # if using strategy 2, 3 or 4, add another layer after the concatenation of word LSTMs layer
        # output and expectation layer output. (comment this out if using strategy 1)
        if feat_dim and comb_method in [2, 3, 4]:
            lstm_feat_concatenation_layer_dim = int(final_output_dim / 2)
            lstm_feat_concatenation_layer = HiddenLayer(final_output_dim, lstm_feat_concatenation_layer_dim,
                                                       name='lstm_feat_concatenation_layer',
                                                       activation='tanh')
            lstm_exp_concatenation_layer_output = lstm_feat_concatenation_layer.link(final_output)
            final_output = lstm_exp_concatenation_layer_output
            final_output_dim = lstm_feat_concatenation_layer_dim

        # Sentence to Named Entity tags - Score
        final_layer = HiddenLayer(final_output_dim, n_tags, name='final_layer',
                                  activation=(None if crf else 'softmax'))
        tags_scores = final_layer.link(final_output)

        # No CRF
        if not crf:
            cost = T.nnet.categorical_crossentropy(tags_scores, tag_ids).mean()
        # CRF
        else:
            transitions = shared((n_tags + 2, n_tags + 2), 'transitions')

            small = -1000
            b_s = np.array([[small] * n_tags + [0, small]]).astype(np.float32)
            e_s = np.array([[small] * n_tags + [small, 0]]).astype(np.float32)
            observations = T.concatenate(
                [tags_scores, small * T.ones((s_len, 2))],
                axis=1
            )
            observations = T.concatenate(
                [b_s, observations, e_s],
                axis=0
            )

            # Score from tags
            real_path_score = tags_scores[T.arange(s_len), tag_ids].sum()

            # Score from transitions
            b_id = theano.shared(value=np.array([n_tags], dtype=np.int32))
            e_id = theano.shared(value=np.array([n_tags + 1], dtype=np.int32))
            padded_tags_ids = T.concatenate([b_id, tag_ids, e_id], axis=0)
            real_path_score += transitions[
                padded_tags_ids[T.arange(s_len + 1)],
                padded_tags_ids[T.arange(s_len + 1) + 1]
            ].sum()

            all_paths_scores = forward(observations, transitions)
            cost = - (real_path_score - all_paths_scores)

        # Network parameters
        params = []
        if word_dim:
            self.add_component(word_layer)
            params.extend([word_input])
        if char_dim:
            self.add_component(char_layer)
            self.add_component(char_lstm_for)
            params.extend(char_layer.params)
            params.extend(char_lstm_for.params)
            if char_bidirect:
                self.add_component(char_lstm_rev)
                params.extend(char_lstm_rev.params)
            if conv:
                # add conv layer param
                self.add_component(conv_layer)
                params.extend(conv_layer.params)
        if word_lstm_dim:
            self.add_component(word_lstm_for)
            params.extend(word_lstm_for.params)
        if word_bidirect:
            self.add_component(word_lstm_rev)
            params.extend(word_lstm_rev.params)
        if cap_dim:
            self.add_component(cap_layer)
            params.extend(cap_layer.params)
        self.add_component(final_layer)
        params.extend(final_layer.params)
        if crf:
            self.add_component(transitions)
            params.append(transitions)
        if word_bidirect:
            self.add_component(tanh_layer)
            params.extend(tanh_layer.params)
        # boliang: add expectation feature layers into the components and params
        if feat_dim:
            for exp_feat_layer in feat_layers:
                self.add_component(exp_feat_layer)
                params.extend(exp_feat_layer.params)

            if comb_method == 3:
                # strategy 3
                self.add_component(feat_hidden_layer)
                params.extend(feat_hidden_layer.params)

            if comb_method == 4:
                # strategy 4
                self.add_component(feat_lstm_for)
                self.add_component(feat_lstm_rev)
                self.add_component(feat_tanh_layer)
                params.extend(feat_lstm_for.params)
                params.extend(feat_lstm_rev.params)
                params.extend(feat_tanh_layer.params)

            if comb_method in [2, 3, 4]:
                self.add_component(lstm_feat_concatenation_layer)
                params.extend(lstm_feat_concatenation_layer.params)
        # if numeric_feat_dim:
        #     if numeric_feat_strategy == 4:
        #         self.add_component(numeric_feat_lstm_for)
        #         self.add_component(numeric_feat_lstm_rev)
        #         self.add_component(numeric_feat_tanh_layer)
        #         params.extend(numeric_feat_lstm_for.params)
        #         params.extend(numeric_feat_lstm_rev.params)
        #         params.extend(numeric_feat_tanh_layer.params)
        #
        #     if numeric_feat_strategy in [2, 4]:
        #         self.add_component(lstm_numeric_concatenation_layer)
        #         params.extend(lstm_numeric_concatenation_layer.params)

        # Prepare train and eval inputs
        eval_inputs = []
        if word_dim:
            eval_inputs.append(word_ids)
        if upenn_stem or ying_stem:
            eval_inputs.append(stem_ids)
        if char_dim:
            eval_inputs.append(char_for_ids)
            if char_bidirect:
                eval_inputs.append(char_rev_ids)
            eval_inputs.append(char_pos_ids)
        if cap_dim:
            eval_inputs.append(cap_ids)
        # boliang
        if feat_dim:
            for feat_type_ids in feat_ids_list:
                eval_inputs.append(feat_type_ids)
        # boliang
        # if numeric_feat_dim:
        #     eval_inputs.append(numeric_feat)

        train_inputs = eval_inputs + [tag_ids]

        # Parse optimization method parameters
        if "-" in lr_method:
            lr_method_name = lr_method[:lr_method.find('-')]
            lr_method_parameters = {}
            for x in lr_method[lr_method.find('-') + 1:].split('-'):
                split = x.split('_')
                assert len(split) == 2
                lr_method_parameters[split[0]] = float(split[1])
        else:
            lr_method_name = lr_method
            lr_method_parameters = {}

        # Compile training function
        print('Compiling...')
        if training:
            _updates = Optimization(clip=5.0).get_updates(
                lr_method_name, cost, params, **lr_method_parameters
            )
            if word_dim:
                updates = [(word_layer.embeddings,
                            T.set_subtensor(word_input, _updates[0][1]))]
                updates += _updates[1:]
            else:
                updates = _updates
            f_train = theano.function(
                inputs=train_inputs,
                outputs=cost,
                updates=updates,
                givens=({is_train: np.cast['int32'](1)} if dropout else {}),
                allow_input_downcast=True
            )
        else:
            f_train = None

        # Compile evaluation function
        if not crf:
            f_eval = theano.function(
                inputs=eval_inputs,
                outputs=tags_scores,
                givens=({is_train: np.cast['int32'](0)} if dropout else {}),
                allow_input_downcast=True
            )
        else:
            f_eval = theano.function(
                inputs=eval_inputs,
                outputs=forward(observations, transitions, viterbi=True,
                                return_alpha=False, return_best_sequence=True),
                givens=({is_train: np.cast['int32'](0)} if dropout else {}),
                allow_input_downcast=True
            )

        return f_train, f_eval
