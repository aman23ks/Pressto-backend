from datetime import datetime
from bson import ObjectId
from .. import db
from app.models.order import Order

class OrderService:
    VALID_STATUSES = [
        'pending', 'accepted', 'pickedUp', 'inProgress', 
        'completed', 'delivered', 'cancelled'
    ]

    STATUS_TRANSITIONS = {
        'pending': ['accepted', 'cancelled'],
        'accepted': ['pickedUp', 'cancelled'],
        'pickedUp': ['inProgress', 'cancelled'],
        'inProgress': ['completed', 'cancelled'],
        'completed': ['delivered'],
        'delivered': [],
        'cancelled': []
    }

    @staticmethod
    def create_order(customer_id, shop_id, items, pickup_date, 
                    pickup_address, special_instructions=None, total_amount=None):
        try:
            shop = db.shops.find_one({'_id': ObjectId(shop_id)})
            if not shop:
                raise ValueError('Shop not found')

            order = {
                'customer_id': ObjectId(customer_id),
                'shop_id': ObjectId(shop_id),
                'items': items,
                'pickup_date': pickup_date,
                'status': 'pending',
                'total_amount': total_amount,
                'pickup_address': pickup_address,
                'special_instructions': special_instructions,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }

            result = db.orders.insert_one(order)
            db.shops.update_one(
            {'_id': ObjectId(shop_id)},
            {'$inc': {'total_orders': 1}}
        )
            return str(result.inserted_id)
        except Exception as e:
            raise Exception(f"Failed to create order: {str(e)}")

    
    @staticmethod
    def update_order_status(order_id, new_status, user_id, user_type):
        if new_status not in OrderService.VALID_STATUSES:
            raise ValueError(
                f"Invalid status. Must be one of {', '.join(OrderService.VALID_STATUSES)}"
            )

        order = db.orders.find_one({'_id': ObjectId(order_id)})
        if not order:
            raise ValueError('Order not found')

        current_status = order['status']
        if new_status not in OrderService.STATUS_TRANSITIONS.get(current_status, []):
            raise ValueError(f"Cannot transition from {current_status} to {new_status}")

        # Verify authorization
        if user_type == 'customer':
            if str(order['customer_id']) != user_id:
                raise ValueError('Not authorized to update this order')
        elif user_type == 'shopOwner':
            shop = db.shops.find_one({'owner_id': ObjectId(user_id)})
            if not shop or str(order['shop_id']) != str(shop['_id']):
                raise ValueError('Not authorized to update this order')

        result = db.orders.update_one(
            {'_id': ObjectId(order_id)},
            {
                '$set': {
                    'status': new_status,
                    'updated_at': datetime.utcnow()
                }
            }
        )

        if result.modified_count == 0:
            raise ValueError('Failed to update order status')

        return True

    @staticmethod
    def get_customer_orders(customer_id, order_type='active'):
        status_map = {
            'active': ['pending', 'accepted', 'pickedUp', 'inProgress', 'completed'],
            'history': ['delivered', 'cancelled']
        }
        
        statuses = status_map.get(order_type, status_map['active'])
        
        pipeline = [
            {
                '$match': {
                    'customer_id': ObjectId(customer_id),
                    'status': {'$in': statuses}
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