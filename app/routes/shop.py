from flask import Blueprint, request, jsonify
from app.services.shop_service import ShopService
from app.utils.decorators import login_required, shop_owner_required
from bson import json_util, ObjectId
import json
from datetime import datetime
from .. import db

shop_bp = Blueprint('shop', __name__)

@shop_bp.route('/', methods=['POST'])
@shop_owner_required
def create_shop(current_user):
    try:
        shop_data = request.get_json()
        shop_id = ShopService.create_shop(current_user['user_id'], shop_data)
        return jsonify({'shop_id': shop_id}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to create shop'}), 500

@shop_bp.route('/<shop_id>', methods=['PUT'])
@shop_owner_required
def update_shop(current_user, shop_id):
    try:
        shop_data = request.get_json()
        ShopService.update_shop(shop_id, current_user['user_id'], shop_data)
        return jsonify({'message': 'Shop updated successfully'}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to update shop'}), 500

@shop_bp.route('/nearby', methods=['GET'])
@login_required
def get_nearby_shops(current_user):
    try:
        lat = float(request.args.get('lat'))
        lng = float(request.args.get('lng'))
        max_distance = float(request.args.get('distance', 5))
        shops = ShopService.get_nearby_shops([lng, lat], max_distance)
        return jsonify(shops), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to fetch nearby shops'}), 500

@shop_bp.route('/<shop_id>', methods=['GET'])
@login_required
def get_shop_details(current_user, shop_id):
    try:
        shop = ShopService.get_shop_details(shop_id)
        shop_json = json_util.dumps(shop)
        return jsonify(json.loads(shop_json)), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to fetch shop details'}), 500

@shop_bp.route('/<shop_id>/stats', methods=['GET'])
@shop_owner_required
def get_shop_stats(current_user, shop_id):
    try:
        # Verify shop ownership
        shop = ShopService.get_shop_details(shop_id)
        if str(shop['owner_id']) != current_user['user_id']:
            return jsonify({'error': 'Unauthorized'}), 403
            
        stats = ShopService.get_shop_stats(shop_id)
        return jsonify(stats), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to fetch shop statistics'}), 500

@shop_bp.route('/<shop_id>/business-hours', methods=['PUT'])
@shop_owner_required
def update_business_hours(current_user, shop_id):
    try:
        hours_data = request.get_json()
        ShopService.update_shop(
            shop_id, 
            current_user['user_id'], 
            {'business_hours': hours_data}
        )
        return jsonify({'message': 'Business hours updated successfully'}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to update business hours'}), 500

@shop_bp.route('/<shop_id>/pricing', methods=['PUT'])
@shop_owner_required
def update_pricing(current_user, shop_id):
    try:
        pricing_data = request.get_json()
        ShopService.update_shop(
            shop_id, 
            current_user['user_id'], 
            {'price_per_item': float(pricing_data['price_per_item'])}
        )
        return jsonify({'message': 'Pricing updated successfully'}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to update pricing'}), 500

@shop_bp.route('/<shop_id>/status', methods=['PUT'])
@shop_owner_required
def update_shop_status(current_user, shop_id):
    try:
        status_data = request.get_json()
        if status_data['status'] not in ['active', 'inactive', 'maintenance']:
            return jsonify({'error': 'Invalid status'}), 400
            
        ShopService.update_shop(
            shop_id, 
            current_user['user_id'], 
            {'status': status_data['status']}
        )
        return jsonify({'message': 'Shop status updated successfully'}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to update shop status'}), 500
    

@shop_bp.route('/', methods=['GET'])
def get_all_shops():
    try:
        # Fetch all active shops
        shops = list(db.shops.find({"status": "active"}))
        # Format the response
        formatted_shops = [{
            "id": str(shop["_id"]),
            "name": shop["name"],
            "pricePerItem": float(shop["price_per_item"]),
            "rating": shop.get("rating", 4.5),  # Default rating if not available
            "totalOrders": shop.get("total_orders", 0),
            "distance": "1.2 km",  # Static for now
            "deliveryTime": "24 hours"  # Static for now
        } for shop in shops]
        return jsonify(formatted_shops), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# routes/shop.py - Add these new endpoints

@shop_bp.route('/orders', methods=['GET'])
@shop_owner_required
def get_shop_orders(current_user):
    try:
        # Get shop_id for current owner
        shop = db.shops.find_one({'owner_id': ObjectId(current_user['user_id'])})
        if not shop:
            return jsonify({'error': 'Shop not found'}), 404

        # Get orders for this shop
        orders = list(db.orders.aggregate([
            {'$match': {'shop_id': shop['_id']}},
            {'$lookup': {
                'from': 'users',
                'localField': 'customer_id',
                'foreignField': '_id',
                'as': 'customer'
            }},
            {'$unwind': '$customer'},
            {'$project': {
                'id': {'$toString': '$_id'},
                'customerName': '$customer.name',
                'items': 1,
                'status': 1,
                'pickupTime': '$pickup_time',
                'deliveryTime': '$delivery_time',
                'totalAmount': '$total_amount',
                'created_at': 1,
                'pickup_address': 1  # Include pickup_address in projection
            }}
        ]))
        orders_json = json_util.dumps(orders)
        return jsonify(json.loads(orders_json)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@shop_bp.route('/orders/<order_id>/status', methods=['PUT'])
@shop_owner_required
def update_order_status(current_user, order_id):
    try:
        data = request.get_json()
        new_status = data.get('status')
        if not new_status:
            return jsonify({'error': 'Status is required'}), 400

        # Verify shop ownership and update status
        shop = db.shops.find_one({'owner_id': ObjectId(current_user['user_id'])})
        if not shop:
            return jsonify({'error': 'Shop not found'}), 404

        result = db.orders.update_one(
            {
                '_id': ObjectId(order_id),
                'shop_id': shop['_id']
            },
            {
                '$set': {
                    'status': new_status,
                    'updated_at': datetime.utcnow()
                }
            }
        )

        if result.matched_count == 0:
            return jsonify({'error': 'Order not found or unauthorized'}), 404

        return jsonify({'message': 'Order status updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@shop_bp.route('/services', methods=['GET'])
@shop_owner_required
def get_services(current_user):
    try:
        shop = db.shops.find_one({'owner_id': ObjectId(current_user['user_id'])})
        if not shop:
            return jsonify({'error': 'Shop not found'}), 404

        services = ShopService.get_services(shop['_id'])
        return jsonify(services), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to fetch services'}), 500

@shop_bp.route('/services', methods=['POST'])
@shop_owner_required
def add_service(current_user):
    try:
        service_data = request.get_json()
        
        # Validate required fields
        if not all(k in service_data for k in ['type', 'price']):
            return jsonify({'error': 'Type and price are required'}), 400

        shop = db.shops.find_one({'owner_id': ObjectId(current_user['user_id'])})
        if not shop:
            return jsonify({'error': 'Shop not found'}), 404

        service_id = ShopService.add_service(
            shop['_id'],
            current_user['user_id'],
            service_data
        )
        return jsonify({'service_id': service_id}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to add service'}), 500

@shop_bp.route('/services/<service_id>', methods=['PUT'])
@shop_owner_required
def update_service(current_user, service_id):
    try:
        service_data = request.get_json()
        
        shop = db.shops.find_one({'owner_id': ObjectId(current_user['user_id'])})
        if not shop:
            return jsonify({'error': 'Shop not found'}), 404

        ShopService.update_service(
            shop['_id'],
            current_user['user_id'],
            service_id,
            service_data
        )
        return jsonify({'message': 'Service updated successfully'}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to update service'}), 500

@shop_bp.route('/services/<service_id>', methods=['DELETE'])
@shop_owner_required
def delete_service(current_user, service_id):
    try:
        shop = db.shops.find_one({'owner_id': ObjectId(current_user['user_id'])})
        if not shop:
            return jsonify({'error': 'Shop not found'}), 404

        ShopService.delete_service(
            shop['_id'],
            current_user['user_id'],
            service_id
        )
        return jsonify({'message': 'Service deleted successfully'}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to delete service'}), 500