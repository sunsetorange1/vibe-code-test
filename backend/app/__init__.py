from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from config import Config

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
from .models import User # Import the User model
from .auth_routes import auth_bp # Import the auth blueprint
from .api_routes import api_bp # Import the api blueprint

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Register blueprints here
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)

    # Simple health check route
    @app.route('/health')
    def health():
        return 'OK', 200

    return app
