# models/user_model.py
from flask_login import UserMixin
from bson import ObjectId, errors
from werkzeug.security import generate_password_hash, check_password_hash
from utils.db import get_db

db = get_db()

class User(UserMixin):
    """
    Multi-user model for Emeka's shop.
    Supports registration, login, and role-based access.
    """

    def __init__(self, user_doc):
        self.id = str(user_doc["_id"])
        self.username = user_doc["username"]
        self.role = user_doc.get("role", "sales")  # default role
        self.created_at = user_doc.get("created_at")

    @staticmethod
    def register(username, password, role="sales"):
        if db.users.find_one({"username": username}):
            raise ValueError("Username already exists")

        user = {
            "username": username.strip(),
            "password_hash": generate_password_hash(password),
            "role": role,
            "created_at": datetime.utcnow()
        }
        result = db.users.insert_one(user)
        return str(result.inserted_id)

    @staticmethod
    def authenticate(username, password):
        user_doc = db.users.find_one({"username": username})
        if user_doc and check_password_hash(user_doc["password_hash"], password):
            return User(user_doc)
        return None

    @staticmethod
    def get_by_id(user_id):
        try:
            obj_id = ObjectId(user_id)
        except (errors.InvalidId, TypeError):
            return None

        user_doc = db.users.find_one({"_id": obj_id})
        return User(user_doc) if user_doc else None
        
    @staticmethod
    def get_all():
        return list(db.users.find({}).sort("created_at", -1))

    @staticmethod
    def delete(user_id):
        return db.users.delete_one({"_id": ObjectId(user_id)})

    @staticmethod
    def update_role(user_id, new_role):
        return db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"role": new_role}}
        )
