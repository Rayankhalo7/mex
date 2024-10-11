# app/models/city.py

from app import db

class City(db.Model):
    __tabelename__ = 'city'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    plz = db.Column(db.Integer, db.ForeignKey('client_postal_code'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client_id'), nullable=False)
