from datetime import datetime
from bson import ObjectId

class Order:
    def __init__(self, customer_id, shop_id, items, pickup_time, delivery_time,
                 status='pending', total_amount=0, pickup_address=None, 
                 special_instructions=None, created_at=None, updated_at=None, _id=None):
        self._id = _id if _id else ObjectId()
        self.customer_id = customer_id
        self.shop_id = shop_id
        self.items = items  # [{type: string, count: number}]
        self.pickup_time = pickup_time
        self.delivery_time = delivery_time
        self.status = status
        self.total_amount = total_amount
        self.pickup_address = pickup_address
        self.special_instructions = special_instructions
        self.created_at = created_at if created_at else datetime.utcnow()
        self.updated_at = updated_at if updated_at else datetime.utcnow()

    def to_dict(self):
        return {
            '_id': str(self._id),
            'customer_id': str(self.customer_id),
            'shop_id': str(self.shop_id),
            'items': self.items,
            'pickup_time': self.pickup_time,
            'delivery_time': self.delivery_time,
            'status': self.status,
            'total_amount': self.total_amount,
            'pickup_address': self.pickup_address,
            'special_instructions': self.special_instructions,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }