import sys
import os
import traceback

# Add project root to sys.path so app.py is importable
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

class VercelPathFixerMiddleware:
    """
    Ensures Flask receives the exact requested path even when Vercel rewrites
    the request to /api/index or /api/index.py.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        matched_path = (
            environ.get('HTTP_X_VERCEL_MATCHED_PATH')
            or environ.get('HTTP_X_NOW_PATHNAME')
            or environ.get('PATH_INFO')
        )
        if matched_path:
            environ['PATH_INFO'] = matched_path
            environ['SCRIPT_NAME'] = ''
        return self.wsgi_app(environ, start_response)

try:
    from app import app
    app.wsgi_app = VercelPathFixerMiddleware(app.wsgi_app)
except Exception as e:
    err_tb = traceback.format_exc()
    print("FATAL FLASK APP IMPORT ERROR ON VERCEL:\n" + err_tb, file=sys.stderr)
    from flask import Flask, jsonify, make_response
    app = Flask(__name__)

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def fallback_handler(path):
        return make_response(jsonify({
            "error": "Serverless Function Startup Error",
            "message": str(e),
            "traceback": err_tb
        }), 500)
