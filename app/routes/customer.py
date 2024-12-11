from flask import Blueprint, request, jsonify
from app.services.customer_service import CustomerService
from app.utils.decorators import login_required
from bson import json_util
import json

customer_bp = Blueprint('customer', __name__)

# Status mapping for order types
ORDER_TYPE_STATUSES = {
    'active': ['pending', 'accepted', 'pickedUp', 'inProgress', 'completed'],
    'history': ['delivered', 'cancelled']
}

@customer_bp.route('/profile', methods=['GET'])
@login_required
def get_profile(current_user):
    try:
        if current_user['user_type'] != 'customer':
            return jsonify({'error': 'Unauthorized'}), 403
            
        profile = CustomerService.get_profile(current_user['user_id'])
        profile_json = json_util.dumps(profile)
        return jsonify(json.loads(profile_json)), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to fetch profile'}), 500

@customer_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile(current_user):
    try:
        if current_user['user_type'] != 'customer':
            return jsonify({'error': 'Unauthorized'}), 403
            
        profile_data = request.get_json()
        CustomerService.update_profile(current_user['user_id'], profile_data)
        return jsonify({'message': 'Profile updated successfully'}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to update profile'}), 500

@customer_bp.route('/addresses', methods=['POST'])
@login_required
def add_address(current_user):
    try:
        if current_user['user_type'] != 'customer':
            return jsonify({'error': 'Unauthorized'}), 403
            
        address_data = request.get_json()
        address_id = CustomerService.add_address(
            current_user['user_id'], 
            address_data
        )
        return jsonify({'address_id': address_id}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to add address'}), 500

@customer_bp.route('/addresses', methods=['GET'])
@login_required
def get_addresses(current_user):
    try:
        if current_user['user_type'] != 'customer':
            return jsonify({'error': 'Unauthorized'}), 403
            
        addresses = CustomerService.get_addresses(current_user['user_id'])
        addresses_json = json_util.dumps(addresses)
        return jsonify(json.loads(addresses_json)), 200
    except Exception as e:
        return jsonify({'error': 'Failed to fetch addresses'}), 500

@customer_bp.route('/addresses/<address_id>', methods=['DELETE'])
@login_required
def delete_address(current_user, address_id):
    try:
        if current_user['user_type'] != 'customer':
            return jsonify({'error': 'Unauthorized'}), 403
            
        CustomerService.delete_address(current_user['user_id'], address_id)
        return jsonify({'message': 'Address deleted successfully'}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to delete address'}), 500

@customer_bp.route('/orders', methods=['GET'])
@login_required
def get_customer_orders(current_user):
    try:
        if current_user['user_type'] != 'customer':
            return jsonify({'error': 'Unauthorized'}), 403

        # Get all orders without filtering by type
        orders = CustomerService.get_order_by_status(current_user)
        orders_json = json_util.dumps(orders)
        
        return jsonify(json.loads(orders_json)), 200
    except Exception as e:
        print(f"Error in get_customer_orders: {str(e)}")
        return jsonify({'error': 'Failed to fetch orders'}), 500

@customer_bp.route('/orders/dashboard', methods=['GET'])
@login_required
def get_dashboard_orders(current_user):
    try:
        if current_user['user_type'] != 'customer':
            return jsonify({'error': 'Unauthorized'}), 403
            
        # Get active orders for dashboard
        orders = CustomerService.get_order_by_status(current_user, 'active')
        
        # Format response for dashboard
        response = {
            'activeOrders': orders,
            'orderCounts': {
                'pending': sum(1 for order in orders if order['status'] == 'pending'),
                'processing': sum(1 for order in orders if order['status'] in ['accepted', 'pickedUp', 'inProgress']),
                'ready': sum(1 for order in orders if order['status'] == 'completed'),
            }
        }
        
        return jsonify(response), 200
    except Exception as e:
        print(f"Error in get_dashboard_orders: {str(e)}")
        return jsonify({'error': 'Failed to fetch dashboard orders'}), 500

@customer_bp.route('/orders/<order_id>', methods=['GET'])
@login_required
def get_order_details(current_user, order_id):
    try:
        if current_user['user_type'] != 'customer':
            return jsonify({'error': 'Unauthorized'}), 403

        order = CustomerService.get_order_details(current_user['user_id'], order_id)
        order_json = json_util.dumps(order)
        return jsonify(json.loads(order_json)), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to fetch order details'}), 500

@customer_bp.route('/orders/history', methods=['GET'])
@login_required
def get_order_history(current_user):
    try:
        if current_user['user_type'] != 'customer':
            return jsonify({'error': 'Unauthorized'}), 403

        # Get completed and cancelled orders
        orders = CustomerService.get_order_by_status(current_user, 'history')
        orders_json = json_util.dumps(orders)
        
        return jsonify(json.loads(orders_json)), 200
    except Exception as e:
        print(f"Error in get_order_history: {str(e)}")
        return jsonify({'error': 'Failed to fetch order history'}), 500