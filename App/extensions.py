from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_uploads import UploadSet, DOCUMENTS, IMAGES, TEXT, configure_uploads
from flask_cors import CORS

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def init_extensions(app):
    """Initialize Flask extensions with the app instance."""
    # Database
    db.init_app(app)
    migrate.init_app(app, db)

    # CORS
    CORS(app)

    # File uploads
    photos = UploadSet('photos', TEXT + DOCUMENTS + IMAGES)
    configure_uploads(app, photos)

    # JWT
    jwt.init_app(app)

    # JWT configuration
    from App.controllers.auth import setup_jwt_handlers, add_auth_context
    setup_jwt_handlers(jwt)
    add_auth_context(app)

    return app
