from datetime import datetime
from bson import ObjectId
from .. import db

class CustomerService:
    @staticmethod
    def get_profile(customer_id):
        customer = db.users.find_one(
            {'_id': ObjectId(customer_id)},
            {'password_hash': 0}  # Exclude password hash
        )
        if not customer:
            raise ValueError('Customer not found')
        return customer

    @staticmethod
    def update_profile(customer_id, profile_data):
        allowed_updates = ['name', 'phone']
        update_data = {
            'updated_at': datetime.utcnow()
        }
        
        for field in allowed_updates:
            if field in profile_data:
                update_data[field] = profile_data[field]

        result = db.users.update_one(
            {'_id': ObjectId(customer_id)},
            {'$set': update_data}
        )
        
        if result.modified_count == 0:
            raise ValueError('Customer not found')
        return True

    @staticmethod
    def add_address(customer_id, address_data):
        required_fields = ['street', 'city', 'state', 'pincode']
        for field in required_fields:
            if field not in address_data:
                raise ValueError(f'{field} is required')

        address = {
            '_id': ObjectId(),
            **address_data,
            'created_at': datetime.utcnow()
        }

        db.users.update_one(
            {'_id': ObjectId(customer_id)},
            {'$push': {'addresses': address}}
        )
        return str(address['_id'])

    @staticmethod
    def get_addresses(customer_id):
        customer = db.users.find_one(
            {'_id': ObjectId(customer_id)},
            {'addresses': 1}
        )
        return customer.get('addresses', []) if customer else []

    @staticmethod
    def delete_address(customer_id, address_id):
        result = db.users.update_one(
            {'_id': ObjectId(customer_id)},
            {'$pull': {'addresses': {'_id': ObjectId(address_id)}}}
        )
        if result.modified_count == 0:
            raise ValueError('Address not found')
        return True

    @staticmethod
    def get_order_history(customer_id):
        orders = list(db.orders.aggregate([
            {'$match': {'customer_id': ObjectId(customer_id)}},
            {'$lookup': {
                'from': 'shops',
                'localField': 'shop_id',
                'foreignField': '_id',
                'as': 'shop'
            }},
            {'$unwind': '$shop'},
            {'$sort': {'created_at': -1}},
            {'$project': {
                'id': {'$toString': '$_id'},
                'shop_name': '$shop.name',
                'status': 1,
                'total_amount': 1,
                'created_at': 1,
                'items': 1
            }}
        ]))
        return orders

    @staticmethod
    def get_order_by_status(current_user, order_type=None):
            pipeline = [
                {
                    '$match': {
                        'customer_id': ObjectId(current_user['user_id'])
                    }
                },
                {
                    '$lookup': {
                        'from': 'shops',
                        'localField': 'shop_id',
                        'foreignField': '_id',
                        'as': 'shop'
                    }
                },
                {
                    '$unwind': '$shop'
                },
                {
                    '$sort': {'created_at': -1}
                },
                {
                    '$project': {
                        'id': {'$toString': '$_id'},
                        'shopName': '$shop.name',
                        'items': 1,
                        'status': 1,
                        'pickup_date': 1,
                        'total_amount': 1,
                        'created_at': 1,
                        'pickup_address': 1
                    }
                }
            ]

            orders = list(db.orders.aggregate(pipeline))
            return orders