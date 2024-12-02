from datetime import datetime
from bson import ObjectId

class User:
    def __init__(self, name, email, phone, password_hash, user_type, 
                 created_at=None, updated_at=None, _id=None):
        self._id = _id if _id else ObjectId()
        self.name = name
        self.email = email
        self.phone = phone
        self.password_hash = password_hash
        self.user_type = user_type  # 'customer' or 'shopOwner'
        self.created_at = created_at if created_at else datetime.utcnow()
        self.updated_at = updated_at if updated_at else datetime.utcnow()

    def to_dict(self):
        return {
            '_id': str(self._id),
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'user_type': self.user_type,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @staticmethod
    def from_dict(data):
        return User(
            name=data.get('name'),
            email=data.get('email'),
            phone=data.get('phone'),
            password_hash=data.get('password_hash'),
            user_type=data.get('user_type'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            _id=data.get('_id')
        )