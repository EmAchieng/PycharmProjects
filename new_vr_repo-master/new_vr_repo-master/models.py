import json
import re
import uuid

from datetime import datetime
from hashlib import sha512

from sqlalchemy_utils import UUIDType

from run import db
from mlservice.services_prediction import construction_price_pred


class UserModel(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def find_by_username(cls, username):
        return cls.query.filter_by(username=username).first()

    @classmethod
    def return_all(cls):
        def to_json(x):
            return {
                'username': x.username,
                'password': x.password,
            }
        return {'users': list(map(lambda x: to_json(x), UserModel.query.all()))}, 200

    @classmethod
    def delete_all(cls):
        try:
            num_rows_deleted = db.session.query(cls).delete()
            db.session.commit()
            return {'message': '{} row(s) deleted'.format(num_rows_deleted)}, 200
        except:
            return {'message': 'Something went wrong'}, 500

    @staticmethod
    def generate_hash(password):
        return sha512((password+'pilsang is the best').encode()).hexdigest()

    @staticmethod
    def verify_hash(password, hash):
        return True if sha512((password+'pilsang is the best').encode()).hexdigest() == hash else False


class RevokedTokenModel(db.Model):
    __tablename__ = 'revoked_token'
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(150))

    def add(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def is_jti_blacklisted(cls, jti):
        query = cls.query.filter_by(jti=jti).first()
        return bool(query)


class CountryModel(db.Model):
    __tablename__ = 'countries'

    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(64), unique=True, nullable=False)
    code = db.Column(db.Integer, unique=True, nullable=False)
    location = db.Column(db.Text)
    polygon = db.Column(db.Text)

    cities = db.relationship('CityModel', backref='country')


class CityModel(db.Model):
    __tablename__ = 'cities'

    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(64), unique=True, nullable=False)
    code = db.Column(db.Integer, unique=True, nullable=False)
    location = db.Column(db.Text)
    polygon = db.Column(db.Text)

    country_id = db.Column(
        UUIDType, db.ForeignKey('countries.id'), default=uuid.uuid4)

    districts = db.relationship('DistrictModel', backref='city')
    neighborhoods = db.relationship('NeighborhoodModel', backref='city')
    lands = db.relationship('LandModel', backref='city')
    jibgaegeus = db.relationship('JibgaegeuModel', backref='city')


class DistrictModel(db.Model):
    __tablename__ = 'districts'

    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(64), unique=True, nullable=False)
    code = db.Column(db.Integer, unique=True, nullable=False)
    location = db.Column(db.Text)
    polygon = db.Column(db.Text)
    area = db.Column(db.Float)

    city_id = db.Column(
        UUIDType, db.ForeignKey('cities.id'), default=uuid.uuid4)

    neighborhoods = db.relationship('NeighborhoodModel', backref='district')
    lands = db.relationship('LandModel', backref='district')
    jibgaegeus = db.relationship('JibgaegeuModel', backref='district')


class NeighborhoodModel(db.Model):
    __tablename__ = 'neighborhoods'

    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(64), unique=True, nullable=False)
    code = db.Column(db.Integer, unique=True, nullable=False)
    location = db.Column(db.Text)
    polygon = db.Column(db.Text)
    area = db.Column(db.Float)
    
    tx_price_m2 = db.Column(db.Text)
    tx_price_hist = db.Column(db.Text)

    city_id = db.Column(
        UUIDType, db.ForeignKey('cities.id'), default=uuid.uuid4)
    district_id = db.Column(
        UUIDType, db.ForeignKey('districts.id'), default=uuid.uuid4)

    lands = db.relationship('LandModel', backref='neighborhood')
    jibgaegeus = db.relationship('JibgaegeuModel', backref='neighborhood')


class LandModel(db.Model):
    __tablename__ = 'lands'

    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(64), unique=True, nullable=False)
    code = db.Column(db.Integer, unique=True, nullable=False)
    location = db.Column(db.Text)
    polygon = db.Column(db.Text)
    area = db.Column(db.Float)

    land_use = db.Column(db.String(64))
    land_use_code = db.Column(db.Integer)

    price_m2 = db.Column(db.Text)
    price_hist = db.Column(db.Text)

    city_id = db.Column(
        UUIDType, db.ForeignKey('cities.id'), default=uuid.uuid4)
    district_id = db.Column(
        UUIDType, db.ForeignKey('districts.id'), default=uuid.uuid4)
    neighborhood_id = db.Column(
        UUIDType, db.ForeignKey('neighborhoods.id'), default=uuid.uuid4)


class JibgaegeuModel(db.Model):
    __tablename__ = 'jibgaegeus'

    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(64), unique=True, nullable=False)
    code = db.Column(db.Integer, unique=True, nullable=False)
    location = db.Column(db.Text)
    polygon = db.Column(db.Text)
    area = db.Column(db.Float)

    tx_price_m2 = db.Column(db.Text)
    tx_price_hist = db.Column(db.Text)

    city_id = db.Column(
        UUIDType, db.ForeignKey('cities.id'), default=uuid.uuid4)
    district_id = db.Column(
        UUIDType, db.ForeignKey('districts.id'), default=uuid.uuid4)
    neighborhood_id = db.Column(
        UUIDType, db.ForeignKey('neighborhoods.id'), default=uuid.uuid4)


class BuildingModel(db.Model):
    __tablename__ = 'buildings'

    # First 19 are PNU
    building_mngt_number = db.Column(db.String(25), primary_key=True)
    street_addr = db.Column(db.String(50))
    lat = db.Column(db.String(30))
    lon = db.Column(db.String(30))

    store_type_count = db.Column(db.Text)

    year_built = db.Column(db.String(20))
    tot_area = db.Column(db.Float)
    main_structure = db.Column(db.String(50))
    main_usage = db.Column(db.String(50))
    detailed_usage = db.Column(db.String(50))
    roof = db.Column(db.String(50))
    floors_b = db.Column(db.Integer)
    floors_g = db.Column(db.Integer)
    building_coverage = db.Column(db.Float)
    volume_to_lot_ratio = db.Column(db.Float)
    outdoor_parking_lot = db.Column(db.String(50))
    indoor_parking_lot = db.Column(db.String(50))
    passenger_elevator = db.Column(db.String(50))
    emergency_elevator = db.Column(db.String(50))

    land_category = db.Column(db.String(50))
    land_use_sit = db.Column(db.String(50))
    use_area = db.Column(db.String(50))
    land_area = db.Column(db.Float)
    road_side = db.Column(db.String(50))
    topology = db.Column(db.String(50))
    land_angle = db.Column(db.String(50))
    public_price = db.Column(db.Integer)

    last_updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())

    def add(self):
        db.session.add(self)
        db.session.commit()

    def to_dict(self):
        return {
            'status': '200',
            'statusText': 'OK',
            'message': '',
            'Data': {
                'addrInfo': {
                    'street_addr': self.street_addr,
                    'lat': self.lat,
                    'lon': self.lon,
                    'building_mngt_number': self.building_mngt_number
                },
                'buildingInfo': {
                    'year_built': self.year_built,
                    'tot_area': self.tot_area,
                    'main_usage': self.main_usage,
                    'detailed_usage': self.detailed_usage,
                    'main_structure': self.main_structure,
                    'roof': self.roof,
                    'floors_g': self.floors_g,
                    'floors_b': self.floors_b,
                    'building_coverage': self.building_coverage,
                    'volume_to_lot_ratio': self.volume_to_lot_ratio,
                    'outdoor_parking_lot': self.outdoor_parking_lot,
                    'indoor_parking_lot': self.indoor_parking_lot,
                    'passenger_elevator': self.passenger_elevator,
                    'emergency_elevator': self.emergency_elevator
                },
                'landInfo': {
                    'land_category': self.land_category,
                    'land_use_sit': self.land_use_sit,
                    'land_area': self.land_area,
                    'road_side': self.road_side,
                    'use_area': self.use_area,
                    'topology': self.topology,
                    'public_price': self.public_price,
                    'land_angle': self.land_angle
                },
                'storesInfo': json.loads(self.store_type_count)
            }
        }

    def delete_record(self):
        try:
            db.session.delete(self)
            db.session.commit()
            return {'message': 'record deleted'}, 200
        except:
            return {'message': 'Something went wrong'}, 500

    def price_estimation(self, transaction_year):
        addr_to_code = {
            '종로구' : 11110,
            '중구' : 11140,
            '용산구' : 11170,
            '성동구' : 11200,
            '광진구' : 11215,
            '동대문구' : 11230,
            '중랑구' : 11260,
            '성북구' : 11290,
            '강북구' : 11305,
            '도봉구' : 11320,
            '노원구' : 11350,
            '은평구' : 11380,
            '서대문구' : 11410,
            '마포구' : 11440,
            '양천구' : 11470,
            '강서구' : 11500,
            '구로구' : 11530,
            '금천구' : 11545,
            '영등포구' : 11560,
            '동작구' : 11590,
            '관악구' : 11620,
            '서초구' : 11650,
            '강남구' : 11680,
            '송파구' : 11710,
            '강동구' : 11740
        }

        feat_dict = {
            'total_floor_area': self.tot_area,
            'total_floors': self.floors_b+self.floors_g,
            'floors_aboveground': self.floors_g,
            'floors_underground': self.floors_b,
            'total_land_price': self.public_price*self.land_area,
            'structure': self.main_structure,
            'building_main_use': self.main_usage,
            'specific_use': self.detailed_usage,
            'land_use': self.use_area.replace('지역', ''),
            'gu_code': addr_to_code[self.street_addr.split(' ')[1]],
            'dong_name': re.findall('\((.*?)\)', self.street_addr)[-1],
            'construction_year': self.year_built.split('-')[0],
            'transaction_year': str(transaction_year),
        }

        prediction  = construction_price_pred(feat_dict)
        tx_price = feat_dict['total_land_price'] + feat_dict['total_floor_area'] * prediction
        return tx_price

    @classmethod
    def find_by_building_mngt_number(cls, building_mngt_number):
        return cls.query.filter_by(building_mngt_number=building_mngt_number).first()

    @classmethod
    def delete_all(cls):
        try:
            num_rows_deleted = db.session.query(cls).delete()
            db.session.commit()
            return {'message': '{} row(s) deleted'.format(num_rows_deleted)}, 200
        except:
            return {'message': 'Something went wrong'}, 500



