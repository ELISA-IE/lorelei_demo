from argparse import ArgumentParser

parser = ArgumentParser()
# name tagger options
parser.add_argument('--preload',  default=False, action="store_true",
                    help="preload name tagger models")
parser.add_argument('--debug',  default=False, action="store_true",
                    help="run demo app with debug option")
parser.add_argument('--port', default=3300, type=int,
                    help='the port the demo runs on')
parser.add_argument('--in_domain', default=False, action="store_true",
                    help="if the image runs in RPI's network")

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
# set theano flags
#
os.environ["THEANO_FLAGS"] = "optimizer=fast_compile,floatX=float32"

#
# preload name tagger models
#
from lorelei_demo.app.model_preload import pytorch_preload
from lorelei_demo.app.api import get_status
if args.preload:
    models = pytorch_preload(get_status())
else:
    models = {}

#
# register blueprint modules
#
# import app modules
from lorelei_demo.app.api import bp_api
from lorelei_demo.app.heatmap import bp_heatmap
from lorelei_demo.app.elisa_ie import bp_elisa_ie
from lorelei_demo.app.misc.abstract_generation import bp_abstract_generation
# register app modules
app.register_blueprint(bp_api)
app.register_blueprint(bp_heatmap)
app.register_blueprint(bp_elisa_ie)
app.register_blueprint(bp_abstract_generation)

