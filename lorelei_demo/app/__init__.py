from argparse import ArgumentParser

parser = ArgumentParser()
# name tagger options
parser.add_argument('--preload',  default=False, action="store_true",
                    help="preload name tagger models")
parser.add_argument('--debug',  default=False, action="store_true",
                    help="run demo app with debug option")

# parse arguments
args = parser.parse_args()

#
# Import flask
#
from flask import Flask
from flask_cors import CORS

#
# Define the WSGI application object
#
app = Flask(__name__)

#
# Cross Origin Resource Sharing(CORS) is required by SWAGGER API
#
CORS(app)


#
# get elisa_ie root path
#
import os
import lorelei_demo
lorelei_demo_dir = os.path.join(os.path.dirname(lorelei_demo.__file__), '../')

#
# preload name tagger models
#
# todo

#
# register blueprint modules
#
# import app modules
from lorelei_demo.app.api import bp_api
from lorelei_demo.app.heatmap import bp_heatmap
from lorelei_demo.app.elisa_ie import bp_elisa_ie
# register app modules
app.register_blueprint(bp_api)
app.register_blueprint(bp_heatmap)
app.register_blueprint(bp_elisa_ie)

