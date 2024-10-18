# app/models/client_model.py
import hashlib
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from app import db 
from hashlib import md5
from app.models.opening_hours import OpeningHours
from app.models.cities import City

# Datenbanken für client
class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    clientname = db.Column(db.String(25), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    
    # Optionale Felder
    photo = db.Column(db.String(150), nullable=True)  
    street = db.Column(db.String(100), nullable=True) 
    house_number = db.Column(db.String(10), nullable=True)  
    postal_code = db.Column(db.String(10), nullable=True)  

    
    
    phone_number = db.Column(db.String(20), nullable=True)  
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Status der Clients
    status = db.Column(db.Integer, default=1)  # bei 1 = aktiv, bei 0 = inaktiv


    # Beziehungen zu anderen Modellen
    categories = db.relationship('Category', backref='client', lazy=True)
    products = db.relationship('Product', backref='client', lazy=True)
    opening_hours = db.relationship('OpeningHours', backref='client', lazy=True, cascade="all, delete-orphan")
    ratings = db.relationship('Rating', backref='client_rating', lazy=True) 
    banners = db.relationship('Banner', backref='banner_client', lazy=True, cascade="all, delete-orphan")
    galerie_images = db.relationship('Galerie', backref='client_galerie', lazy=True, cascade="all, delete-orphan") 
    lieferzeiten = db.relationship('Lieferzeiten', backref='client_lieferzeiten', lazy=True, cascade="all, delete-orphan")
    client_orders = db.relationship('Order', backref='client_for_orders', lazy=True)


    # city_id = db.Column(db.Integer, db.ForeignKey('cities.id'), nullable=False)
    city_id = db.Column(db.Integer, db.ForeignKey('cities.id'), nullable=False)

    city = db.relationship('City', backref='clients')

    def set_password(self, password):
        # Verwende hashlib, um den md5-Hash zu generieren
        md5_hash = hashlib.md5(password.encode()).hexdigest()
        self.password_hash = f'md5${md5_hash}'

    def check_password(self, password):
        # Gespeicherten md5-Hash wie bei Admin
        stored_md5_hash = self.password_hash.split('$')[1]
        return stored_md5_hash == hashlib.md5(password.encode()).hexdigest()
    



# Funktion zur Suche nach Clients basierend auf PLZ
def find_clients_by_postal_code(postal_code):
    city = City.query.filter_by(postal_code=postal_code).first()
    if city:
        return city.clients  # Gibt alle Clients zurück, die zu dieser PLZ gehören
    return None

# Funktion zur Suche nach Clients basierend auf Stadtname
def find_clients_by_city_name(city_name):
    city = City.query.filter_by(name=city_name).first()
    if city:
        return city.clients  # Gibt alle Clients zurück, die zu dieser Stadt gehören
    return None