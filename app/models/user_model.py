# app/models/user_model.py
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from app import db  # Importiere die 'db' Instanz aus der App

# Datenbanken Models - Nur für User
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    
    # Adresse in einzelne Felder unterteilt
    street = db.Column(db.String(100), nullable=False)  # Straße
    house_number = db.Column(db.String(10), nullable=False)  # Hausnummer
    postal_code = db.Column(db.String(10), nullable=False)  # PLZ
    city = db.Column(db.String(50), nullable=False)  # Ort
    
    # Telefonnummer
    phone_number = db.Column(db.String(20), nullable=True)  # Telefonnummer, optional
    
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())  # Erstellungsdatum

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

