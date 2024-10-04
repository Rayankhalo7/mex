# app/models/user_model.py
from flask_login import UserMixin
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from app import db  # Importiere die 'db' Instanz aus der App

# Datenbanken Models - Nur für User
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    
    # Adresse als optionale Felder
    street = db.Column(db.String(100), nullable=True)  # Straße optional
    house_number = db.Column(db.String(10), nullable=True)  # Hausnummer optional
    postal_code = db.Column(db.String(10), nullable=True)  # PLZ optional
    city = db.Column(db.String(50), nullable=True)  # Ort optional
    
    phone_number = db.Column(db.String(20), nullable=True)  # Telefonnummer optional

    # Neue Spalte für das Benutzerprofilbild
    photo = db.Column(db.String(200), nullable=True)  # Bildpfad oder Name der Bilddatei

    # Spalte für den Status des Benutzers (z.B. active, inactive, suspended)
    status = db.Column(db.String(20), default='active', nullable=False)

    # Automatisch den Erstellungszeitpunkt speichern
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def set_password(self, password):
        """
        Setzt das Passwort mit MD5-Verschlüsselung.
        """
        # Erstelle einen md5-Hash des Passworts und speichere ihn
        self.password_hash = hashlib.md5(password.encode()).hexdigest()

    def check_password(self, password):
        """
        Überprüft das Passwort mit MD5-Verschlüsselung.
        """
        # Vergleiche das eingegebene Passwort nach md5-Verschlüsselung mit dem gespeicherten Hash
        return self.password_hash == hashlib.md5(password.encode()).hexdigest()

    # Überprüfe, ob der Benutzer aktiv ist
    @property
    def is_active(self):
        """Überprüft, ob der Benutzerstatus 'active' ist."""
        return self.status == 'active'

    def __repr__(self):
        return f'<User {self.username}>'
