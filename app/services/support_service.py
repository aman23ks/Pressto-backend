from app.models.supoort_ticket import SupportTicket
from .. import db
from bson import ObjectId
from datetime import datetime

class SupportService:
    @staticmethod
    def create_ticket(user_id, ticket_data):
        """Create a new support ticket."""
        try:
            # Create ticket instance
            ticket = SupportTicket(
                user_id=user_id,
                type=ticket_data['type'],
                subject=ticket_data['subject'],
                message=ticket_data['message'],
                name=ticket_data['name'],
                email=ticket_data['email'],
                phone=ticket_data.get('phone')
            )
            
            # Validate ticket data
            ticket.validate()
            
            # Convert to dictionary and insert
            ticket_dict = ticket.to_dict()
            result = db.support_tickets.insert_one(ticket_dict)
            return str(result.inserted_id)
            
        except ValueError as e:
            raise ValueError(str(e))
        except Exception as e:
            raise Exception(f'Failed to create ticket: {str(e)}')

    @staticmethod
    def get_user_tickets(user_id):
        """Get all tickets for a user."""
        tickets = list(db.support_tickets.find(
            {'user_id': user_id}
        ).sort('created_at', -1))
        # Convert to SupportTicket objects
        return [SupportTicket.from_dict(ticket) for ticket in tickets]

    @staticmethod
    def get_ticket_details(user_id, ticket_id):
        """Get details of a specific ticket."""
        ticket = db.support_tickets.find_one({
            '_id': ObjectId(ticket_id),
            'user_id': ObjectId(user_id)
        })
        if not ticket:
            raise ValueError('Ticket not found')
        
        return SupportTicket.from_dict(ticket)

    @staticmethod
    def update_ticket_status(ticket_id, new_status):
        """Update ticket status."""
        ticket = db.support_tickets.find_one({'_id': ObjectId(ticket_id)})
        if not ticket:
            raise ValueError('Ticket not found')
        
        ticket_obj = SupportTicket.from_dict(ticket)
        ticket_obj.update_status(new_status)
        
        result = db.support_tickets.update_one(
            {'_id': ObjectId(ticket_id)},
            {'$set': {
                'status': new_status,
                'updated_at': datetime.utcnow()
            }}
        )
        
        if result.modified_count == 0:
            raise ValueError('Failed to update ticket status')
        
        return True