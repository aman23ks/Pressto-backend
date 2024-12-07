from datetime import datetime
from bson import ObjectId
from .. import db
from app.models.order import Order

class OrderService:
    @staticmethod
    def create_order(customer_id, shop_id, items, pickup_date, 
                    pickup_address, special_instructions=None, total_amount=None):
        # Get shop details for price calculation
        shop = db.shops.find_one({'_id': ObjectId(shop_id)})
        if not shop:
            raise ValueError('Shop not found')

        # Calculate total amount
        order = {
            'customer_id': ObjectId(customer_id),
            'shop_id': ObjectId(shop_id),
            'items': items,
            'pickup_date': pickup_date,
            # 'pickup_time': pickup_time,
            # 'delivery_time': delivery_time,
            'status': 'pending',
            'total_amount': total_amount,
            'pickup_address': pickup_address,
            'special_instructions': special_instructions,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }

        result = db.orders.insert_one(order)
        
        # Update shop's total orders
        db.shops.update_one(
            {'_id': ObjectId(shop_id)},
            {'$inc': {'total_orders': 1}}
        )

        return str(result.inserted_id)

    @staticmethod
    def get_customer_orders(customer_id, status=None):
        query = {'customer_id': ObjectId(customer_id)}
        if status:
            query['status'] = status

        orders = list(db.orders.aggregate([
            {'$match': query},
            {'$lookup': {
                'from': 'shops',
                'localField': 'shop_id',
                'foreignField': '_id',
                'as': 'shop'
            }},
            {'$unwind': '$shop'},
            {'$project': {
                'id': {'$toString': '$_id'},
                'items': 1,
                'status': 1,
                'total_amount': 1,
                'pickup_date': 1,
                # 'pickup_time': 1,
                # 'delivery_time': 1,
                'shop_name': '$shop.name',
                'shop_contact': '$shop.contact_info',
                'created_at': 1
            }}
        ]))

        return orders

    @staticmethod
    def get_shop_orders(shop_id, status=None):
        query = {'shop_id': ObjectId(shop_id)}
        if status:
            query['status'] = status

        orders = list(db.orders.aggregate([
            {'$match': query},
            {'$lookup': {
                'from': 'users',
                'localField': 'customer_id',
                'foreignField': '_id',
                'as': 'customer'
            }},
            {'$unwind': '$customer'},
            {'$project': {
                'id': {'$toString': '$_id'},
                'items': 1,
                'status': 1,
                'total_amount': 1,
                'pickup_time': 1,
                'delivery_time': 1,
                'customer_name': '$customer.name',
                'customer_phone': '$customer.phone',
                'pickup_address': 1,
                'special_instructions': 1,
                'created_at': 1
            }}
        ]))

        return orders

    @staticmethod
    def update_order_status(order_id, new_status, user_id, user_type):
        order = db.orders.find_one({'_id': ObjectId(order_id)})
        if not order:
            raise ValueError('Order not found')

        # Verify user has permission to update
        if user_type == 'customer' and str(order['customer_id']) != user_id:
            raise ValueError('Not authorized to update this order')
        elif user_type == 'shopOwner' and str(order['shop_id']) != user_id:
            raise ValueError('Not authorized to update this order')

        # Update order status
        db.orders.update_one(
            {'_id': ObjectId(order_id)},
            {
                '$set': {
                    'status': new_status,
                    'updated_at': datetime.utcnow()
                }
            }
        )

        return True

    @staticmethod
    def get_order_details(order_id, user_id, user_type):
        order = db.orders.find_one({'_id': ObjectId(order_id)})
        if not order:
            raise ValueError('Order not found')

        # Verify user has permission to view
        if user_type == 'customer' and str(order['customer_id']) != user_id:
            raise ValueError('Not authorized to view this order')
        elif user_type == 'shopOwner' and str(order['shop_id']) != user_id:
            raise ValueError('Not authorized to view this order')

        return order