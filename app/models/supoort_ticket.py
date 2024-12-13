from datetime import datetime
from bson import ObjectId

class SupportTicket:
    def __init__(self, user_id, type, subject, message, name, email, 
                 phone=None, status='open', created_at=None, updated_at=None, _id=None):
        self._id = _id if _id else ObjectId()
        self.user_id = ObjectId(user_id)
        self.type = type
        self.subject = subject
        self.message = message
        self.name = name
        self.email = email
        self.phone = phone
        self.status = status  # 'open', 'in_progress', 'resolved', 'closed'
        self.created_at = created_at if created_at else datetime.utcnow()
        self.updated_at = updated_at if updated_at else datetime.utcnow()

    def to_dict(self):
        return {
            '_id': str(self._id),
            'user_id': str(self.user_id),
            'type': self.type,
            'subject': self.subject,
            'message': self.message,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @staticmethod
    def from_dict(data):
        return SupportTicket(
            user_id=data.get('user_id'),
            type=data.get('type'),
            subject=data.get('subject'),
            message=data.get('message'),
            name=data.get('name'),
            email=data.get('email'),
            phone=data.get('phone'),
            status=data.get('status', 'open'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            _id=data.get('_id')
        )

    def update_status(self, new_status):
        allowed_statuses = ['open', 'in_progress', 'resolved', 'closed']
        if new_status not in allowed_statuses:
            raise ValueError(f'Invalid status. Must be one of: {", ".join(allowed_statuses)}')
        self.status = new_status
        self.updated_at = datetime.utcnow()

    def validate(self):
        if not all([self.user_id, self.type, self.subject, self.message, self.name, self.email]):
            raise ValueError('Missing required fields')
        
        allowed_types = ['bug', 'feature', 'general', 'account']
        if self.type not in allowed_types:
            raise ValueError(f'Invalid ticket type. Must be one of: {", ".join(allowed_types)}')