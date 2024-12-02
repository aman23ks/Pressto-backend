from datetime import datetime
from bson import ObjectId

class Address:
    def __init__(self, user_id, street, city, state, pincode, landmark=None, 
                 is_default=False, address_type='home', created_at=None, 
                 updated_at=None, _id=None):
        self._id = _id if _id else ObjectId()
        self.user_id = user_id
        self.street = street
        self.city = city
        self.state = state
        self.pincode = pincode
        self.landmark = landmark
        self.is_default = is_default
        self.address_type = address_type  # 'home', 'work', 'other'
        self.created_at = created_at if created_at else datetime.utcnow()
        self.updated_at = updated_at if updated_at else datetime.utcnow()

    def to_dict(self):
        return {
            '_id': str(self._id),
            'user_id': str(self.user_id),
            'street': self.street,
            'city': self.city,
            'state': self.state,
            'pincode': self.pincode,
            'landmark': self.landmark,
            'is_default': self.is_default,
            'address_type': self.address_type,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @staticmethod
    def from_dict(data):
        return Address(
            user_id=data.get('user_id'),
            street=data.get('street'),
            city=data.get('city'),
            state=data.get('state'),
            pincode=data.get('pincode'),
            landmark=data.get('landmark'),
            is_default=data.get('is_default', False),
            address_type=data.get('address_type', 'home'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            _id=data.get('_id')
        )

    def validate(self):
        """Validate address data"""
        errors = []
        
        if not self.street or not self.street.strip():
            errors.append("Street address is required")
        
        if not self.city or not self.city.strip():
            errors.append("City is required")
            
        if not self.state or not self.state.strip():
            errors.append("State is required")
            
        if not self.pincode or not str(self.pincode).strip():
            errors.append("PIN code is required")
        elif not str(self.pincode).isdigit() or len(str(self.pincode)) != 6:
            errors.append("PIN code must be a 6-digit number")
            
        if self.address_type not in ['home', 'work', 'other']:
            errors.append("Invalid address type")
            
        return errors

    @staticmethod
    def create_indexes(db):
        """Create necessary indexes for the addresses collection"""
        db.addresses.create_index([("user_id", 1)])
        db.addresses.create_index([("pincode", 1)])
        # Compound index for user_id and is_default
        db.addresses.create_index([
            ("user_id", 1), 
            ("is_default", 1)
        ])

    @classmethod
    def get_user_addresses(cls, db, user_id):
        """Get all addresses for a user"""
        addresses = db.addresses.find({"user_id": ObjectId(user_id)})
        return [cls.from_dict(addr) for addr in addresses]

    @classmethod
    def get_address_by_id(cls, db, address_id, user_id):
        """Get specific address by ID and user ID"""
        address = db.addresses.find_one({
            "_id": ObjectId(address_id),
            "user_id": ObjectId(user_id)
        })
        return cls.from_dict(address) if address else None

    @classmethod
    def set_default_address(cls, db, address_id, user_id):
        """Set an address as default and unset any existing default"""
        # First, unset any existing default address
        db.addresses.update_many(
            {"user_id": ObjectId(user_id)},
            {"$set": {"is_default": False}}
        )
        
        # Then set the new default address
        result = db.addresses.update_one(
            {
                "_id": ObjectId(address_id),
                "user_id": ObjectId(user_id)
            },
            {"$set": {"is_default": True}}
        )
        return result.modified_count > 0

    @classmethod
    def update_address(cls, db, address_id, user_id, update_data):
        """Update an address"""
        allowed_fields = ['street', 'city', 'state', 'pincode', 'landmark', 
                         'address_type']
        update_dict = {
            key: value for key, value in update_data.items() 
            if key in allowed_fields
        }
        update_dict['updated_at'] = datetime.utcnow()
        
        result = db.addresses.update_one(
            {
                "_id": ObjectId(address_id),
                "user_id": ObjectId(user_id)
            },
            {"$set": update_dict}
        )
        return result.modified_count > 0

    @classmethod
    def delete_address(cls, db, address_id, user_id):
        """Delete an address"""
        result = db.addresses.delete_one({
            "_id": ObjectId(address_id),
            "user_id": ObjectId(user_id)
        })
        return result.deleted_count > 0

    def save(self, db):
        """Save address to database"""
        errors = self.validate()
        if errors:
            raise ValueError(", ".join(errors))

        address_dict = self.to_dict()
        # Convert string IDs back to ObjectId
        address_dict['_id'] = ObjectId(address_dict['_id'])
        address_dict['user_id'] = ObjectId(address_dict['user_id'])
        
        # If this is set as default, unset any existing default
        if self.is_default:
            db.addresses.update_many(
                {"user_id": ObjectId(self.user_id)},
                {"$set": {"is_default": False}}
            )
        
        result = db.addresses.update_one(
            {"_id": address_dict['_id']},
            {"$set": address_dict},
            upsert=True
        )
        return result.upserted_id or self._id