from datetime import datetime
from bson import ObjectId
import re

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_phone(phone):
    pattern = r'^\+?1?\d{9,15}$'
    return bool(re.match(pattern, phone))

def validate_password(password):
    """Password must be at least 8 characters long and contain at least one number"""
    if len(password) < 8:
        return False
    return bool(re.search(r"\d", password))

def calculate_distance(coord1, coord2):
    """Calculate distance between two coordinates using Haversine formula"""
    from math import sin, cos, sqrt, atan2, radians
    
    R = 6371  # Earth's radius in kilometers

    lat1, lon1 = radians(coord1[1]), radians(coord1[0])
    lat2, lon2 = radians(coord2[1]), radians(coord2[0])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c

    return distance

def format_datetime(dt):
    return datetime.strftime(dt, "%Y-%m-%d %H:%M:%S")

def parse_datetime(dt_str):
    return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")