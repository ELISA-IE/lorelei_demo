import os
import tempfile
import codecs

from multiprocessing import Pool
from functools import partial
try:
    from lorelei_demo.scripts.format_converter import ltf2bio
except ImportError:
    pass

from lorelei_demo.app.model_preload import pytorch_load_model, pytorch_tag


def multithread_tagger(input, output, model_path, threads=1, is_bio=False, filelist=None):
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
    func = partial(pytorch_single_thread_tagger, model_path, is_bio)
    results = p.map(func, input_batches)

    with codecs.open(output, 'w', 'utf-8') as f:
        f.write('\n\n'.join(results))


def pytorch_single_thread_tagger(model_path, is_bio, input_batches,):
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

    # temporal output path
    out_path = os.path.join(tmp_dir, 'output.bio')

    # run tagger
    model, parameters, mappings = pytorch_load_model(model_path)
    pytorch_tag(bio_input_file, out_path, model, parameters, mappings)

    #
    # process output
    #
    return codecs.open(out_path, 'r', 'utf-8').read()
