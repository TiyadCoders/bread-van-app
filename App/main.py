import os
from flask import Flask, render_template
import json, pathlib
from werkzeug.utils import secure_filename
from werkzeug.datastructures import  FileStorage

from App.extensions import init_extensions, jwt
from App.config import load_config
from App.views import views, setup_admin

def add_views(app):
    for view in views:
        app.register_blueprint(view)

def create_app(overrides={}):
    app = Flask(__name__, static_url_path='/static')
    load_config(app, overrides)

    # Initialize all extensions
    init_extensions(app)

    # Register blueprints
    add_views(app)

    # Setup admin
    setup_admin(app)

    # JWT error handlers
    @jwt.invalid_token_loader
    @jwt.unauthorized_loader
    def custom_unauthorized_response(error):
        return render_template('401.html', error=error), 401

    app.app_context().push()
    return app
