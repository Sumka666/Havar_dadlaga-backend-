import jwt, datetime
from django.conf import settings

def create_token(user_id, role):
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=6)
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

def decode_token(token):
    return jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
