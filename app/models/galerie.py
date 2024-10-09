# app/models/galerie.py

from app import db

# Datenbank zur Galerie Bilder von client
class Galerie(db.Model):
    __tablename__ = 'galerie'
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(150), nullable=False)  
    description = db.Column(db.String(255), nullable=True)  
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False) # Client als Fremdschlüssel



    # beziehung zur Client
    client = db.relationship('Client', backref=db.backref('galerie_client', lazy=True))
