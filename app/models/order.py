from datetime import datetime
from bson import ObjectId

class Order:
    VALID_STATUSES = ['Pending', 'Accepted', 'PickedUp', 'InProgress', 'Completed', 'Delivered', 'Cancelled']
    
    def __init__(self, customer_id, shop_id, items, pickup_time, delivery_time,
                 status='Pending', total_amount=0, pickup_address=None, 
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

    def validate(self):
        errors = []
        if self.status not in self.VALID_STATUSES:
            errors.append(f"Invalid status. Must be one of {', '.join(self.VALID_STATUSES)}")
        return errors

    def can_transition_to(self, new_status):
        """Define valid status transitions"""
        valid_transitions = {
            'Pending': ['Accepted', 'Cancelled'],
            'Accepted': ['PickedUp', 'Cancelled'],
            'PickedUp': ['InProgress', 'Cancelled'],
            'InProgress': ['Completed', 'Cancelled'],
            'Completed': ['Delivered'],
            'Delivered': [],
            'Cancelled': []
        }
        return new_status in valid_transitions.get(self.status, [])