from flask import Blueprint, request, jsonify
from app.services.order_service import OrderService
from app.utils.decorators import login_required
from bson import json_util
import json

orders_bp = Blueprint('orders', __name__)

@orders_bp.route('/', methods=['POST'])
@login_required
def create_order(current_user):
    try:
        if current_user['user_type'] != 'customer':
            return jsonify({'error': 'Only customers can create orders'}), 403

        data = request.get_json()
        order_id = OrderService.create_order(
            customer_id=current_user['user_id'],
            shop_id=data['shop_id'],
            items=data['items'],
            pickup_date=data['pickup_date'],
            # pickup_time=data['pickup_time'],
            # delivery_time=data['delivery_time'],
            pickup_address=data['pickup_address'],
            special_instructions=data.get('special_instructions'),
            total_amount=data.get('total_amount')
        )
        return jsonify({'order_id': order_id}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to create order'}), 500

@orders_bp.route('/customer', methods=['GET'])
@login_required
def get_customer_orders(current_user):
    try:
        if current_user['user_type'] != 'customer':
            return jsonify({'error': 'Unauthorized'}), 403

        status = request.args.get('status')
        orders = OrderService.get_customer_orders(current_user['user_id'], status)
        orders_json = json_util.dumps(orders)
        return jsonify(json.loads(orders_json)), 200
    except Exception as e:
        return jsonify({'error': 'Failed to fetch orders'}), 500

@orders_bp.route('/shop', methods=['GET'])
@login_required
def get_shop_orders(current_user):
    try:
        if current_user['user_type'] != 'shopOwner':
            return jsonify({'error': 'Unauthorized'}), 403

        status = request.args.get('status')
        orders = OrderService.get_shop_orders(current_user['user_id'], status)
        orders_json = json_util.dumps(orders)
        return jsonify(json.loads(orders_json)), 200
    except Exception as e:
        return jsonify({'error': 'Failed to fetch orders'}), 500

@orders_bp.route('/<order_id>/status', methods=['PUT'])
@login_required
def update_order_status(current_user, order_id):
    try:
        data = request.get_json()
        new_status = data.get('status')
        if not new_status:
            return jsonify({'error': 'Status is required'}), 400

        OrderService.update_order_status(
            order_id=order_id,
            new_status=new_status,
            user_id=current_user['user_id'],
            user_type=current_user['user_type']
        )
        return jsonify({'message': 'Order status updated successfully'}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to update order status'}), 500

@orders_bp.route('/<order_id>', methods=['GET'])
@login_required
def get_order_details(current_user, order_id):
    try:
        order = OrderService.get_order_details(
            order_id=order_id,
            user_id=current_user['user_id'],
            user_type=current_user['user_type']
        )
        return jsonify(order), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to fetch order details'}), 500