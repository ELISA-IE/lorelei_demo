import os
import subprocess


train = 'data/train.bio'
dev = 'data/dev.bio'
test = 'data/test.bio'

model_dir = 'model'

pre_emb = ''

# run command
script = '../train.py'
cmd = ['python3', script,
       # data settings
       '--train', train,
       '--dev', dev,
       '--test', test,
       '--model_dp', model_dir,
       '--tag_scheme', 'iob',

       # parameter settings
       '--lower', '0',
       '--char_dim', '50',
       '--char_lstm_dim', '50',
       '--char_bidirect', '1',
       '--word_dim', '100',
       '--word_lstm_dim', '100',
       '--word_bidirect', '1',
       '--pre_emb', pre_emb,
       '--all_emb', '0',
       '--cap_dim', '0',
       '--crf', '1',
       '--conv', '1',
       '--dropout', '0.5',
       '--lr_method', 'sgd-lr_.01',

       # external feature settings
       '--feat_dim', '0',
       '--comb_method', '0',
       '--upenn_stem', '',
       '--pos_model', '',
       '--brown_cluster', '',
       '--ying_stem', ''
       ]

os.environ.update({'OMP_NUM_THREADS': '1'})
print(' '.join(cmd))
subprocess.call(cmd, env=os.environ)