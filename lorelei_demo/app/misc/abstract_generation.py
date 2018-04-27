from flask import render_template, Blueprint, request, jsonify
import requests
import json
import urllib.request

bp_abstract_generation = Blueprint('abstract_generation', __name__)


@bp_abstract_generation.route('/abstract_generation')
def abstract_generation():
    response = urllib.request.urlopen('http://blender05.cs.rpi.edu:5000/index')
    return response.read()


@bp_abstract_generation.route('/baseline', methods=['POST'])
def baseline():
    data = request.get_json()['queryText'].strip()
    answer = requests.post('http://blender05.cs.rpi.edu:5000/baseline',
                           json={'queryText': data},
                           timeout=20
                           )
    return jsonify(json.loads(answer.text))


@bp_abstract_generation.route('/baselinet', methods=['POST'])
def generatet():
    data = request.get_json()['queryText'].strip()
    answer = requests.post('http://blender05.cs.rpi.edu:5000/baselinet',
                           json={'queryText': data},
                           timeout=20
                           )
    return jsonify(json.loads(answer.text))


@bp_abstract_generation.route('/baselinepre', methods=['GET', 'POST'])
def generatepre():
    data = request.get_json()['queryText'].strip()
    index = request.get_json()['index']
    answer = requests.post('http://blender05.cs.rpi.edu:5000/baselinepre',
                           json={'queryText': data, 'index': index},
                           timeout=20
                           )
    return jsonify(json.loads(answer.text))


@bp_abstract_generation.route('/baselinepret', methods=['GET', 'POST'])
def generatepret():
    data = request.get_json()['queryText'].strip()
    index = request.get_json()['index']
    answer = requests.post('http://blender05.cs.rpi.edu:5000/baselinepret',
                           json={'queryText': data, 'index': index},
                           timeout=20
                           )
    return jsonify(json.loads(answer.text))


@bp_abstract_generation.route('/seq2seq', methods=['POST'])
def generateseq():
    data = request.get_json()['queryText'].strip()
    answer = requests.post('http://blender05.cs.rpi.edu:5000/seq2seq',
                           json={'queryText': data},
                           timeout=30
                           )
    return jsonify(json.loads(answer.text))


@bp_abstract_generation.route('/seq2seqpre', methods=['GET', 'POST'])
def generateseqt():
    data = request.get_json()['queryText'].strip()
    index = request.get_json()['index']
    answer = requests.post('http://blender05.cs.rpi.edu:5000/seq2seqpre',
                           json={'queryText': data, 'index': index},
                           timeout=30
                           )
    return jsonify(json.loads(answer.text))