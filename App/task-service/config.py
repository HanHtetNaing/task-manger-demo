import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://dbadmin:SecurePassword123!@localhost/taskmanager'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    JWT_SECRET = os.environ.get('JWT_SECRET') or 'your-secret-key'
    USER_SERVICE_URL = os.environ.get('USER_SERVICE_URL') or 'http://user-service'
