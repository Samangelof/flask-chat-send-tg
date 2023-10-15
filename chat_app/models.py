from flask_sqlalchemy import SQLAlchemy
import random
import string


db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(50), unique=True, nullable=True)
    phone = db.Column(db.String(15), unique=True, nullable=True)
    rebound_telegrams = db.relationship('Channel', backref='user', lazy='dynamic')

# class Manager(db.Model):
#     ...


class Channel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    link = db.Column(db.String(100), unique=True, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user_name = db.Column(db.String(100))
    
def generate_unique_channel_link():
    while True:
        name = ''.join(random.choices(string.ascii_letters, k=10))
        if not Channel.query.filter_by(link=name).first():
            return name

class ReboundTelegram(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name_user = db.Column(db.String(100))
    email_user = db.Column(db.String(50))
    phone_user = db.Column(db.String(15))
    link_chat = db.Column(db.String(100))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='rebound_telegram_user')

    channel_id = db.Column(db.Integer, db.ForeignKey('channel.id'))
    channel = db.relationship('Channel', backref='rebound_telegram_channel')
