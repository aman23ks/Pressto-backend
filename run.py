from app import create_app

app = create_app()

# def setup_indexes():
    # Create geospatial index for shop locations
    # mongo.db.shops.create_index([("location", "2dsphere")])
    
    # # Create indexes for common queries
    # mongo.db.users.create_index("email", unique=True)
    # mongo.db.orders.create_index([("customer_id", 1), ("created_at", -1)])
    # mongo.db.orders.create_index([("shop_id", 1), ("created_at", -1)])
    # mongo.db.orders.create_index([("status", 1)])

if __name__ == '__main__':
    # with app.app_context():
        # setup_indexes()
    app.run()