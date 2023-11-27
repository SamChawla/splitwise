import time
from . import api, ma
from flask import Blueprint, jsonify

from marshmallow import Schema, fields
from flask_restful import Resource, Api
from flask_apispec.views import MethodResource
from flask_apispec import marshal_with, doc, use_kwargs
from flask_login import current_user, login_user, logout_user, login_required

from ..models import db, User, UserBalance, UserTransaction, Expense
from ..controller import api, ma, docs, login


@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class APIResponse(Schema):
    message = fields.Str(default="Success")
    data = fields.Dict(default={})


class UserTransactionSchema(ma.Schema):
    recipient_id = fields.Int(required=True)
    amount = fields.Float(required=True)
    description = fields.Str(required=True)


class ExpenseSchema(ma.Schema):
    class Meta:
        model = Expense
        fields = ("id", "payer_id", "amount", "description", "created_at")


class CreateExpenseRequest(ma.Schema):
    amount = fields.Float(required=True)
    description = fields.Str(required=True)
    category = fields.Str(required=True)
    split_type = fields.Str(
        required=True, validate=fields.validate.OneOf(["EQUAL", "PERCENTAGE", "EXACT"])
    )
    owed_by = fields.List(fields.Int(), required=True)
    split_values = fields.List(fields.Float(), required=False)


expense_routes = Blueprint("expense_routes", __name__, url_prefix="/api/")


class ExpenseAPI(MethodResource, Resource):
    @doc(description="Create Expense API", tags=["Create Expense API"])
    @use_kwargs(ExpenseSchema, location=("json"))
    @marshal_with(APIResponse)  # marshalling
    def post(self, **kwargs):
        try:
            current_user_id = current_user.get_id()

            expense = Expense()
            expense.paid_by = current_user_id
            expense.amount = kwargs["amount"]
            expense.description = kwargs["description"]
            expense.category = kwargs["category"]
            expense.split_type = kwargs["split_type"]
            expense.date = time.strftime("%Y-%m-%d")

            if expense.split_type == "EQUAL":
                share_amount = expense.amount / (len(kwargs["owed_by"]) + 1)

                user_balance = UserBalance.query.filter_by(
                    user_id=current_user_id
                ).first()
                if not user_balance:
                    user_balance = UserBalance()
                    user_balance.user_id = current_user_id
                    user_balance.balance = 0

                user_balance.balance += expense.amount - share_amount
                db.session.add(user_balance)
                db.session.commit()

                for user_id in kwargs["owed_by"]:
                    expense.owed_by.append(user_id)

                    user_balance = UserBalance.query.filter_by(user_id=user_id).first()
                    if not user_balance:
                        user_balance = UserBalance()
                        user_balance.user_id = user_id
                        user_balance.balance = 0

                    user_transaction = UserTransaction()
                    user_transaction.payer_id = current_user_id
                    user_transaction.recipient_id = user_id
                    user_transaction.expense_id = expense.id
                    user_transaction.amount = share_amount
                    user_transaction.description = expense.description
                    user_transaction.created_at = time.strftime("%Y-%m-%d")

                    user_balance.balance -= share_amount
                    db.session.add(user_transaction)
                    db.session.add(user_balance)
                    db.session.commit()

            elif expense.split_type == "PERCENTAGE":
                if sum(kwargs["split_values"]) != 100:
                    return APIResponse().dump(dict(message="Invalid split values")), 400

                for user_id, percentage in zip(
                    kwargs["owed_by"], kwargs["split_values"]
                ):
                    expense.owed_by.append(user_id)

                    user_balance = UserBalance.query.filter_by(user_id=user_id).first()

                    if not user_balance:
                        user_balance = UserBalance()
                        user_balance.user_id = user_id
                        user_balance.balance = 0

                    expense_amount = expense.amount * percentage / 100

                    user_transaction = UserTransaction()
                    user_transaction.payer_id = current_user_id
                    user_transaction.recipient_id = user_id
                    user_transaction.expense_id = expense.id
                    user_transaction.amount = expense_amount
                    user_transaction.description = expense.description
                    user_transaction.created_at = time.strftime("%Y-%m-%d")

                    if user_id == current_user_id:
                        user_balance.balance += expense_amount
                    else:
                        user_balance.balance -= expense_amount

                    db.session.add(user_transaction)
                    db.session.add(user_balance)
                    db.session.commit()

            elif expense.split_type == "EXACT":
                if sum(kwargs["split_values"]) != expense.amount:
                    return APIResponse().dump(dict(message="Invalid split values")), 400

                for user_id, amount in zip(kwargs["owed_by"], kwargs["split_values"]):
                    expense.owed_by.append(user_id)

                    user_balance = UserBalance.query.filter_by(user_id=user_id).first()
                    if not user_balance:
                        user_balance = UserBalance()
                        user_balance.user_id = user_id
                        user_balance.balance = 0

                    user_transaction = UserTransaction()
                    user_transaction.payer_id = current_user_id
                    user_transaction.recipient_id = user_id
                    user_transaction.expense_id = expense.id
                    user_transaction.amount = amount
                    user_transaction.description = expense.description
                    user_transaction.created_at = time.strftime("%Y-%m-%d")

                    if user_id == current_user_id:
                        user_balance.balance += amount
                    else:
                        user_balance.balance -= amount

                    db.session.add(user_transaction)
                    db.session.add(user_balance)
                    db.session.commit()

            db.session.add(expense)
            db.session.commit()
            return APIResponse().dump(
                {"message": "Expense created successfully", "data": expense.to_dict()},
                200,
            )
        except Exception as e:
            return APIResponse().dump(dict(message=str(e))), 500

    @doc(description="Get Expense API", tags=["Get Expense API"])
    @marshal_with(APIResponse)  # marshalling
    @login.user_loader
    def get(self):
        try:
            expenses = Expense.query.filter_by(paid_by=current_user.get_id()).all()
            return APIResponse().dump(
                dict(
                    message="Expenses fetched successfully",
                    data=[expense.to_dict() for expense in expenses],
                )
            )
        except Exception as e:
            return APIResponse().dump(dict(message=str(e))), 500

api.add_resource(ExpenseAPI, "/expenses")
docs.register(ExpenseAPI)


class ExpenseDetailsAPI(MethodResource, Resource):
    @doc(description="Get Expense Details API", tags=["Get Expense Details API"])
    @marshal_with(APIResponse)  # marshalling
    @login.user_loader
    def get(self, expense_id):
        try:
            expense = Expense.query.filter_by(id=expense_id).first()
            if not expense:
                return (
                    APIResponse().dump(dict(message="Expense not found")),
                    404,
                )

            if current_user.get_id() != expense.paid_by:
                return (
                    APIResponse().dump(dict(message="You are not allowed to view")),
                    403,
                )

            return APIResponse().dump(
                dict(
                    message="Expense fetched successfully",
                    data=expense.to_dict(),
                )
            )
        except Exception as e:
            return APIResponse().dump(dict(message=str(e))), 500

    @doc(description="Delete Expense API", tags=["Delete Expense API"])
    @marshal_with(APIResponse)  # marshalling
    @login.user_loader
    def delete(self, expense_id):
        try:
            expense = Expense.query.filter_by(id=expense_id).first()
            if not expense:
                return (
                    APIResponse().dump(dict(message="Expense not found")),
                    404,
                )

            if current_user.get_id() != expense.paid_by:
                return (
                    APIResponse().dump(dict(message="You are not allowed to delete")),
                    403,
                )

            db.session.delete(expense)
            db.session.commit()

            return (
                APIResponse().dump(
                    dict(
                        message="Expense deleted successfully",
                    )
                ),
                200,
            )
        except Exception as e:
            return APIResponse().dump(dict(message=str(e))), 500


api.add_resource(ExpenseDetailsAPI, "/expenses/<int:expense_id>")
docs.register(ExpenseDetailsAPI)


class UserTransactionsAPI(MethodResource, Resource):
    @doc(description="Get User Transactions API", tags=["Get User Transactions API"])
    @marshal_with(APIResponse)  # marshalling
    @login.user_loader
    def get(self):
        try:
            user_transactions = UserTransaction.query.filter_by(
                recipient_id=current_user.get_id()
            ).all()
            return APIResponse().dump(
                dict(
                    message="User transactions fetched successfully",
                    data=[
                        user_transaction.to_dict()
                        for user_transaction in user_transactions
                    ],
                )
            )
        except Exception as e:
            return APIResponse().dump(dict(message=str(e))), 500


api.add_resource(UserTransactionsAPI, "/user/transactions")
docs.register(UserTransactionsAPI)


class UserBalanceAPI(MethodResource, Resource):
    @doc(description="Get User Balance API", tags=["Get User Balance API"])
    @marshal_with(APIResponse)  # marshalling
    @login.user_loader
    def get(self):
        try:
            user_balance = UserBalance.query.filter_by(
                user_id=current_user.get_id()
            ).first()
            if not user_balance:
                return (
                    APIResponse().dump(dict(message="User balance not found")),
                    404,
                )

            return APIResponse().dump(
                dict(
                    message="User balance fetched successfully",
                    data=user_balance.to_dict(),
                )
            )
        except Exception as e:
            return APIResponse().dump(dict(message=str(e))), 500


api.add_resource(UserBalanceAPI, "/user/balance")
docs.register(UserBalanceAPI)


class CreateTransactionAPI(MethodResource, Resource):
    @doc(description="Create Transaction API", tags=["Create Transaction API"])
    @use_kwargs(UserTransactionSchema, location=("json"))
    @marshal_with(APIResponse)  # marshalling
    @login.user_loader
    def post(self, **kwargs):
        try:
            user_transaction = UserTransaction()
            user_transaction.payer_id = current_user.get_id()
            user_transaction.recipient_id = kwargs["recipient_id"]
            user_transaction.amount = kwargs["amount"]
            user_transaction.description = kwargs["description"]
            user_transaction.created_at = time.strftime("%Y-%m-%d")

            user_balance = UserBalance.query.filter_by(
                user_id=current_user.get_id()
            ).first()
            
            if not user_balance:
                user_balance = UserBalance()
                user_balance.user_id = current_user.get_id()
                user_balance.balance = 0

            user_balance.balance -= kwargs["amount"]
            db.session.add(user_balance)
            db.session.add(user_transaction)
            db.session.commit()

            user_balance = UserBalance.query.filter_by(
                user_id=kwargs["recipient_id"]
            ).first()
            if not user_balance:
                user_balance = UserBalance()
                user_balance.user_id = kwargs["recipient_id"]
                user_balance.balance = 0

            user_balance.balance += kwargs["amount"]
            db.session.add(user_balance)
            db.session.commit()

            return (
                APIResponse().dump(
                    dict(
                        message="Transaction created successfully",
                        data=user_transaction.to_dict(),
                    )
                ),
                200,
            )
        except Exception as e:
            return APIResponse().dump(dict(message=str(e))), 500


api.add_resource(CreateTransactionAPI, "/transactions")
docs.register(CreateTransactionAPI)
