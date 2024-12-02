import jwt
import bcrypt
import logging
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from flask import current_app
from .. import db
from ..utils.helpers import validate_email, validate_password, validate_phone

logger = logging.getLogger(__name__)

class AuthService:
    @staticmethod
    def generate_token(user_id, user_type):
        """Generate JWT token for authenticated user"""
        payload = {
            'user_id': str(user_id),
            'user_type': user_type,
            'exp': datetime.utcnow() + timedelta(days=1)
        }
        return jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_token(token):
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            raise Exception('Token has expired')
        except jwt.InvalidTokenError:
            raise Exception('Invalid token')

    @staticmethod
    def hash_password(password):
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    @staticmethod
    def check_password(password, hashed):
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed)

    @classmethod
    def register_customer(cls, name, email, phone, password):
        """Register a new customer"""
        try:
            # Validate input
            if not all([name, email, phone, password]):
                raise ValueError('All fields are required')
            
            if not validate_email(email):
                raise ValueError('Invalid email format')
                
            if not validate_phone(phone):
                raise ValueError('Invalid phone format')
                
            if not validate_password(password):
                raise ValueError('Password must be at least 8 characters and contain a number')

            # Check if user exists
            if db.users.find_one({'email': email}):
                raise ValueError('Email already registered')

            # Create user
            user = {
                'name': name,
                'email': email,
                'phone': phone,
                'password_hash': cls.hash_password(password),
                'user_type': 'customer',
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }

            result = db.users.insert_one(user)
            user['_id'] = result.inserted_id

            # Generate token
            token = cls.generate_token(user['_id'], 'customer')

            return {
                'token': token,
                'user': {
                    'id': str(user['_id']),
                    'name': user['name'],
                    'email': user['email'],
                    'user_type': 'customer'
                }
            }

        except Exception as e:
            logger.error(f"Error in register_customer: {str(e)}")
            raise

    @classmethod
    def register_shop_owner(cls, shop_data):
        """Register a shop owner with shop details"""
        try:
            # Validate required fields
            required_fields = {
                'shopName': 'Shop name',
                'ownerName': 'Owner name',
                'email': 'Email',
                'phone': 'Phone number',
                'address': 'Shop address',
                'zipCode': 'ZIP code',
                'serviceArea': 'Service area',
                'pricePerItem': 'Price per item',
                'password': 'Password'
            }

            # Check for missing fields
            for field, label in required_fields.items():
                if not shop_data.get(field):
                    raise ValueError(f'{label} is required')

            # Validate email and phone
            if not validate_email(shop_data['email']):
                raise ValueError('Invalid email format')
            
            if not validate_phone(shop_data['phone']):
                raise ValueError('Invalid phone format')
            
            if not validate_password(shop_data['password']):
                raise ValueError('Password must be at least 8 characters and contain a number')

            # Check if user/shop already exists
            if db.users.find_one({'email': shop_data['email']}):
                raise ValueError('Email already registered')
            
            if db.shops.find_one({'name': shop_data['shopName']}):
                raise ValueError('Shop name already exists')

            # Create user document
            user = {
                'name': shop_data['ownerName'],
                'email': shop_data['email'],
                'phone': shop_data['phone'],
                'password_hash': cls.hash_password(shop_data['password']),
                'user_type': 'shopOwner',
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }

            # Insert user and get ID
            user_result = db.users.insert_one(user)
            user_id = user_result.inserted_id

            # Create shop document
            shop = {
                'owner_id': user_id,
                'name': shop_data['shopName'],
                'address': shop_data['address'],
                'zip_code': shop_data['zipCode'],
                'service_area': float(shop_data['serviceArea']),
                'price_per_item': float(shop_data['pricePerItem']),
                'status': 'active',
                'rating': 0,
                'total_orders': 0,
                'business_hours': {
                    'monday': {'open': '09:00', 'close': '18:00'},
                    'tuesday': {'open': '09:00', 'close': '18:00'},
                    'wednesday': {'open': '09:00', 'close': '18:00'},
                    'thursday': {'open': '09:00', 'close': '18:00'},
                    'friday': {'open': '09:00', 'close': '18:00'},
                    'saturday': {'open': '09:00', 'close': '18:00'},
                    'sunday': 'closed'
                },
                'location': {
                    'type': 'Point',
                    'coordinates': [0, 0]  # Will be updated later with geocoding
                },
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }

            # Insert shop
            shop_result = db.shops.insert_one(shop)

            # Generate token
            token = cls.generate_token(user_id, 'shopOwner')

            return {
                'token': token,
                'user': {
                    'id': str(user_id),
                    'name': shop_data['ownerName'],
                    'email': shop_data['email'],
                    'user_type': 'shopOwner',
                    'shop_id': str(shop_result.inserted_id)
                }
            }

        except ValueError as e:
            logger.error(f"Validation error in register_shop_owner: {str(e)}")
            # Rollback if user was created but shop creation failed
            if 'user_id' in locals():
                db.users.delete_one({'_id': user_id})
            raise
        except Exception as e:
            logger.error(f"Error in register_shop_owner: {str(e)}")
            if 'user_id' in locals():
                db.users.delete_one({'_id': user_id})
            raise ValueError(f'Shop registration failed: {str(e)}')

    @classmethod
    def login_user(cls, email, password):
        """Login user with email and password"""
        try:
            user = db.users.find_one({'email': email})
            
            if not user:
                raise ValueError('Invalid email or password')

            if not cls.check_password(password, user['password_hash']):
                raise ValueError('Invalid email or password')

            # Get shop details if user is shop owner
            shop_data = None
            if user['user_type'] == 'shopOwner':
                shop = db.shops.find_one({'owner_id': user['_id']})
                if shop:
                    shop_data = {
                        'shop_id': str(shop['_id']),
                        'shop_name': shop['name']
                    }

            token = cls.generate_token(user['_id'], user['user_type'])

            response = {
                'token': token,
                'user': {
                    'id': str(user['_id']),
                    'name': user['name'],
                    'email': user['email'],
                    'user_type': user['user_type']
                }
            }

            if shop_data:
                response['user']['shop'] = shop_data

            return response

        except Exception as e:
            logger.error(f"Error in login_user: {str(e)}")
            raise

    @classmethod
    def forgot_password(cls, email):
        """Initiate forgot password process"""
        try:
            user = db.users.find_one({'email': email})
            if not user:
                raise ValueError('Email not found')

            # Generate reset token (valid for 1 hour)
            reset_token = jwt.encode(
                {
                    'user_id': str(user['_id']),
                    'exp': datetime.utcnow() + timedelta(hours=1)
                },
                current_app.config['JWT_SECRET_KEY'],
                algorithm='HS256'
            )

            # Store reset token
            db.users.update_one(
                {'_id': user['_id']},
                {
                    '$set': {
                        'reset_token': reset_token,
                        'reset_token_exp': datetime.utcnow() + timedelta(hours=1)
                    }
                }
            )

            # In production, send email with reset link
            # For now, just return the token
            return {'reset_token': reset_token}

        except Exception as e:
            logger.error(f"Error in forgot_password: {str(e)}")
            raise

    @classmethod
    def reset_password(cls, reset_token, new_password):
        """Reset password using reset token"""
        try:
            # Verify token
            payload = jwt.decode(
                reset_token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=['HS256']
            )

            user = db.users.find_one({
                '_id': ObjectId(payload['user_id']),
                'reset_token': reset_token,
                'reset_token_exp': {'$gt': datetime.utcnow()}
            })

            if not user:
                raise ValueError('Invalid or expired reset token')

            # Update password
            db.users.update_one(
                {'_id': user['_id']},
                {
                    '$set': {
                        'password_hash': cls.hash_password(new_password),
                        'updated_at': datetime.utcnow()
                    },
                    '$unset': {
                        'reset_token': '',
                        'reset_token_exp': ''
                    }
                }
            )

            return {'message': 'Password reset successful'}

        except Exception as e:
            logger.error(f"Error in reset_password: {str(e)}")
            raise