"""
TOAD

I am a package supporting the Tool for Organization and Analysis of DNA (TOAD).
version = "0.1.0"
"""
from flask import Flask
from flask_cors import CORS
from flask_pymongo import PyMongo

from toad.config import Config

FRONTEND_URL = 'http://localhost:5173'

mongo = PyMongo()


def after_request(response):
    response.headers['Access-Control-Allow-Origin'] = FRONTEND_URL
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods',
                         'GET, POST, PUT, OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response


def handle_http_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    # from https://flask.palletsprojects.com/en/2.3.x/errorhandling/#generic-exception-handlers
    # start with the correct headers and status code from the error
    import json
    traceback.print_exc()  # provide what went wrong in the server side log as well
    response = e.get_response()
    # replace the body with JSON
    response.data = json.dumps({
        "code": e.code,
        "name": e.name,
        "description": e.description,
    })
    response.content_type = "application/json"
    return response


def create_app(config_class=Config):
    '''
    Creating the app
    '''
    app = Flask(__name__)
    app.config.from_object(config_class)
    CORS(app, resources={r'/api/v*': {'origins': FRONTEND_URL}})
    app.after_request(after_request)

    mongo.init_app(app)

    from toad.api.amplicon import api_amplicon
    app.register_blueprint(api_amplicon)

    from toad.routes import main
    app.register_blueprint(main)

    from toad.api.lib.dn_exceptions import DBInsertException, RequestValidationException
    app.register_error_handler(
        RequestValidationException, handle_http_exception)
    app.register_error_handler(DBInsertException, handle_http_exception)

    return app
