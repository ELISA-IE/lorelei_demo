from lorelei_demo.app import app
from lorelei_demo.app import args


app.run('0.0.0.0', port=3300, threaded=True, debug=args.debug)
