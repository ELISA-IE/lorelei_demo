import os
import json
from flask import Flask, render_template, jsonify, Blueprint
from random import uniform, choice
from lorelei_demo.app import lorelei_demo_dir, app


bp_heatmap = Blueprint('heatmap', __name__)

DATA_PATH = os.path.join(lorelei_demo_dir, 'data/app/heatmap/data_set.json')
RANDOM_FACTOR = .8
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 1


@bp_heatmap.route('/elisa_ie/heatmap')
def demo():
    return render_template('heatmap.html')

features = []
topics = ['Food Supply', 'Water Supply', 'Medical Assistance', 'Terrorism or other Extreme Violence', 'Utilities, Energy, or Sanitation', 'Evacuation', 'Shelter', 'Search and Rescue', 'Civil Unrest or Wide-spread Crime', 'Infrastructure']


@bp_heatmap.route('/elisa_ie/heatmap/data')
def get_data():
    if features:
        return jsonify({
            'type': 'FeatureCollection',
            'features': features
        })
    else:
        data = json.load(open(DATA_PATH, 'r', encoding='utf-8'))
        languages = set()
        for loc, item in data.items():
            latitude = float(item['center']['lat'])
            longitude = float(item['center']['lng'])
            sentence = item['sentence']
            topic = item['topic']
            incident = item['incident']
            language = item['language']
            translation = item['translation'] if 'translation' in item else ''
            languages.add(language)
            if topic == 'Noclass':
                continue
            features.append({
                'type': 'Feature',
                'properties': {
                    'location': loc,
                    'sentence': sentence,
                    'topic': topic,
                    'incident': incident,
                    'language': language,
                    'translation': translation
                },
                'geometry': {
                    'type': 'Point',
                    'coordinates': [longitude + RANDOM_FACTOR * uniform(-1, 1) * uniform(-1, 1),
                                    latitude + RANDOM_FACTOR * uniform(-1, 1) * uniform(-1, 1)]
                }
            })
        print(languages)
        return jsonify({
            'type': 'FeatureCollection',
            'features': features
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9997, debug=True, threaded=True)
