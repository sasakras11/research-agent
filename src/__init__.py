import os
from flask import Flask
import logging
from .config import Config  # Note the relative import

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    
    # Configure logging
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'sdr_researcher.sqlite'),
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import db
    db.init_app(app)

    from .routes import main  # Note the relative import
    app.register_blueprint(main)

    return app

# Make create_app available when importing from src
__all__ = ['create_app']