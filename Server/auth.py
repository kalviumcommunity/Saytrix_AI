from flask import request, jsonify, current_app
from functools import wraps
import jwt
from datetime import datetime, timedelta
import os

class AuthManager:
    def __init__(self):
        self.secret_key = os.getenv('JWT_SECRET_KEY')
        if not self.secret_key:
            raise ValueError('JWT_SECRET_KEY environment variable is required')
    
    def generate_token(self, user_id: str) -> str:
        """Generate JWT token for user"""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(days=7),  # 7 day expiry
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_token(self, token: str) -> dict:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return {'valid': True, 'user_id': payload['user_id']}
        except jwt.ExpiredSignatureError:
            return {'valid': False, 'error': 'Token expired'}
        except jwt.InvalidTokenError:
            return {'valid': False, 'error': 'Invalid token'}

# Global auth manager
auth_manager = AuthManager()

def require_auth(f):
    """Decorator to require authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'No token provided'}), 401
        
        if token.startswith('Bearer '):
            token = token[7:]
        
        result = auth_manager.verify_token(token)
        if not result['valid']:
            return jsonify({'error': result['error']}), 401
        
        # Add user_id to request context
        request.user_id = result['user_id']
        return f(*args, **kwargs)
    
    return decorated_function