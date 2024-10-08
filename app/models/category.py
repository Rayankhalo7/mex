#app/models/category.py

from app import db

class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False) # Beziehung zur Client also Restaurant
    products = db.relationship('Product', backref='category', lazy=True)
