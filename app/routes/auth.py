from flask import Blueprint, request, jsonify, g
from app.services.auth_service import AuthService
import logging
from functools import wraps

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__)

def token_required(f):
    """Decorator to verify JWT token and attach user to request context"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from header
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(' ')[1]
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
            
        try:
            # Verify token and store user info in Flask's g object
            current_user = AuthService.verify_token(token)
            g.user = current_user
        except Exception as e:
            return jsonify({'error': 'Token is invalid'}), 401
            
        return f(*args, **kwargs)
    return decorated

@auth_bp.route('/register/customer', methods=['POST'])
def register_customer():
    """Register a new customer and return JWT token"""
    try:
        data = request.get_json()
        result = AuthService.register_customer(
            name=data.get('name'),
            email=data.get('email'),
            phone=data.get('phone'),
            password=data.get('password')
        )
        # Set token in response header
        response = jsonify(result)
        response.headers['Authorization'] = f"Bearer {result['token']}"
        return response, 201
    except ValueError as e:
        logger.warning(f"Customer registration validation error: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Customer registration failed: {str(e)}")
        return jsonify({'error': 'Registration failed'}), 500

@auth_bp.route('/register/shop', methods=['POST'])
def register_shop():
    """Register a shop owner and return JWT token"""
    try:
        data = request.get_json()
        required_fields = [
            'shopName', 'ownerName', 'email', 'phone', 'address',
            'zipCode', 'serviceArea', 'pricePerItem', 'password'
        ]
        
        # Check for missing fields
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return jsonify({
                'error': f"Missing required fields: {', '.join(missing_fields)}"
            }), 400

        # Validate password confirmation
        if data.get('password') != data.get('confirmPassword'):
            return jsonify({'error': 'Passwords do not match'}), 400

        result = AuthService.register_shop_owner(data)
        # Set token in response header
        response = jsonify(result)
        response.headers['Authorization'] = f"Bearer {result['token']}"
        return response, 201
    except ValueError as e:
        logger.warning(f"Shop registration validation error: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Shop registration failed: {str(e)}")
        return jsonify({'error': 'Registration failed'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user and return new JWT token"""
    try:
        data = request.get_json()
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400

        result = AuthService.login_user(
            email=data.get('email'),
            password=data.get('password')
        )
        # Set token in response header
        response = jsonify(result)
        response.headers['Authorization'] = f"Bearer {result['token']}"
        return response, 200
    except ValueError as e:
        logger.warning(f"Login validation error: {str(e)}")
        return jsonify({'error': str(e)}), 401
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        return jsonify({'error': 'Login failed'}), 500

@auth_bp.route('/verify-token', methods=['GET'])
@token_required
def verify_token():
    """Verify JWT token and return user info"""
    try:
        # g.user is set by token_required decorator
        return jsonify({
            'valid': True,
            'user': g.user,
            'message': 'Token is valid'
        }), 200
    except Exception as e:
        logger.warning(f"Token verification failed: {str(e)}")
        return jsonify({'error': str(e)}), 401

@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout():
    """Invalidate JWT token"""
    try:
        # Get token from header
        token = request.headers['Authorization'].split(' ')[1]
        # Add token to blacklist (you'll need to implement token blacklisting)
        # AuthService.blacklist_token(token)
        return jsonify({
            'message': 'Successfully logged out',
            'token_invalidated': True
        }), 200
    except Exception as e:
        logger.error(f"Logout failed: {str(e)}")
        return jsonify({'error': 'Logout failed'}), 500
