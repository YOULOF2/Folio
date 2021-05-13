from flask import Flask, jsonify, render_template, request, send_from_directory, abort, Response
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
SOCIALMEDIA_APPS = ["facebook", "instagram", "twitter", "tiktok", "snapchat"]

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


def get_user_details(user_obj: User):
    """
    :param user_obj:
    :return json:
    """
    response = {
        "username": user_obj.username,
        "email": user_obj.email,
        "real_name": user_obj.realname,
        "user_folios": user_obj.user_folios,
        "social_media": user_obj.social_media,
        "f_f": user_obj.following_and_followers,
        "admin_privilages": user_obj.admin_privilages
    }
    return return_message(response)


def return_message(message):
    return jsonify(response=message)


@app.route("/user/new_user", methods=["POST"])
def create_user():
    email = request.args.get("email")
    print(User.query.filter_by(email=email).first())
    if User.query.filter_by(email=email).first() is not None:
        print("USER IS REGISTERED")
        return return_message("user already registered")
    else:
        print("USER NOT FOUND")
        username = request.args.get("username")
        password = request.args.get("password")
        real_name = request.args.get("name")
        social_media = [{sm: request.args.get(sm)} for sm in SOCIALMEDIA_APPS if request.args.get(sm) is not None]
        encrypted_password = generate_password_hash(password=password, method=HASHING_METHOD, salt_length=SALT_TIMES)
        new_user = User(
            username=username,
            password_encrypted=encrypted_password,
            email=email,
            realname=real_name,
            social_media=social_media,
            admin_privilages=False
        )
        db.session.add(new_user)
        db.session.commit()
        return get_user_details(new_user)


@app.route("/user/delete", methods=["POST"])
def delete_user():
    user_id = request.args.get("id")
    user = User.query.get(user_id)
    db.session.delete(user)
    db.session.commit()
    return return_message("user deleted")


@app.route("/user/authenticate", methods=["GET"])
def authenticate_user():
    email = request.args.get("email")
    password = request.args.get("password")
    user = User.query.filter_by(email=email).first()
    if user is not None:
        password_correct = check_password_hash(user.password_encrypted, password)
        if password_correct:
            return get_user_details(user)
        else:
            return return_message("wrong password")
    else:
        return return_message("user not found")


@app.route("/user/search", methods=["GET"])
def search_user():
    search_item = request.args.get("query")
    found_username = User.query.filter_by(username=search_item).first()
    found_realname = User.query.filter_by(realname=search_item).first()
    found_email = User.query.filter_by(email=search_item).first()
    print(f"{found_username}\n{found_email}\n{found_realname}")
    if found_username is not None:
        return get_user_details(found_username)
    elif found_realname is not None:
        return get_user_details(found_realname)
    elif found_email is not None:
        return get_user_details(found_email)
    else:
        return return_message("user not found")


if "__main__" == __name__:
    app.run(debug=True)
