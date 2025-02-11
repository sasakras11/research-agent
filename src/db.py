
import sqlite3
from flask import g

DATABASE = 'sdr_researcher.sqlite'  # Adjust if needed

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def init_app(app):
    with app.app_context():
        db = get_db()
        # Initialize database tables here if needed
        # db.execute("CREATE TABLE IF NOT EXISTS ...")
        db.commit()

    app.teardown_appcontext(close_db)

def close_db(e=None):
    db = g.pop('_database', None)
    if db is not None:
        db.close()