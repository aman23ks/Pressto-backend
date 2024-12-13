# app/routes/support_routes.py

from flask import Blueprint, request, jsonify
from app.services.support_service import SupportService
from app.utils.decorators import login_required
from app.models.supoort_ticket import SupportTicket  # Add this import
from bson import json_util, ObjectId
import json
from datetime import datetime
from .. import db

support_bp = Blueprint('support', __name__)

@support_bp.route('/tickets', methods=['POST'])
@login_required
def create_ticket(current_user):
    try:
        ticket_data = request.get_json()
        
        # Validate required fields
        required_fields = ['type', 'subject', 'message']
        for field in required_fields:
            if not ticket_data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Add user information to ticket data
        user = db.users.find_one({'_id': ObjectId(current_user['user_id'])})
        ticket_data['name'] = user.get('name', '')
        ticket_data['email'] = user.get('email', '')
        ticket_data['phone'] = user.get('phone', '')
        
        # Create ticket
        ticket_id = SupportService.create_ticket(
            current_user['user_id'],
            ticket_data
        )

        # Send email notification
        try:
            send_support_notification(ticket_data)
        except Exception as e:
            print(f"Failed to send email notification: {str(e)}")

        return jsonify({
            'message': 'Support ticket created successfully',
            'ticket_id': ticket_id
        }), 201

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Error creating support ticket: {str(e)}")
        return jsonify({'error': 'Failed to create support ticket'}), 500

@support_bp.route('/tickets', methods=['GET'])
@login_required
def get_user_tickets(current_user):
    try:
        tickets = SupportService.get_user_tickets(current_user['user_id'])
        # Convert tickets to dictionary format
        tickets_dict = [ticket.to_dict() for ticket in tickets]
        return jsonify(tickets_dict), 200
    except Exception as e:
        return jsonify({'error': 'Failed to fetch tickets'}), 500

@support_bp.route('/tickets/<ticket_id>', methods=['GET'])
@login_required
def get_ticket_details(current_user, ticket_id):
    try:
        ticket = SupportService.get_ticket_details(
            current_user['user_id'],
            ticket_id
        )
        return jsonify(ticket.to_dict()), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to fetch ticket details'}), 500

@support_bp.route('/tickets/<ticket_id>/status', methods=['PUT'])
@login_required
def update_ticket_status(current_user, ticket_id):
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if not new_status:
            return jsonify({'error': 'Status is required'}), 400
            
        SupportService.update_ticket_status(ticket_id, new_status)
        return jsonify({'message': 'Ticket status updated successfully'}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to update ticket status'}), 500

# Helper function to send email notifications
def send_support_notification(ticket_data):
    # Import your email service
    from app.utils.email_service import send_email
    
    subject = f"New Support Ticket: {ticket_data['subject']}"
    body = f"""
    New support ticket received:
    
    Type: {ticket_data['type']}
    From: {ticket_data['name']} ({ticket_data['email']})
    Subject: {ticket_data['subject']}
    
    Message:
    {ticket_data['message']}
    
    Phone: {ticket_data.get('phone', 'Not provided')}
    
    Status: {ticket_data.get('status', 'open')}
    Ticket Type: {ticket_data['type']}
    Created At: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
    """
    
    # Send to support email
    send_email(
        to_email="support@pressto.com",
        subject=subject,
        body=body
    )