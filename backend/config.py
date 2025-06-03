import os
from dotenv import load_dotenv

# Ensure .env is loaded right at the start
basedir = os.path.abspath(os.path.dirname(__file__))
dotenv_path = os.path.join(basedir, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    # This else block can be used for logging or raising an error if .env is critical
    print(f"Warning: .env file not found at {dotenv_path}. Using default configurations or environment variables.")


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'

    DATABASE_URL_ENV = os.environ.get('DATABASE_URL')

    if DATABASE_URL_ENV and DATABASE_URL_ENV.startswith('sqlite:///'):
        # Treat the part after 'sqlite:///' as a filename relative to basedir
        db_filename = DATABASE_URL_ENV.split('///')[1]
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, db_filename)
    elif DATABASE_URL_ENV:
        # For non-sqlite URLs or absolute sqlite paths already defined in .env
        SQLALCHEMY_DATABASE_URI = DATABASE_URL_ENV
    else:
        # Fallback if DATABASE_URL is not in .env or is empty
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app_fallback.db') # Changed default name for clarity

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'super-secret'
