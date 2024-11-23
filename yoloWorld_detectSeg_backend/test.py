import logging

import sqlalchemy
from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate

import config
from database_models import ServiceModel, WorkOrderModel, MemberModel, ServiceLogModel
from extensions import db

app = Flask(__name__)
app.config.from_object(config)
db.init_app(app)
migrate = Migrate(app, db)
CORS(app, supports_credentials=True)
with app.app_context():
    print(ServiceModel.query.first().to_dict())
    print(WorkOrderModel.query.first().to_dict())
    print(MemberModel.query.first().to_dict())
    print(ServiceLogModel.query.first().to_dict())

