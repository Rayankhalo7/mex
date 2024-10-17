# app/models/order_item.py
from app import db

class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=True)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)  # Preis pro Produkt in der Bestellung
    total_tax = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # Beziehung zu den Produkten
    product = db.relationship('Product', backref='order_items')

    def calculate_tax(self):
        """
        Berechnet die Steuer für das Produkt basierend auf dem `tax_rate` des Produkts.
        """
        tax_rate = self.product.tax_rate / 100  # Steuerprozentsatz in Dezimal umwandeln
        return self.price * tax_rate

    def calculate_total(self):
        """
        Berechnet den Gesamtpreis (Brutto) des Produkts inklusive Steuer.
        """
        return self.price + self.calculate_tax()

    def __repr__(self):
        return f'<OrderItem {self.id}, Order {self.order_id}, Product {self.product_id}>'
