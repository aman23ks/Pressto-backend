from flask import Blueprint, request, jsonify
from app.services.shop_service import ShopService
from app.utils.decorators import login_required, shop_owner_required
from bson import json_util
import json
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