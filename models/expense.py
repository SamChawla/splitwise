from .db import db

from enum import Enum

class SplitType(Enum):
    EQUAL = "EQUAL"
    PERCENTAGE = "PERCENTAGE"
    EXACT = "EXACT"

members_table = db.Table('members',
    db.Column('expense_id', db.Integer, db.ForeignKey('expenses.id')),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'))
)

class Expense(db.Model):
    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True)
    paid_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(255), nullable=False)
    split_type = db.Column(db.Enum(SplitType), nullable=False)
    # owed_by should be a list of user ids
    owed_by = db.relationship('User', secondary=members_table, backref='expenses')
    date = db.Column(db.Date, nullable=False)


    def to_dict(self):
        return {
            "id": self.id,
            "paid_by": self.paid_by,
            "amount": self.amount,
            "description": self.description,
            "category": self.category,
            "type": self.split_type,
            "date": self.date,
        }