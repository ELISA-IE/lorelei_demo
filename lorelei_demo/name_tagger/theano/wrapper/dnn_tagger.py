import argparse
import os
import subprocess
import tempfile
import codecs

from multiprocessing import Pool
from functools import partial
try:
    from lorelei_demo.scripts.format_converter import ltf2bio
except ImportError:
    pass


def multithread_tagger(input, output, model_dir, threads, is_bio, filelist):
    ##
    # multi-processing
    #
    if is_bio:
        bio_str = codecs.open(input, 'r', 'utf-8').read()
        model_input = [bio.strip() for bio in bio_str.split('\n\n')
                       if bio.strip()]
    else:
        if filelist:
            fns = [item for item in open(filelist).read().splitlines() if item]
            model_input = []
            for fn in fns:
                fp = os.path.join(input, fn)
                if not os.path.exists(fp):
                    print("%s not exists."% fp)
                    continue
                model_input.append(fp)
        else:
            model_input = [os.path.join(input, fn)
                           for fn in os.listdir(input) if fn.endswith('.ltf.xml')]

    model_input = model_input[:]

    # split documents
    n = int(len(model_input) / threads + 1)
    input_batches = [model_input[i:i + n]
                     for i in range(0, len(model_input), n)]

    # run multiple single thread tagger
    p = Pool(threads)
    func = partial(single_thread_tagger, model_dir, is_bio)
    results = p.map(func, input_batches)

    with codecs.open(output, 'w', 'utf-8') as f:
        f.write('\n\n'.join(results))


def single_thread_tagger(model_dir, is_bio, input_batches,):
    print('single thread tagger starting...')
    bios = []
    if is_bio:
        bios = input_batches
    else:
        for i, l in enumerate(input_batches):
            bio_str = ltf2bio.ltf2bio(codecs.open(l, 'r', 'utf-8').read())
            bios.append(bio_str)

    # merge multiple bio into one single bio
    bio_input = '\n\n'.join(bios)

    # save bio input to file
    tmp_dir = tempfile.mkdtemp()
    print('thread temp file: %s' % tmp_dir)
    bio_input_file = os.path.join(tmp_dir, 'input.bio')
    f = codecs.open(bio_input_file, 'w', 'utf-8')
    if bio_input.strip():
        f.write(bio_input)
    f.close()

    # LSTMs name tagger path
    tagger_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               os.pardir, 'tagger.py')

    # temporal output path
    out_path = os.path.join(tmp_dir, 'output.bio')

    # LSTMs tagger command
    cmd = ['python3', tagger_path,
           '--model', model_dir,
           '--input', bio_input_file,
           '--output', out_path]

    print(' '.join(cmd))
    os.environ.update({'OMP_NUM_THREADS': '1'})
    subprocess.call(cmd, env=os.environ)

    #
    # process output
    #
    return codecs.open(out_path, 'r', 'utf-8').read()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=str,
                        help='input path')
    parser.add_argument('output', type=str,
                        help='output path')
    parser.add_argument('model_dir', type=str,
                        help='model directory')
    parser.add_argument('-b', '--bio', action='store_true', default=False,
                        help='use bio as input format')
    parser.add_argument('--threads', default=4, type=int,
                        help='number of cores to use')
    parser.add_argument('--filelist',
                        help='A filelist containing document file names. '
                             '(output should be directory for this option)')

    args = parser.parse_args()

    input = args.input
    output = args.output
    model_dir = args.model_dir
    threads = args.threads
    is_bio = args.bio
    filelist = args.filelist

    multithread_tagger(input, output, model_dir,
                       threads=threads, is_bio=is_bio, filelist=filelist)




