import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-dev-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY') or ''
