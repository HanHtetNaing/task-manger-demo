import jwt
import requests
from functools import wraps
from flask import request, jsonify, current_app, g
from config import Config

def authenticate(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            auth_header = request.headers.get('Authorization')
            
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'error': 'Access token required'}), 401
            
            token = auth_header.split(' ')[1]
            decoded = jwt.decode(token, Config.JWT_SECRET, algorithms=['HS256'])
            
            g.current_user = decoded
            return f(*args, **kwargs)
            
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        except Exception as e:
            current_app.logger.error(f"Authentication error: {e}")
            return jsonify({'error': 'Authentication failed'}), 401
    
    return decorated_function

def get_current_user():
    return g.current_user