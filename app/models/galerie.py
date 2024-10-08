# app/models/galerie.py

from app import db

# Datenbank zur Galerie Bilder
class Galerie(db.Model):
    __tablename__ = 'galerie'
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(150), nullable=False)  
    description = db.Column(db.String(255), nullable=True)  
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False) 


    client = db.relationship('Client', backref=db.backref('galerie_client', lazy=True))
