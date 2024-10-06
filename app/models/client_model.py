# app/models/client_model.py
import hashlib
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from app import db  # Importiere die 'db' Instanz aus der App
from hashlib import md5

# Datenbanken Models - Nur für client
class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    clientname = db.Column(db.String(25), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    
    # Felder in Datenbanken als optionale Felder
    photo = db.Column(db.String(150), nullable=True)  # Bildpfad optional
    street = db.Column(db.String(100), nullable=True)  # Straße optional
    house_number = db.Column(db.String(10), nullable=True)  # Hausnummer optional
    postal_code = db.Column(db.String(10), nullable=True)  # PLZ optional
    city = db.Column(db.String(50), nullable=True)  # Ort optional
    
    phone_number = db.Column(db.String(20), nullable=True)  # Telefonnummer optional
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Status der Clients
    status = db.Column(db.Integer, default=1)  # 1 = aktiv, 0 = inaktiv

    def set_password(self, password):
        # Verwende hashlib, um den md5-Hash zu generieren
        md5_hash = hashlib.md5(password.encode()).hexdigest()
        self.password_hash = f'md5${md5_hash}'  # Speichere den Hash mit einem Präfix, um ihn zu identifizieren

    def check_password(self, password):
        # Extrahiere den gespeicherten md5-Hash und vergleiche
        stored_md5_hash = self.password_hash.split('$')[1]
        return stored_md5_hash == hashlib.md5(password.encode()).hexdigest()

