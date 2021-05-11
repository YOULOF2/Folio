from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy import PickleType

import os
from sqlalchemy_json import MutableJson
from dotenv import load_dotenv

load_dotenv()

HASHING_METHOD = "pbkdf2:sha256"
SALT_TIMES = 8
APP_SECRET_KEY = os.environ.get("APP_SECRET_KEY")
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///Folio-database.db")
follow_BACKBONE = {'following': [], 'followed-by': []}

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
    user_folios = db.Column(MutableList.as_mutable(PickleType), nullable=False, default=[])
    social_media = db.Column(MutableList.as_mutable(PickleType), nullable=False, default=[])
    following_and_followers = db.Column(MutableJson, nullable=False, default=follow_BACKBONE)
    admin_privilages = db.Column(db.Boolean, nullable=False)


def add_follower(follower_id: int, followed_id: int):
    followed_user = User.query.get(followed_id)
    followed_followers_list = [follower for follower in followed_user.following_and_followers.get("followed-by")]
    followed_followers_list.append(follower_id)
    followed_following_list = [follower for follower in followed_user.following_and_followers.get("following")]
    followed_user.following_and_followers = {'following': followed_following_list,
                                             'followed-by': followed_followers_list}

    follower_user = User.query.get(follower_id)
    follower_followers_list = [follower for follower in follower_user.following_and_followers.get("followed-by")]
    follower_following_list = [follower for follower in follower_user.following_and_followers.get("following")]
    follower_following_list.append(followed_id)
    follower_user.following_and_followers = {'following': follower_following_list,
                                             'followed-by': follower_followers_list}
    db.session.commit()


def remove_follower(followed_id: int, follower_id: int):
    followed_user = User.query.get(followed_id)
    if len(followed_user.following_and_followers.get("following")) != 0:
        followed_followers_list = [follower for follower in followed_user.following_and_followers.get("followed-by")]
        followed_following_list = [follower for follower in followed_user.following_and_followers.get("following")]
        followed_following_list.remove(follower_id)
        followed_user.following_and_followers = {'following': followed_following_list,
                                                 'followed-by': followed_followers_list}

        follower_user = User.query.get(follower_id)
        follower_followers_list = [follower for follower in follower_user.following_and_followers.get("followed-by")]
        follower_followers_list.remove(followed_id)
        follower_following_list = [follower for follower in follower_user.following_and_followers.get("following")]
        follower_user.following_and_followers = {'following': follower_following_list,
                                                 'followed-by': follower_followers_list}
        db.session.commit()
