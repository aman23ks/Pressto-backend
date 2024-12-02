from functools import wraps
from flask import request, jsonify
from app.services.auth_service import AuthService

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'No authorization header'}), 401
        
        try:
            token = auth_header.split(' ')[1]
            user = AuthService.verify_token(token)
            return f(user, *args, **kwargs)
        except Exception as e:
            return jsonify({'error': str(e)}), 401
            
    return decorated_function

def shop_owner_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'No authorization header'}), 401
        
        try:
            token = auth_header.split(' ')[1]
            user = AuthService.verify_token(token)
            if user['user_type'] != 'shopOwner':
                return jsonify({'error': 'Shop owner access required'}), 403
            return f(user, *args, **kwargs)
        except Exception as e:
            return jsonify({'error': str(e)}), 401
            
    return decorated_function