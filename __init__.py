import os

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from flask import Flask, jsonify

from .controller import api, ma, docs, login
from .controller.user_routes import user_routes
from .controller.expense_routes import expense_routes
from .models import db


base_dir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)


app.config["DEBUG"] = True
app.config["ENV"] = "development"
app.config["FLASK_ENV"] = "development"
app.config["SECRET_KEY"] = "ItShouldBeALongStringOfRandomCharacters"
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://root:Root.123@127.0.0.1:3306/splitwise"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True


db.init_app(app)
ma.init_app(app)
api.init_app(app)
docs.init_app(app)
login.init_app(app)

app.register_blueprint(user_routes)
app.register_blueprint(expense_routes)

app.config.update(
    {
        "APISPEC_SPEC": APISpec(
            title="Splitwise Clone APIs",
            version="v1",
            plugins=[MarshmallowPlugin()],
            openapi_version="2.0.0",
        ),
        "APISPEC_SWAGGER_URL": "/swagger/",  # URI to access API Doc JSON
        "APISPEC_SWAGGER_UI_URL": "/swagger-ui/",  # URI to access UI of API Doc
    }
)

if __name__ == "__main__":
    db.create_all()
    db.session.commit()
    app.run(debug=True)
