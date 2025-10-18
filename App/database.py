from App.extensions import db, migrate

def get_migrate(app):
    """Legacy function - migrate is now handled in extensions.py"""
    return migrate

def create_db():
    db.create_all()

def init_db(app):
    """Legacy function - db init is now handled in extensions.py"""
    db.init_app(app)
