from flask import Blueprint, jsonify
from marshmallow import Schema, fields
from flask_restful import Resource, Api
from flask_apispec.views import MethodResource
from flask_apispec import marshal_with, doc, use_kwargs
from flask_login import current_user, login_user, logout_user, login_required

from ..models import db, User
from ..controller import api, ma, docs, login


class APIResponse(Schema):
    message = fields.Str(default="Success")
    data = fields.Dict(default={})


class UserSchema(ma.Schema):
    class Meta:
        model = User
        fields = ("id", "username", "name", "email", "mobile_number")


class SignUpRequest(ma.Schema):
    class Meta:
        model = User
        fields = ("username", "name", "email", "mobile_number", "password")


user_schema = UserSchema()


class LoginRequest(ma.Schema):
    class Meta:
        model = User
        fields = ("username", "password")


# Create a Blueprint for users
user_routes = Blueprint("user_routes", __name__, url_prefix="/api/users")


class SignUpAPI(MethodResource, Resource):
    @doc(description="Sign Up API", tags=["SignUp API"])
    @use_kwargs(SignUpRequest, location=("json"))
    @marshal_with(APIResponse)  # marshalling
    def post(self, **kwargs):
        try:
            user = User(
                kwargs["username"],
                kwargs["name"],
                kwargs["email"],
                kwargs["mobile_number"],
                kwargs["password"],
            )

            db.session.add(user)
            db.session.commit()
            login_user(user)
            return (
                APIResponse().dump(
                    dict(
                        message="User is successfully registerd",
                        data=user_schema.dump(user),
                    )
                ),
                200,
            )
        except Exception as e:
            print(str(e))
            return (
                APIResponse().dump(
                    dict(message=f"Not able to register User : {str(e)}")
                ),
                400,
            )


api.add_resource(SignUpAPI, "/signup")
docs.register(SignUpAPI)


class LoginAPI(MethodResource, Resource):
    @doc(description="Login API", tags=["Login API"])
    @use_kwargs(LoginRequest, location=("json"))
    @marshal_with(APIResponse)  # marshalling
    @login.user_loader
    def post(self, **kwargs):
        try:
            user = User.query.filter_by(username=kwargs["username"]).first()
            if user and user.check_password(kwargs["password"]):
                user.authenticated = True
                db.session.add(user)
                db.session.commit()
                login_user(user, force=True, remember=True)
                return (
                    APIResponse().dump(
                        dict(
                            message="User is successfully logged in",
                            data=user_schema.dump(user),
                        )
                    ),
                    200,
                )
            else:
                return (
                    APIResponse().dump(dict(message=f"Invalid username or password")),
                    400,
                )
        except Exception as e:
            print(str(e))
            return (
                APIResponse().dump(dict(message=f"Not able to login : {str(e)}")),
                400,
            )


api.add_resource(LoginAPI, "/login")
docs.register(LoginAPI)


class LogoutAPI(MethodResource, Resource):
    @doc(description="Logout API", tags=["Logout API"])
    @marshal_with(APIResponse)  # marshalling
    @login.user_loader
    def post(self, **kwargs):
        try:
            logout_user()
            return (
                APIResponse().dump(
                    dict(
                        message="User is successfully logged out",
                    )
                ),
                200,
            )
        except Exception as e:
            print(str(e))
            return (
                APIResponse().dump(dict(message=f"Not able to logout : {str(e)}")),
                400,
            )


api.add_resource(LogoutAPI, "/logout")
docs.register(LogoutAPI)