import os
from dotenv import load_dotenv
from cachelib.file import FileSystemCache # Import FileSystemCache at module level

# Ensure .env is loaded right at the start
basedir = os.path.abspath(os.path.dirname(__file__))
dotenv_path = os.path.join(basedir, '.env')

if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
elif os.environ.get('CI'):
    print(f"Info: .env file not found at {dotenv_path}, but assuming CI environment where vars are set directly.")
else:
    print(f"Warning: .env file not found at {dotenv_path}. Using default configurations or actual environment variables if set.")


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'

    DATABASE_URL_ENV = os.environ.get('DATABASE_URL')

    if DATABASE_URL_ENV and DATABASE_URL_ENV.startswith('sqlite:///'):
        db_filename = DATABASE_URL_ENV.split('///')[1]
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, db_filename)
    elif DATABASE_URL_ENV:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL_ENV
    else:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app_fallback.db')

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'super-secret'

    # Flask-Session configuration using CacheLib
    SESSION_TYPE = 'cachelib' # Explicitly set to use CacheLib
    SESSION_CACHELIB = FileSystemCache( # Initialize the cache instance directly
        cache_dir=os.path.join(basedir, 'instance', 'flask_session'),
        threshold=500,
        default_timeout=300
    )

    # Azure AD SSO Configuration
    AZURE_AD_CLIENT_ID = os.environ.get('AZURE_AD_CLIENT_ID')
    AZURE_AD_CLIENT_SECRET = os.environ.get('AZURE_AD_CLIENT_SECRET')
    AZURE_AD_TENANT_ID = os.environ.get('AZURE_AD_TENANT_ID')
    AZURE_AD_SCOPES = os.environ.get('AZURE_AD_SCOPES', 'User.Read openid profile email').split()

    _azure_tenant_id = os.environ.get('AZURE_AD_TENANT_ID')
    if _azure_tenant_id:
        AZURE_AD_AUTHORITY = f"https://login.microsoftonline.com/{_azure_tenant_id}"
    else:
        AZURE_AD_AUTHORITY = None
        print("Warning: AZURE_AD_TENANT_ID not set. AZURE_AD_AUTHORITY will be None.")
