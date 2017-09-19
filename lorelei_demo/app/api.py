__author__ = 'boliangzhang'

import os
import uuid
import socket
import subprocess
import urllib.request

from lorelei_demo.scripts.format_converter.rsd2bio import rsd2bio
from lorelei_demo.scripts.format_converter.bio2tab import bio2tab
from lorelei_demo.scripts.format_converter.tab2kg import tab2kg

from lorelei_demo.app import lorelei_demo_dir
from lorelei_demo.app.geo_name import GeoName

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

    tab_str = run_plain_text(language_code, plain_text_input)

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


@bp_api.route("/elisa_ie/localize/<identifier>", methods=['GET'])
def api_localize(identifier):
    query = request.args.get('query')
    language_code = identifier

    # call linking api
    try:
        query = query.encode('utf-8')
        url = 'https://blender04.cs.rpi.edu/~panx2/cgi-bin/linking.py?query=%s'\
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


#
# helper functions
#
def run_plain_text(language_code, plain_text):
    #
    # prepare data
    #
    doc_id = str(uuid.uuid4()).replace('-', '_')

    # create workspace dir
    workspace_dir = tempfile.mkdtemp()
    print('single doc ie temp dir: '+workspace_dir)

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

    return open(output_tab_file, encoding="utf8").read()


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
        lorelei_demo_dir, 'data/app/wikilang_mapping.txt'
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