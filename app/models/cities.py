# app/models/city.py
from app import db

class City(db.Model):
    __tablename__ = 'cities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    postal_code = db.Column(db.String(20), nullable=False, unique=True)  # PLZ sollte zur Stadt gehören
    latitude = db.Column(db.Float, nullable=False)  # Breitengrad
    longitude = db.Column(db.Float, nullable=False)  # Längengrad

    # Beziehung zu Client (Eine Stadt hat viele Clients)
    client = db.relationship('Client', backref='city_relation', lazy=True)
