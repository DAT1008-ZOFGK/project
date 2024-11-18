from flask_jwt_extended import JWTManager, create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask import jsonify, request
from models import User, db

jwt = JWTManager()

def authenticate():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                return jsonify({"msg": "Missing token"}), 401
            try:
                # Verify JWT token
                token = auth_header.split(" ")[1]
                jwt.decode_token(token)
                return fn(*args, **kwargs)
            except Exception as e:
                return jsonify({"msg": "Invalid token"}), 401
        return decorator
    return wrapper