from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

import os
from sqlalchemy_json import MutableJson
from dotenv import load_dotenv

load_dotenv()

HASHING_METHOD = "pbkdf2:sha256"
SALT_TIMES = 8
APP_SECRET_KEY = os.environ.get("APP_SECRET_KEY")
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///Folio-database.db")
FOLIO_JOINER = ","
# Initialize app
app = Flask(__name__)
app.config['SECRET_KEY'] = APP_SECRET_KEY
# Connect db to app
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(250), nullable=False)
    password_encrypted = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(250), nullable=False, unique=True)
    realname = db.Column(db.String(250), nullable=False)
    user_folios = db.Column(db.String(250), nullable=False)
    admin_privilages = db.Column(db.Boolean, nullable=False)
    additional_json = db.Column(MutableJson, nullable=False)


def get_user_folios(user_id):
    user = User.query.get(user_id)
    return user.user_folios.split(FOLIO_JOINER)


def write_user_folios(user_id: int, folio_list: list):
    user = User.query.get(user_id)
    user.user_folios = FOLIO_JOINER.join(folio_list)
    db.session.commit()


def get_additional_details(user_id: int):
    user = User.query.get(user_id)
    return user.additional_json


def write_additional_details(user_id: int, json_data: dict):
    user = User.query.get(user_id)
    user.additional_json = json_data
    db.session.commit()

