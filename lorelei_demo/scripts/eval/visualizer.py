import codecs
import argparse
import os
import sys
import unidecode
import html
import xml.etree.ElementTree as ET
from jinja2 import Environment, FileSystemLoader

# dirty import from parent class
script_dirname = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dirname, os.pardir, 'format_converter'))
from bio2tab import bio2tab
from bio2bio_offset import bio2bio_offset
import edl_eval


def visualize(data, translation, lexicon, pred_stats, ref_stats, scores, errors,
              is_rtl, no_ref, latin):
    print('=> visualizing...')
    html_result = dict()
    script_dirname = os.path.dirname(os.path.abspath(__file__))

    # sort overall score by f1
    sorted_scores = sorted(scores.items(),
                           key=lambda x: x[1]['overall'][2])

    for i in range(len(data))[:]:
        doc_id = sorted_scores[i][0]
        segs = data[doc_id]

        data_to_render = dict()
        data_to_render['doc_id'] = doc_id
        data_to_render['segs'] = segs
        data_to_render['has_src'] = True
        data_to_render['has_ref'] = True
        data_to_render['has_lex'] = True if lexicon else False
        data_to_render['rtl'] = is_rtl
        data_to_render['no_ref'] = no_ref
        data_to_render['latin'] = latin

        # add translation
        trans = []
        if doc_id in translation and len(segs) == len(translation[doc_id]):
            trans = translation[doc_id]
            data_to_render['has_trans'] = True
        else:
            data_to_render['has_trans'] = False

        data_to_render['trans'] = trans

        # add edl evaluation results
        p = pred_stats[doc_id]
        r = ref_stats[doc_id]
        s = scores[doc_id]
        e = errors[doc_id]
        data_to_render['pred_stats'] = p
        data_to_render['ref_stats'] = r
        data_to_render['scores'] = s
        data_to_render['errors'] = e

        j2_env = Environment(loader=FileSystemLoader(script_dirname),
                             trim_blocks=True)
        html = j2_env.get_template('visualizer.html').render(**data_to_render)

        html_result[doc_id] = html

        sys.stdout.write('  %d documents visualized.\r' % i)
        sys.stdout.flush()

    print('  %d documents visualized in total.' % len(data))

    return html_result


def generate_errors_dict(errors):
    d = dict()
    for doc_id, error in errors.items():
        for error_type, e in error.items():
            for offset, _ in e.items():
                _, start, end = offset
                for i in range(int(start), int(end)):
                    try:
                        d[doc_id][i] = error_type
                    except KeyError:
                        d[doc_id] = {i: error_type}
    return d


def parse_bio(bio_str, no_ref, lexicon, error_dict):
    print("=> parsing bio file...")
    res = dict()
    num_sent = 0
    num_token = 0
    for sent in bio_str.split('\n\n'):
        if not sent.strip():
            continue
        num_sent += 1
        seg = dict()
        seg['tokens'] = []
        for i, line in enumerate(sent.splitlines()):
            num_token += 1
            line = line.split()
            text = line[0]

            # get lexicon
            lex = '*'
            if text in lexicon:
                lex = lexicon[text]

            # get transliteration
            unidecoded_text = unidecode.unidecode(text)
            offset = line[1]

            # get offset
            doc_id, o = offset.split(':')
            start, end = o.split('-')

            # get reference
            if no_ref:
                label = line[-1]
                ref = ""
            else:
                label = line[-1]
                ref = line[-2]

            # get error
            if doc_id in error_dict:
                e = error_dict[doc_id]
            else:
                e = {}
            error_type = 'O'
            for j in range(int(start), int(end)):
                if j in e:
                    if j - 1 not in e:
                        tag = 'B'
                    else:
                        tag = 'I'
                    error_type = '%s-%s' % (tag, e[j])
                    break

            token = dict()
            token['id'] = offset
            token['start'] = start
            token['end'] = end
            token['label'] = label
            token['ref'] = ref
            token['text'] = html.escape(text)
            token['unidecoded_text'] = html.escape(unidecoded_text)
            token['lex'] = lex
            token['error'] = error_type

            seg['tokens'].append(token)
        try:
            res[doc_id].append(seg)
        except KeyError:
            res[doc_id] = [seg]

        sys.stdout.write('  %d sentences and %d tokens parsed from bio.\r' %
                         (num_sent, num_token))
        sys.stdout.flush()

    num_doc = len(res)

    print('  %d documents, %d sentences and %d tokens parsed from bio.' %
          (num_doc, num_sent, num_token))

    return res


def load_translation(translation_dir, doc_ids):
    if not translation_dir or not os.path.exists(translation_dir):
        return {}

    print('=> loading translation...')
    doc_id_added = set()
    translation = dict()
    for fn in os.listdir(translation_dir):
        if '.ltf.xml' not in fn:
            continue

        d_id = fn.split('.')[0]

        if d_id not in doc_ids or d_id in doc_id_added:
            continue

        root = ET.parse(os.path.join(translation_dir, fn))
        sents = []
        for seg in root.findall('.//SEG'):
            seg_text = seg.find('ORIGINAL_TEXT').text
            seg_text = html.escape(seg_text)
            sents.append(seg_text.split())
        translation[d_id] = sents

        doc_id_added.add(d_id)

    print('  %d translation documents loaded.' % len(translation))

    return translation


def load_lexicon(lexicon_file):
    if not lexicon_file or not os.path.exists(lexicon_file):
        return {}

    print('=> loading lexicons...')
    lexicon = dict()

    if lexicon_file.endswith('.xml'):
        for event, elem in ET.iterparse(lexicon_file):
            if elem.tag != 'ENTRY':
                continue
            lemma = elem.find('LEMMA')
            gloss = elem.find('GLOSS')
            lexicon[lemma] = gloss
    else:
        for line in codecs.open(lexicon_file):
            line = line.strip()
            if not line:
                continue
            line = line.split('\t')
            text = line[0]
            lex = line[1]
            lex = html.escape(lex)
            lexicon[text] = lex

    print('  %d entries loaded.' % len(lexicon))

    return lexicon


def write2file(html_result, out_dir, rank):
    for i, (doc_id, html) in enumerate(html_result.items()):
        if rank:
            # add index to file name
            index_len = len(str(len(html_result)))
            index = str(i).zfill(index_len)
            out_path = os.path.join(out_dir, '%s_%s.html' % (index, doc_id))
        else:
            out_path = os.path.join(out_dir, doc_id+'.html')

        with codecs.open(out_path, 'w', 'utf-8') as f:
            f.write(html)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("bio")
    parser.add_argument("output_dir")
    parser.add_argument("--no_ref", action="store_true", default=False,
                        help="visualize reference")
    parser.add_argument("--translation",
                        help="directory contains eng translation in ltf format")
    parser.add_argument("--lexicon")
    parser.add_argument('--rtl', action="store_true", default=False,
                        help="right to left alignment.")
    parser.add_argument('--rank', action='store_true', default=False,
                        help='rank document by f1 score.')
    parser.add_argument('--latin', action='store_true', default=False,
                        help='show latin script')
    parser.add_argument('--no_offset', action='store_true', default=False,
                        help='tokenize file with space, 20 sentences per '
                             'document')

    args = parser.parse_args()

    print("=> loading bio data...")
    bio_str = codecs.open(args.bio, 'r', 'utf-8').read()

    # generate offsets if no offset provided
    d_id = os.path.basename(args.bio).replace('.bio', '')
    bio_offset = bio2bio_offset(bio_str, d_id, split=20)
    bio_str = '\n\n'.join(list(bio_offset.values()))

    #
    # load lexicon
    #
    lexicon = load_lexicon(args.lexicon)

    #
    # evaluate edl results
    #
    # generate ref bio str and tab str
    ref_bio_str = ''
    if args.no_ref:
        ref_bio_str = bio_str
    else:
        for line in bio_str.splitlines():
            if not line.strip():
                ref_bio_str += line
            line = ' '.join(line.split()[:-1])
            ref_bio_str += line + '\n'
    pred_tab = bio2tab(bio_str)
    ref_tab = bio2tab(ref_bio_str)

    input_bio, ref_bio, input_tab, ref_tab = edl_eval.split_data(
        bio_str, pred_tab, ref_bio_str, ref_tab
    )
    # evaluate result for each document
    overall_pred_stats = {}
    overall_ref_stats = {}
    overall_scores = {}
    overall_errors = {}
    for doc_id in ref_bio:
        if doc_id not in input_tab:
            input_tab[doc_id] = ''
        if doc_id not in input_bio:
            input_bio[doc_id] = ''

        # ref stats
        input_stats = edl_eval.stats(input_bio[doc_id], input_tab[doc_id])
        ref_stats = edl_eval.stats(ref_bio[doc_id], ref_tab[doc_id])
        overall_pred_stats[doc_id] = input_stats
        overall_ref_stats[doc_id] = ref_stats

        # evaluate tab
        scores = edl_eval.evaluate(input_tab[doc_id], ref_tab[doc_id])

        # error analysis
        errors = edl_eval.error_analysis(input_tab[doc_id], ref_tab[doc_id])

        overall_scores[doc_id] = scores
        overall_errors[doc_id] = errors

    #
    # parse bio str
    #
    error_dict = generate_errors_dict(overall_errors)
    data = parse_bio(bio_str, args.no_ref, lexicon, error_dict)

    #
    # load translation
    #
    translation = load_translation(args.translation, data.keys())

    #
    # visualize ner results
    #
    html_result = visualize(data,
                            translation,
                            lexicon,
                            overall_pred_stats,
                            overall_ref_stats,
                            overall_scores,
                            overall_errors,
                            args.rtl,
                            args.no_ref,
                            args.latin)

    write2file(html_result, args.output_dir, args.rank)
