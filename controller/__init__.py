from flask_login import LoginManager
from flask_marshmallow import Marshmallow
from flask_restful import Api
from flask_apispec.extension import FlaskApiSpec


api = Api()
docs = FlaskApiSpec()
ma = Marshmallow()
login = LoginManager()
login.session_protection = "strong"
login.login_view = "login"
login.login_message_category = "info"
