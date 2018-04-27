# this script trains name tagging models for 282 languages using various types
# of sources. Pytorch name tagger is used.

# import io
# import tempfile
# import argparse
# import stat
# import time
# import socket
# import math
# from multiprocessing import Pool
# from functools import partial
# import subprocess
# from subprocess import Popen, PIPE
# from collections import OrderedDict
# from src.naacl15 import elisa_ie_root
# from src.demo.app.visualization.edl_err_ana import visualize_batch_doc_with_gold, visualize_batch_doc_without_gold
# from src.demo.app.tab_api import evaluate_tab_file

import os
import sys
import paramiko
import logging
import time
from lorelei_demo.app.misc.train_282_models.utils import generate_pretrained_embedding_path, generate_gold_ann_path, generate_wikiann_ann_path
from lorelei_demo.app import lorelei_demo_dir


def train_model(server_id, lang_code, train, dev, test, model_path, pre_emb, emb_dim):
    dnn_pytorch_dir = os.path.join(lorelei_demo_dir, 'lorelei_demo/name_tagger/dnn_pytorch')
    train_script = os.path.join(dnn_pytorch_dir, 'dnn_pytorch/seq_labeling/train.py')

    python_path = '/nas/data/m1/zhangb8/tools/anaconda3/bin/python3.6'
    cmd = [
        python_path,
        train_script,
        # data settings
        '--train', train,
        '--dev', dev,
        '--test', test,
        '--model_dp', model_path,
        '--tag_scheme', 'iobes',

        # parameter settings
        '--lower', '0',
        '--zeros', '1',
        '--char_dim', '25',
        '--char_lstm_dim', '0',
        '--char_conv', '25',
        '--word_dim', str(emb_dim),
        '--word_lstm_dim', '100',
        '--all_emb', '0',
        '--cap_dim', '0',
        '--crf', '1',
        '--dropout', '0.5',
        '--lr_method', 'sgd-init_lr=.01-lr_decay_epoch=100',
        '--batch_size', '40',
        '--num_epochs', '100',
    ]

    if pre_emb:
        cmd += ['--pre_emb', pre_emb]

    #
    # run cmd at background using screen
    #
    # lorelei demo path
    path_variable = 'OMP_NUM_THREADS=1 PYTHONPATH=/data/m1/zhangb8/lorelei_demo/:/nas/data/m1/zhangb8/lorelei_demo/lorelei_demo/name_tagger/dnn_pytorch'

    screen_cmd = [path_variable, 'screen', "-d", "-m", "-S", 'dnn_training_%s' % lang_code,
                  '%s' % ' '.join(cmd)]

    logging.info(' '.join(screen_cmd))

    # ssh to execute command on server
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('blender0%d.cs.rpi.edu' % server_id, username='zhangb8', password='RPI.blender666')
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(' '.join(screen_cmd))
    ssh.close()

    # execute at local
    # subprocess.call(' '.join(screen_cmd), shell=True)


def main():
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    annotation_path = generate_wikiann_ann_path()

    annotation_path.update(generate_gold_ann_path())

    pre_emb_path = generate_pretrained_embedding_path()

    model_dir = os.path.join(lorelei_demo_dir, 'data/name_tagger/pytorch_models/')
    os.makedirs(model_dir, exist_ok=True)

    # lang_to_process = [
    #     'ar', 'ti', 'om', 'zh', 'hu', 'ug', 'fa', 'bg', 'hr', 'pl', 'ru', 'uk',
    #     'sk', 'es', 'pt', 'en', 'de', 'sv'
    # ]
    lang_to_process = ['ug']
    requests_sent = 0
    for lang_code, ann_path in list(annotation_path.items())[270:300]:
        if lang_code in lang_to_process:
            continue
        logging.info('#')
        logging.info('# processing %s...' % lang_code)
        logging.info('#')

        if lang_code in pre_emb_path:
            pre_emb = pre_emb_path[lang_code][0]
            emb_dim = pre_emb_path[lang_code][1]
        else:
            pre_emb = ''
            emb_dim = '100'

        train = ann_path['train']
        dev = ann_path['dev']
        test = ann_path['test']

        # create model directory
        model_path = os.path.join(model_dir, lang_code)
        os.makedirs(model_path, exist_ok=True)

        server_id = 5
        train_model(server_id, lang_code, train, dev, test, model_path, pre_emb, emb_dim)

        requests_sent += 1
        logging.info('%d requests have been sent.' % requests_sent)

        time.sleep(5)


if __name__ == "__main__":
    main()
