# app/models/user_model.py
from flask_login import UserMixin
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from app import db  # Importiere die 'db' Instanz aus der App

# Datenbanken für User # also Kunde
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    
    # Adresse des Kundes
    street = db.Column(db.String(100), nullable=True)  # Straße 
    house_number = db.Column(db.String(10), nullable=True)  # Hausnummer 
    postal_code = db.Column(db.String(10), nullable=True)  # PLZ 
    city = db.Column(db.String(50), nullable=True)  # Ort 
    
    phone_number = db.Column(db.String(20), nullable=True)  # Telefonnummer 

    # Benutzerprofilbild
    photo = db.Column(db.String(200), nullable=True) 

    # Status des Benutzers (active, inactive, suspended)
    status = db.Column(db.String(20), default='active', nullable=False)

    # Registerierungszeit speichern
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    user_orders = db.relationship('Order', backref='order_user', lazy=True)

    def set_password(self, password):
        """
        Setzt das Passwort mit MD5-Verschlüsselung.
        """
        # Erstelle einen md5-Hash des Passworts und speichere ihn als hashpasswort
        self.password_hash = hashlib.md5(password.encode()).hexdigest()

    def check_password(self, password):
        """
        Überprüft das Passwort mit MD5-Verschlüsselung.
        """
        # Vergleiche das eingegebene Passwort nach md5-Verschlüsselung mit dem gespeicherten Hash
        return self.password_hash == hashlib.md5(password.encode()).hexdigest()

    # Überprüft, ob der Benutzer aktiv ist
    @property
    def is_active(self):
        """Überprüft, ob der Benutzerstatus 'active' ist."""
        return self.status == 'active'

    def __repr__(self):
        return f'<User {self.username}>'