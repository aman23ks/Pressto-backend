from flask import Blueprint, request, jsonify
from app.services.shop_service import ShopService
from app.utils.decorators import login_required, shop_owner_required
from bson import json_util, ObjectId
import json
from datetime import datetime, timedelta
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
            "rating": shop.get("rating", 4.5),  # Default rating if not available
            "totalOrders": shop.get("total_orders", 0),
            "distance": "1.2 km",  # Static for now
            "services": shop.get("services", []),
            "address": shop.get("address", "No address available")  
        } for shop in shops]
        return jsonify(formatted_shops), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@shop_bp.route('/orders', methods=['GET'])
@shop_owner_required
def get_shop_orders(current_user):
    try:
        shop = db.shops.find_one({'owner_id': ObjectId(current_user['user_id'])})
        if not shop:
            return jsonify({'error': 'Shop not found'}), 404

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
                'pickup_date': 1,
                'totalAmount': '$total_amount',
                'created_at': 1,
                'pickup_address': 1
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

@shop_bp.route('/services', methods=['GET', 'POST'])
@shop_owner_required
def handle_services(current_user):
    try:
        shop = db.shops.find_one({'owner_id': ObjectId(current_user['user_id'])})
        if not shop:
            return jsonify({'error': 'Shop not found'}), 404

        if request.method == 'GET':
            services = ShopService.get_services(shop['_id'])
            return jsonify(services), 200
        else:  # POST
            service_data = request.get_json()
            service_id = ShopService.add_service(
                shop['_id'],
                current_user['user_id'],
                service_data
            )
            return jsonify({'service_id': service_id}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to handle service request'}), 500

@shop_bp.route('/services/<service_id>', methods=['PUT', 'DELETE'])
@shop_owner_required
def handle_service(current_user, service_id):
    try:
        shop = db.shops.find_one({'owner_id': ObjectId(current_user['user_id'])})
        if not shop:
            return jsonify({'error': 'Shop not found'}), 404

        if request.method == 'PUT':
            service_data = request.get_json()
            ShopService.update_service(
                shop['_id'],
                current_user['user_id'],
                service_id,
                service_data
            )
            return jsonify({'message': 'Service updated successfully'}), 200
        else:  # DELETE
            ShopService.delete_service(
                shop['_id'],
                current_user['user_id'],
                service_id
            )
            return jsonify({'message': 'Service deleted successfully'}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to handle service request'}), 500
    

@shop_bp.route('/dashboard-stats', methods=['GET'])
@shop_owner_required
def get_dashboard_stats(current_user):
    try:
        # Get shop for current owner
        shop = db.shops.find_one({'owner_id': ObjectId(current_user['user_id'])})
        if not shop:
            return jsonify({'error': 'Shop not found'}), 404

        # Parse timeframe from query params
        timeframe = request.args.get('timeframe', 'week')
        
        # Calculate date range
        end_date = datetime.utcnow()
        if timeframe == 'week':
            start_date = end_date - timedelta(days=7)
        elif timeframe == 'month':
            start_date = end_date - timedelta(days=30)
        else:  # year
            start_date = end_date - timedelta(days=365)

        # Get orders for this shop
        orders = list(db.orders.find({
            'shop_id': shop['_id'],
            'created_at': {'$gte': start_date, '$lte': end_date}
        }).sort('created_at', -1))

        # Initialize default stats
        stats = {
            'totalOrders': 0,
            'totalRevenue': 0,
            'completedOrders': 0,
            'pendingOrders': 0,
            'revenueByDay': [],
            'ordersByStatus': [],
            'topServices': []
        }

        if not orders:
            return jsonify(stats), 200

        # Calculate basic stats
        stats['totalOrders'] = len(orders)
        stats['totalRevenue'] = sum(order.get('total_amount', 0) for order in orders)
        stats['completedOrders'] = sum(1 for order in orders if order.get('status') == 'completed')
        stats['pendingOrders'] = sum(1 for order in orders if order.get('status') == 'pending')

        # Calculate revenue by day
        revenue_by_day = {}
        for order in orders:
            date = order['created_at'].strftime('%Y-%m-%d')
            revenue_by_day[date] = revenue_by_day.get(date, 0) + order.get('total_amount', 0)

        stats['revenueByDay'] = [
            {'date': date, 'revenue': amount} 
            for date, amount in sorted(revenue_by_day.items())
        ]

        # Calculate orders by status
        status_count = {}
        for order in orders:
            status = order.get('status', 'unknown')
            status_count[status] = status_count.get(status, 0) + 1

        stats['ordersByStatus'] = [
            {'status': status, 'count': count}
            for status, count in status_count.items()
        ]

        # Calculate top services
        service_count = {}
        for order in orders:
            for item in order.get('items', []):
                service = item.get('type')
                if service:
                    service_count[service] = service_count.get(service, 0) + item.get('count', 0)

        stats['topServices'] = [
            {'name': service, 'count': count}
            for service, count in sorted(service_count.items(), key=lambda x: x[1], reverse=True)
        ][:5]  # Top 5 services

        return jsonify(stats), 200

    except Exception as e:
        print(f"Error in dashboard stats: {str(e)}")  # Add logging
        return jsonify({'error': 'Failed to fetch shop details'}), 500