from datetime import datetime
from bson import ObjectId
from .. import db
from app.utils.helpers import calculate_distance

class ShopService:
    @staticmethod
    def create_shop(owner_id, shop_data):
        # Validate required fields
        required_fields = ['name', 'address', 'location', 'service_area', 
                         'price_per_item', 'business_hours', 'contact_info']
        for field in required_fields:
            if field not in shop_data:
                raise ValueError(f'{field} is required')

        shop = {
            'owner_id': ObjectId(owner_id),
            'name': shop_data['name'],
            'address': shop_data['address'],
            'location': shop_data['location'],
            'service_area': float(shop_data['service_area']),
            'price_per_item': float(shop_data['price_per_item']),
            'business_hours': shop_data['business_hours'],
            'contact_info': shop_data['contact_info'],
            'status': 'active',
            'rating': 0,
            'total_orders': 0,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }

        result = db.shops.insert_one(shop)
        return str(result.inserted_id)

    @staticmethod
    def update_shop(shop_id, owner_id, shop_data):
        # Verify shop ownership
        shop = db.shops.find_one({
            '_id': ObjectId(shop_id),
            'owner_id': ObjectId(owner_id)
        })

        if not shop:
            raise ValueError('Shop not found or unauthorized')

        # Update allowed fields
        allowed_updates = [
            'name', 'address', 'location', 'service_area', 
            'price_per_item', 'business_hours', 'contact_info', 'status'
        ]

        update_data = {
            'updated_at': datetime.utcnow()
        }

        for field in allowed_updates:
            if field in shop_data:
                update_data[field] = shop_data[field]
        
        db.shops.update_one(
            {'_id': ObjectId(shop_id)},
            {'$set': update_data}
        )
        return True

    @staticmethod
    def get_shop_details(shop_id):
        shop = db.shops.find_one({'_id': ObjectId(shop_id)})
        if not shop:
            raise ValueError('Shop not found')
        return shop

    @staticmethod
    def get_nearby_shops(location, max_distance=5):
        """Find shops within the specified distance (in km)"""
        shops = list(db.shops.find({
            'status': 'active',
            'location': {
                '$near': {
                    '$geometry': {
                        'type': 'Point',
                        'coordinates': location
                    },
                    '$maxDistance': max_distance * 1000  # Convert to meters
                }
            }
        }))
        # Calculate exact distance and add to result
        for shop in shops:
            shop['distance'] = calculate_distance(
                location,
                shop['location']['coordinates']
            )
            shop['_id'] = str(shop['_id'])
            shop['owner_id'] = str(shop['owner_id'])

        return shops

    @staticmethod
    def get_shop_stats(shop_id):
        """Get shop statistics"""
        pipeline = [
            {'$match': {'shop_id': ObjectId(shop_id)}},
            {'$group': {
                '_id': '$status',
                'count': {'$sum': 1},
                'total_amount': {'$sum': '$total_amount'}
            }}
        ]
        
        stats = list(db.orders.aggregate(pipeline))
        
        # Format stats
        formatted_stats = {
            'total_orders': 0,
            'pending_orders': 0,
            'completed_orders': 0,
            'total_revenue': 0
        }
        
        for stat in stats:
            if stat['_id'] == 'completed':
                formatted_stats['completed_orders'] = stat['count']
                formatted_stats['total_revenue'] = stat['total_amount']
            elif stat['_id'] == 'pending':
                formatted_stats['pending_orders'] = stat['count']
            
            formatted_stats['total_orders'] += stat['count']
            
        return formatted_stats

    @staticmethod
    def add_service(shop_id, owner_id, service_data):
        """Add a new service to the shop"""
        shop = db.shops.find_one({
            '_id': ObjectId(shop_id),
            'owner_id': ObjectId(owner_id)
        })

        if not shop:
            raise ValueError('Shop not found or unauthorized')

        service = {
            'id': str(ObjectId()),
            'type': service_data['type'],
            'price': float(service_data['price']),
            'description': service_data.get('description', ''),
            'created_at': datetime.utcnow()
        }

        result = db.shops.update_one(
            {'_id': ObjectId(shop_id)},
            {
                '$push': {'services': service},
                '$set': {'updated_at': datetime.utcnow()}
            }
        )

        if result.modified_count == 0:
            raise ValueError('Failed to add service')

        return service['id']

    @staticmethod
    def update_service(shop_id, owner_id, service_id, service_data):
        """Update an existing service"""
        shop = db.shops.find_one({
            '_id': ObjectId(shop_id),
            'owner_id': ObjectId(owner_id)
        })

        if not shop:
            raise ValueError('Shop not found or unauthorized')

        result = db.shops.update_one(
            {
                '_id': ObjectId(shop_id),
                'services.id': service_id
            },
            {
                '$set': {
                    'services.$.type': service_data['type'],
                    'services.$.price': float(service_data['price']),
                    'services.$.description': service_data.get('description', ''),
                    'services.$.updated_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                }
            }
        )

        if result.modified_count == 0:
            raise ValueError('Service not found')

        return True

    @staticmethod
    def delete_service(shop_id, owner_id, service_id):
        """Delete a service"""
        shop = db.shops.find_one({
            '_id': ObjectId(shop_id),
            'owner_id': ObjectId(owner_id)
        })

        if not shop:
            raise ValueError('Shop not found or unauthorized')

        result = db.shops.update_one(
            {'_id': ObjectId(shop_id)},
            {
                '$pull': {'services': {'id': service_id}},
                '$set': {'updated_at': datetime.utcnow()}
            }
        )

        if result.modified_count == 0:
            raise ValueError('Service not found')

        return True

    @staticmethod
    def get_services(shop_id):
        """Get all services for a shop"""
        shop = db.shops.find_one({'_id': ObjectId(shop_id)})
        if not shop:
            raise ValueError('Shop not found')
        return shop.get('services', [])