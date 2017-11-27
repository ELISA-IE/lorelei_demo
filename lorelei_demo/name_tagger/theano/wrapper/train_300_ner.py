import os
import shutil
from multiprocessing import Pool
from functools import partial
import subprocess

import lorelei_demo


def train(model_dp, il_data_dp):
    train_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     os.pardir, 'train.py')

    train_set = os.path.join(il_data_dp, 'train.bio')
    dev_set = os.path.join(il_data_dp, 'test.bio')
    test_set = os.path.join(il_data_dp, 'test.bio')

    cmd = ['python3', train_script_path,
           '--train', train_set,
           '--dev', dev_set,
           '--test', test_set,
           '--model_dp', model_dp,
           '--tag_scheme', 'iobes',
           '--lower', '1',
           '--char_dim', '50',
           '--char_lstm_dim', '50',
           '--char_bidirect', '1',
           '--word_dim', '100',
           '--word_lstm_dim', '100',
           '--word_bidirect', '1',
           '--pre_emb', '',
           '--all_emb', '0',
           '--cap_dim', '1',
           '--crf', '1',
           '--conv', '1',
           '--dropout', '0.5',
           '--lr_method', 'sgd-lr_.01',
           '--feat_dim', '0',
           '--comb_method', '0',
           '--upenn_stem', '',
           '--pos_model', '',
           '--brown_cluster', '',
           '--ying_stem', ''
           ]

    print(' '.join([str(item) for item in cmd]))

    os.environ.update({'OMP_NUM_THREADS': '1'})

    subprocess.call(cmd)


def batch_train(lorelei_demo_dir, lang_batch):
    print('#')
    print('# training models for %s' % ', '.join(lang_batch))
    print('#')
    for l in lang_batch:
        print('=> processing', l)
        data_dp = os.path.join(lorelei_demo_dir,
                               'data/app/elisa_ie/il_annotation_300/%s/bio' % l)
        model_dp = os.path.join(lorelei_demo_dir,
                                'data/name_tagger/models/%s' % l)

        if os.path.exists(model_dp):
            continue
            # shutil.rmtree(model_dp)
        os.makedirs(model_dp)

        train(model_dp, data_dp)

        # rename model name to 'model'
        model_name = os.path.join(model_dp, os.listdir(model_dp)[0])
        print(model_name)
        renamed_model_name = os.path.join(model_dp, 'model')
        print(renamed_model_name)
        shutil.move(model_name, renamed_model_name)


if __name__ == "__main__":
    lorelei_demo_dir = os.path.join(os.path.dirname(lorelei_demo.__file__),
                                    '../')

    il_annotation_300_dir = os.path.join(lorelei_demo_dir,
                                         'data/app/elisa_ie/il_annotation_300')

    languages = [fn for fn in os.listdir(il_annotation_300_dir)
                 if os.path.isdir(os.path.join(il_annotation_300_dir, fn))]

    languages = languages[:]

    threads = 4

    n = int(len(languages) / threads + 1)
    lang_batches = [languages[i:i + n]
                    for i in range(0, len(languages), n)]

    p = Pool(threads)
    func = partial(batch_train, lorelei_demo_dir)
    p.map(func, lang_batches)
