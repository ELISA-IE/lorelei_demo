from lorelei_demo.app import app
from lorelei_demo.app import args


app.run('0.0.0.0', port=args.port, threaded=True, debug=args.debug)
