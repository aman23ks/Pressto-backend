from flask import Flask, request, Response
from pymongo import MongoClient
from flask_cors import CORS
from .config import Config
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)      

db = None

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    # Initialize extensions
    CORS(app)
    
    @app.before_request
    def before_authentication():
        if request.method.lower() == 'options':
            return Response()
    
    global db
    
    # Initialize MongoDB with the app instance, not the URI string
    try:
        client = MongoClient(app.config["MONGO_URI"])
        db = client.get_default_database()
        app.db = db
        logger.info("MongoDB connected successfully using pymongo.")
    except Exception as e:
        logger.error(f"Error initializing MongoDB: {e}")
        raise

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.customer import customer_bp
    from app.routes.shop import shop_bp
    from app.routes.order import orders_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(customer_bp, url_prefix='/api/customer')
    app.register_blueprint(shop_bp, url_prefix='/api/shop')
    app.register_blueprint(orders_bp, url_prefix='/api/orders')
    
    return app