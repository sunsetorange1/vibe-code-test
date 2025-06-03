from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_session import Session # Import Session
from flask_dance.contrib.azure import make_azure_blueprint # Import make_azure_blueprint
from config import Config

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
sess = Session() # Create Session instance
# azure_bp is created and registered within create_app to access app.config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    sess.init_app(app) # Initialize Session with app

    # Create and register Flask-Dance blueprint for Azure AD
    # Ensure required configurations are present before creating blueprint
    if app.config.get("AZURE_AD_CLIENT_ID") and \
       app.config.get("AZURE_AD_CLIENT_SECRET") and \
       app.config.get("AZURE_AD_TENANT_ID"):
        azure_bp = make_azure_blueprint(
            client_id=app.config.get("AZURE_AD_CLIENT_ID"),
            client_secret=app.config.get("AZURE_AD_CLIENT_SECRET"),
            tenant=app.config.get("AZURE_AD_TENANT_ID"),
            scope=app.config.get("AZURE_AD_SCOPES"),
            redirect_to="auth.sso_azure_callback",
            # This route ('auth.sso_azure_callback') will be defined later.
            # It's the view function that Flask-Dance redirects to *after*
            # it has completed the OAuth dance with Azure AD and obtained tokens.
            # Flask-Dance handles /auth/sso/azure/login and /auth/sso/azure/authorized (callback from Azure)
        )
        app.register_blueprint(azure_bp, url_prefix="/auth/sso/azure")
    else:
        app.logger.warning("Azure AD SSO configuration missing. Skipping Azure SSO blueprint registration.")

    # Import models to ensure they are known to SQLAlchemy/Migrate
    # This should ideally be done carefully. If models define db.event listeners or something
    # that requires app context or db to be initialized, it might be tricky.
    # For simple models, it's usually fine.
    from . import models # Contains User model
    from . import project_models # Contains Project, Baseline, TaskDefinition, ProjectTask, Evidence

    from .auth_routes import auth_bp
    app.register_blueprint(auth_bp)

    from .api_routes import api_bp
    app.register_blueprint(api_bp)

    from .project_api_routes import project_api_bp
    app.register_blueprint(project_api_bp)

    from .baseline_api_routes import baseline_api_bp
    app.register_blueprint(baseline_api_bp)

    from .task_api_routes import task_api_bp
    app.register_blueprint(task_api_bp)

    from .evidence_api_routes import evidence_api_bp # Import evidence_api_bp
    app.register_blueprint(evidence_api_bp) # Register it

    # Simple health check route
    @app.route('/health')
    def health():
        return 'OK', 200

    return app
