from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role          = db.Column(db.String(20), nullable=False)
    name          = db.Column(db.String(100), nullable=False)
    email         = db.Column(db.String(100), nullable=True)   # added for profile
    contact       = db.Column(db.String(50), nullable=True)
    status        = db.Column(db.String(20), default='approved')

    assigned_treks = db.relationship('Trek', backref='staff', lazy=True)
    bookings       = db.relationship('Booking', backref='trekker', lazy=True)


class Trek(db.Model):
    __tablename__ = 'trek'
    id               = db.Column(db.Integer, primary_key=True)
    name             = db.Column(db.String(100), nullable=False)
    location         = db.Column(db.String(100), nullable=False)
    difficulty       = db.Column(db.String(20), nullable=False)
    duration         = db.Column(db.Integer, nullable=False)
    available_slots  = db.Column(db.Integer, nullable=False)
    status           = db.Column(db.String(20), default='Open')
    start_date       = db.Column(db.Date, nullable=False)
    end_date         = db.Column(db.Date, nullable=False)
    assigned_staff_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    bookings = db.relationship('Booking', backref='trek', lazy=True)


class Booking(db.Model):
    __tablename__ = 'booking'
    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    trek_id      = db.Column(db.Integer, db.ForeignKey('trek.id'), nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    status       = db.Column(db.String(20), default='Booked')
    attendance   = db.Column(db.String(20), default='Not Marked')  # added for staff attendance
