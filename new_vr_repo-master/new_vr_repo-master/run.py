import os
import requests

from flask import Flask, render_template
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy



app = Flask(__name__, template_folder='dist', static_folder='dist')
api = Api(app)
cors = CORS(app, resources={r'/*': {'origins': '*'}})

POSTGRES = {
    'user': os.environ['DATABASE_USER'],
    'pw': os.environ['DATABASE_PASSWORD'],
    'db': os.environ['DATABASE_NAME'],
    'host': os.environ['DATABASE_HOST'],
    'port': '5432',
}

DATABASE_URL = 'postgresql://{user}:{pw}@{host}:{port}/{db}'
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL.format(**POSTGRES)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
app.config['CORS_HEADERS'] = 'Content-Type'

db = SQLAlchemy(app)
db.create_all()

app.config['JWT_SECRET_KEY'] = os.environ['JWT_SECRET_KEY']
app.config['JWT_BLACKLIST_ENABLED'] = True
app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']

jwt = JWTManager(app)

@jwt.token_in_blacklist_loader
def check_if_token_in_blacklist(decrypted_token):
    jti = decrypted_token['jti']
    return models.RevokedTokenModel.is_jti_blacklisted(jti)

import models
import resources

api.add_resource(resources.UserRegistration, '/registration')
api.add_resource(resources.UserLogin, '/token')
api.add_resource(resources.UserLogoutAccess, '/logout/access')
api.add_resource(resources.UserLogoutRefresh, '/logout/refresh')
api.add_resource(resources.TokenRefresh, '/token/refresh')
api.add_resource(resources.AllUsers, '/users')
api.add_resource(resources.SecretResource, '/secret')
api.add_resource(resources.SearchBuilding, '/search')
api.add_resource(resources.MLBuildingPrediction, '/predict')
api.add_resource(resources.FloorDetails, '/floordetails')
api.add_resource(resources.MlsListings, '/mlslistings')

@app.shell_context_processor
def make_shell_context():
    return dict(
        db=db,
        UserModel=models.UserModel,
        CityModel=models.CityModel,
        DistrictModel=models.DistrictModel,
        NeighborhoodModel=models.NeighborhoodModel,
        LandModel=models.LandModel,
        JibgaegeuModel=models.JibgaegeuModel,
    )

if __name__ == "__main__":
    app.run()
