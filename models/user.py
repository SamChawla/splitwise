from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Column, Integer, String

from .db import db


class User(db.Model, UserMixin):
    __tablename__ = "users"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    # Can use sqlalchemy-utils for mobile number field and validation
    mobile_number = db.Column(db.String(10), nullable=False)
    hashed_password = db.Column(db.String(255), nullable=False)

    def __init__(self, username, name, email, mobile_number, password):
        self.username = username
        self.name = name
        self.email = email
        self.mobile_number = mobile_number
        self.password = password

    @property
    def password(self):
        return self.hashed_password

    @password.setter
    def password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "name": self.name,
            "email": self.email,
            "mobile_number": self.mobile_number,
        }
