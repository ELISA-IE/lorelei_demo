import subprocess
import os


dnn_tagger_script = '../wrapper/dnn_tagger.py'
model_dir = 'model/word_dim=100,word_lstm_dim=100,word_bidirect=True,pre_emb=,all_emb=False,cap_dim=0,crf=True,conv=True,dropout=0.5,lr_method=sgd-lr_.01,feat_dim=0,comb_method=0,upenn_stem=,pos_model=,brown_cluster=,ying_stem=,gaz='
input_file = 'data/test.bio'
output_file = 'result/test.ner.bio'

cmd = ['python3',
       dnn_tagger_script,
       input_file,
       output_file,
       model_dir,
       '-b',
       '--threads',
       '5']

print(' '.join(cmd))
subprocess.call(cmd)