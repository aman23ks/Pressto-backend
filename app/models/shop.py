# models/shop.py
from datetime import datetime
from bson import ObjectId

class Shop:
    def __init__(self, name, owner_id, address, location,
                 business_hours, contact_info, services=None, status='active',
                 rating=0, total_orders=0, created_at=None, updated_at=None, _id=None):
        self._id = _id if _id else ObjectId()
        self.name = name
        self.owner_id = owner_id
        self.address = address
        self.location = location  # {type: "Point", coordinates: [longitude, latitude]}
        self.services = services if services else []  # List of service items
        self.business_hours = business_hours
        self.contact_info = contact_info
        self.status = status
        self.rating = rating
        self.total_orders = total_orders
        self.created_at = created_at if created_at else datetime.utcnow()
        self.updated_at = updated_at if updated_at else datetime.utcnow()

    def to_dict(self):
        return {
            '_id': str(self._id),
            'name': self.name,
            'owner_id': str(self.owner_id),
            'address': self.address,
            'location': self.location,
            'services': self.services,
            'business_hours': self.business_hours,
            'contact_info': self.contact_info,
            'status': self.status,
            'rating': self.rating,
            'total_orders': self.total_orders,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }