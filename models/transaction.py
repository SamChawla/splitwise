from .db import db

class UserTransaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    payer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    expense_id = db.Column(db.Integer, db.ForeignKey("expenses.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.Date, nullable=False)

    paid_by = db.relationship("User", foreign_keys=[payer_id], backref="credit_transactions")
    paid_to = db.relationship("User", foreign_keys=[recipient_id], backref="debit_transactions")
    expense = db.relationship("Expense", foreign_keys=[expense_id], backref="transactions")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "amount": self.amount,
            "description": self.description,
            "date": self.date,
        }