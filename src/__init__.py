from flask import Flask
from .config import Config  # Note the relative import

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Register blueprints
    from .routes import main  # Note the relative import
    app.register_blueprint(main)

    return app

# Make create_app available when importing from src
__all__ = ['create_app']