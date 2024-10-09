# app/models/produkt.py
from app import db

class Product(db.Model):
    __tablename__ = 'product'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(255), nullable=True)  # Speichert den Dateinamen des Produktbildes
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)

    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)

    is_must_popular = db.Column(db.Boolean, default=False)  # Produkt gehört zu "Must Popular"
    is_bestseller = db.Column(db.Boolean, default=False)    # Produkt gehört zu "Bestseller"
