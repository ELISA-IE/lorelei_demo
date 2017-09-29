__author__ = 'boliangzhang'

import os
import uuid
import socket
import subprocess
import io
import urllib.request
import xml.etree.ElementTree as ET

from lorelei_demo.scripts.format_converter.rsd2bio import rsd2bio
from lorelei_demo.scripts.format_converter.bio2tab import bio2tab
from lorelei_demo.scripts.format_converter.tab2kg import tab2kg
from lorelei_demo.scripts.format_converter.laf2tab import laf2tab
from lorelei_demo.scripts.format_converter.ltf2rsd import ltf2rsd
from lorelei_demo.scripts.format_converter.ltftab2bio import ltftab2bio
from lorelei_demo.scripts.format_converter.bio2ltf import bio2ltf
from lorelei_demo.scripts.format_converter import bio2laf

from lorelei_demo.app import lorelei_demo_dir
from lorelei_demo.app.geo_name import GeoName
from lorelei_demo.app.visualization.edl_err_ana import visualize_single_doc_without_gold
from lorelei_demo.app.visualization.edl_err_ana import visualize_single_doc_with_gold
import json
import tempfile
import re
from flask import request, send_from_directory, Blueprint, jsonify
from flask_cors import cross_origin


bp_api = Blueprint('api', __name__)


#
# swagger public APIs
#
@bp_api.route("/elisa_ie/api", methods=["GET"])
@cross_origin()
def swagger():
    """
    swagger api main page
    """
    return send_from_directory(
        os.path.join(lorelei_demo_dir, 'lorelei_demo/app/static/swagger'),
        'index.html'
    )


@bp_api.route("/elisa_ie/status", defaults={'identifier': ""}, methods=["GET"])
@bp_api.route("/elisa_ie/status/<identifier>", methods=["GET"])
def status(identifier):
    """
    status of ie server
    """
    # get status
    status = get_status()

    # return status
    result = dict()

    for language_code in status:
        d = dict()
        d["identifier"] = language_code
        language = status[language_code][0]
        lang_status = status[language_code][1]
        d["language"] = language
        d["status"] = lang_status
        result[language_code] = d

    if identifier:
        if identifier not in status.keys():
            return 'Language code not found.'
        result = result[identifier]
    else:
        result = list(result.values())

    return json.dumps(result, indent=4, sort_keys=True)


@bp_api.route("/elisa_ie/run/<identifier>", methods=["POST"])
def run(identifier):
    """
    single document API
    """
    language_code = identifier

    # get output format
    output_format = request.args.get('output_format')

    # return error message for invalid identifier
    if not is_valid_identifier(identifier):
        return "Invalid language code."

    # get plain text input
    plain_text_input = request.form.get('text')

    # run ner
    tab_str = run_plain_text(language_code, plain_text_input)

    # run entity linking
    tab_str = entity_linking(tab_str)

    if output_format == 'EvalTab':
        result = tab_str
    elif output_format == 'KnowledgeGraph':
        result = tab2kg(tab_str)
    else:
        result = 'Please choose name tagging output format.'

    return result


@bp_api.route("/elisa_ie/name_translation/<identifier>", methods=["GET"])
def name_translation(identifier):
    query = request.form.get('name')

    return json.dumps(name_translation(query, identifier), ensure_ascii=False)


@bp_api.route("/elisa_ie/name_transliteration/<identifier>", methods=["GET"])
def name_transliteration(identifier):
    name = request.args.get('name')

    if len(name) > 15:
        transliteration_result = '[]'
    else:
        # generate transliteration
        url = 'http://0.0.0.0:12306/trans/%s/%s?number=5' % (
            identifier, urllib.request.quote(name)
        )
        try:
            transliteration_result = urllib.request.urlopen(url, timeout=5).read()
        except (urllib.request.URLError, socket.timeout) as e:
            transliteration_result = '[]'
            print(e)

    transliteration_result = json.loads(transliteration_result)

    return jsonify(transliteration_result)


# todo
def entity_linking(tab_str):
    return tab_str


@bp_api.route("/elisa_ie/localize/<identifier>", methods=['GET'])
def api_localize(identifier):
    query = request.args.get('query')
    language_code = identifier

    # call linking api
    try:
        query = query.encode('utf-8')
        url = 'https://blender04.cs.rpi.edu/~panx2/cgi-bin/linking.py?query=%s' \
              % urllib.request.quote(query)
        edl_result = urllib.request.urlopen(url, timeout=20).read()
        edl_result = json.loads(edl_result)
        edl_result = edl_result['results'][0]['annotations'][0]['url']
    except :
        edl_result = ''
        pass

    # get content within '<' and '>'
    mention_name = edl_result[edl_result.find("<") + 1:edl_result.find(">")]
    mention_name = mention_name.replace('http://dbpedia.org/resource/', '')
    # remove content in parenthesis
    mention_name = re.sub(r'\([^)]*\)', '', mention_name)
    mention_name = mention_name.replace('_', ' ')

    # load GeoName database
    g = GeoName()

    position = g.search_city_position(mention_name)

    if not position[0] or not position[1]:
        res = {'error': 'longitude and latitude not found.'}
    else:
        res = {'latitude': position[0],
               'longitude': position[1]}

    return json.dumps(res)


@bp_api.route("/elisa_ie/sample_doc/<identifier>", methods=["GET"])
def get_sample_doc(identifier):
    def generate_sent_from_bio(bio_fp, doc_num, sent_num):
        res_bios = []
        doc_bio = []
        current_bio = []
        for line in io.open(bio_fp, 'r', -1, 'utf-8'):
            try:
                if line.strip() == '':
                    doc_bio.append('\n'.join(current_bio))
                    current_bio = []  # clear current bio
                    if len(doc_bio) == sent_num:
                        res_bios.append(doc_bio)
                        if len(res_bios) == doc_num:
                            break
                        doc_bio = []  # clear doc bio
                else:
                    current_bio.append(line.strip())
            except ValueError as e:
                print(bio_fp)
                print(e)

        return res_bios

    def validate(bios, doc_num, sent_num):
        res = []
        for i in range(doc_num):
            try:
                if len(bios[i]) == sent_num:
                    res.append(bios[i])
                else:
                    res.append(bios[i] + (sent_num - len(bios[i])) * [bios[0][0]])
            except IndexError:
                res.append(sent_num * [bios[0][0]])

        return res

    il_annotation_dir = os.path.join(
        lorelei_demo_dir, 'data/app/elisa_ie/il_annotation_300'
    )
    test_bio_fp = os.path.join(il_annotation_dir, identifier, 'bio/test.bio')
    train_bio_fp = os.path.join(il_annotation_dir, identifier, 'bio/train.bio')

    example_doc_num = 3
    test_sent_num_per_doc = 4
    train_sent_num_per_doc = 4

    test_res_bios = generate_sent_from_bio(
        test_bio_fp, example_doc_num, test_sent_num_per_doc
    )
    train_res_bios = generate_sent_from_bio(
        train_bio_fp, example_doc_num, train_sent_num_per_doc
    )

    # validate res_docs and res_bios
    test_res_bios = validate(test_res_bios, example_doc_num, test_sent_num_per_doc)
    train_res_bios = validate(train_res_bios, example_doc_num, train_sent_num_per_doc)

    res = {'sample_docs': [],
           'sample_bio': []
           }

    for i in range(example_doc_num):
        bios = []
        for j in range(train_sent_num_per_doc):
            bios.append(train_res_bios[i][j])
            if j < test_sent_num_per_doc:
                bios.append(test_res_bios[i][j])
        raw_bio_str = '\n\n'.join(bios)

        # generate offset for each token here, because there is no offset in
        # the original bio.
        if identifier in ['zh', 'ja', 'th', 'zh-yue', 'zh-classical']:
            delimiter = ''
        else:
            delimiter = ' '

        doc_id = '%s-sample-%d' % (identifier, i)
        ltf = bio2ltf(raw_bio_str, doc_id, with_offset=False, delimiter=delimiter)
        laf = bio2laf.bio2laf_no_offset(raw_bio_str, doc_id, delimiter)
        bio_str = ltftab2bio(ltf, laf2tab(laf))

        res['sample_bio'].append(bio_str)

    for i, bio in enumerate(res['sample_bio']):
        doc_id = bio.strip().splitlines()[0].split()[1].split(':')[0]
        ltf_root = bio2ltf(bio, with_offset=True)[doc_id]

        res['sample_docs'].append(ltf2rsd(ET.tostring(ltf_root, 'utf-8')))

    return jsonify(res)


#
# helper functions
#
def run_plain_text(language_code, plain_text, to_visualize=False):
    #
    # prepare data
    #
    doc_id = str(uuid.uuid4()).replace('-', '_')

    # get select doc index from demo interface (this will be none if called
    # from API)
    seleted_doc_index = request.form.get('seleted_doc_index')
    if seleted_doc_index: seleted_doc_index = int(seleted_doc_index)

    if to_visualize and seleted_doc_index != 3:
        samples = json.loads(get_sample_doc(language_code).data)
        bio_str = samples['sample_bio'][seleted_doc_index]
        doc_id = bio_str.splitlines()[0].split(' ')[1].split(':')[0]
        plain_text = samples['sample_docs'][seleted_doc_index]
    else:
        # text normalization
        plain_text = plain_text.replace("\r\n", "\n").replace("\r", "\n")

        # convert plain text to bio format
        seg_option = 'nltk+linebreak'
        tok_option = 'unitok'
        bio_str = rsd2bio(plain_text, doc_id, seg_option, tok_option)

    # make temp file for input and output bio
    input_bio_file = tempfile.mktemp()
    with open(input_bio_file, 'w', encoding="utf8") as f:
        f.write(bio_str)
    output_tab_file = tempfile.mktemp()

    #
    # run dnn name tagger
    #
    run_dnn(language_code, input_bio_file, output_tab_file)

    tab_str = open(output_tab_file, encoding="utf8").read()

    if to_visualize:
        # create sys tab
        sys_tab = tempfile.mktemp()
        with open(sys_tab, 'w') as f:
            f.write(tab_str)

        # check rtl
        status = get_status()  # check if the language is rtl
        if status[language_code][3] == 'rtl':
            rtl = True
        else:
            rtl = False

        # create workspace dir
        workspace_dir = tempfile.mkdtemp()
        print('visualization temp dir: ' + workspace_dir)

        if seleted_doc_index != 3:  # if it's a sample doc
            # create gold tab
            gold_tab_str = bio2tab(bio_str)

            gold_tab = tempfile.mktemp()
            with open(gold_tab, 'w') as f:
                f.write(gold_tab_str)
            print('demo sample gold tab path: %s' % gold_tab)

            try:
                visualization_html = visualize_single_doc_with_gold(
                    doc_id, None, gold_tab, sys_tab, out_dir=workspace_dir,
                    srctext=plain_text, lang=language_code, rtl=rtl
                )
            except KeyError as e:  # if eval.tab file is empty
                print(e)
                visualization_html = \
                    '<span style="color:red;">No name found.</span>'
        else:  # if it's an entered text
            try:
                visualization_html = visualize_single_doc_without_gold(
                    doc_id, None, sys_tab, out_dir=workspace_dir,
                    srctext=plain_text, lang=language_code, rtl=rtl
                )
            except KeyError as e:  # if eval.tab file is empty
                print(e)
                visualization_html = \
                    '<span style="color:red;">No name found.</span>'

        return tab_str, visualization_html
    else:
        return tab_str


def is_valid_identifier(identifier):
    supported_languages = get_status()

    if identifier not in supported_languages.keys():
        return False

    return True


def get_status():
    # check model directory to get online and offline languages
    model_dir = os.path.join(lorelei_demo_dir, 'data/name_tagger/models')
    languages = [item for item in os.listdir(model_dir) if
                 item != '.DS_Store']

    online_languages = []
    offline_languages = []
    for lan in languages:
        model_dp = os.path.join(model_dir, lan, 'model')
        if os.path.exists(model_dp):
            online_languages.append(lan)
        else:
            offline_languages.append(lan)

    # load language code mapping
    wiki_lang_mapping_fp = os.path.join(
        lorelei_demo_dir, 'data/app/elisa_ie/wikilang_mapping.txt'
    )
    f = open(wiki_lang_mapping_fp, encoding="utf8").read().strip()
    wiki_lang_code_mapping = dict()
    wiki_lang_group_mapping = dict()
    wiki_lang_direction_mapping = dict()

    for line in f.splitlines():
        line = line.split('\t')
        lang_code = line[0]
        lang_name = line[2]
        lang_group = line[3]
        direction = line[4]

        wiki_lang_code_mapping[lang_code] = lang_name
        wiki_lang_group_mapping[lang_code] = lang_group
        wiki_lang_direction_mapping[lang_code] = direction

    # map language code to language names
    status = dict()
    for lang_code, lang_name in wiki_lang_code_mapping.items():
        lang_group = wiki_lang_group_mapping[lang_code]
        direction = wiki_lang_direction_mapping[lang_code]
        if lang_code in online_languages:
            status[lang_code] = (lang_name, 'online', lang_group, direction)
        elif lang_code in offline_languages:
            status[lang_code] = (lang_name, 'offline', lang_group, direction)

    return status


#
# run name tagger methods
#
def run_dnn(language_code, input_file, ouput_file):
    print('=> running dnn name tagger...')
    tagger_script = os.path.join(
        lorelei_demo_dir, 'lorelei_demo/name_tagger/theano/wrapper/dnn_tagger.py'
    )

    model_dir = os.path.join(
        lorelei_demo_dir, 'data/name_tagger/models/%s/model/' % language_code
    )

    ner_bio_file = tempfile.mktemp()
    cmd = ['python3', tagger_script, input_file, ner_bio_file, model_dir,
           '-b', '--threads', '1']

    print(' '.join(cmd))
    subprocess.call(cmd)

    # convert bio result to tab
    ner_tab = bio2tab(open(ner_bio_file, encoding="utf8").read())
    with open(ouput_file, 'w', encoding="utf8") as f:
        if ner_tab.strip():
            f.write(ner_tab)

    # Uyghur post-processing
    if language_code == 'ug':
        print('=> running xiaoman uig post processing...')
        pp_dir = os.path.join(
            lorelei_demo_dir,
            'lorelei_demo/name_tagger/post_processing/xiaoman_pp/il3/'
        )
        pp_script = os.path.join(pp_dir, 'post_processing.py')
        cmd = ['python3', pp_script,
               ner_bio_file,
               ouput_file,
               ouput_file,
               '--ppsm', os.path.join(pp_dir, 'psm_flat_setE'),
               '--pgaz', os.path.join(pp_dir, 'high_confidence.gaz'),
               '--prule', os.path.join(pp_dir, 'il3.rule'),
               ]
        print(' '.join(cmd))
        subprocess.call(cmd)

    return ner_bio_file