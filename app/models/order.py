# app/models/order.py
import uuid  # Für die Generierung einer eindeutigen Nummer
from app import db
from datetime import datetime

class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)  # Verbindung zu einem Client
    name = db.Column(db.String(255), nullable=False)  # Name des Käufers
    email = db.Column(db.String(255), nullable=False)  # E-Mail des Käufers
    phone = db.Column(db.String(20), nullable=False)   # Telefonnummer des Käufers
    address = db.Column(db.Text, nullable=False)       # Lieferadresse des Käufers
    payment_type = db.Column(db.String(50), nullable=True)  # Z.B. Barzahlung, Kreditkarte
    payment_method = db.Column(db.String(50), nullable=True)  # Z.B. Paypal, Stripe
    transaction_id = db.Column(db.String(255), nullable=True)  # Transaktions-ID vom Zahlungsdienstleister
    currency = db.Column(db.String(10), nullable=True, default='EUR')  # Standardwährung (z.B. EUR, USD)
    amount = db.Column(db.Float, nullable=False)  # Gesamtkosten der Bestellung
    total_amount = db.Column(db.Float, nullable=False)  # Summe nach Steuern und Rabatten
    order_number = db.Column(db.String(50), nullable=True, unique=True)  # Eindeutige Bestellnummer
    invoice_no = db.Column(db.String(50), nullable=True, unique=True)  # Eindeutige Rechnungsnummer
    order_date = db.Column(db.DateTime, default=datetime.utcnow)  # Datum der Bestellung
    confirmed_date = db.Column(db.DateTime, nullable=True)  # Datum der Bestätigung
    processing_date = db.Column(db.DateTime, nullable=True)  # Datum der Bearbeitung
    shipped_date = db.Column(db.DateTime, nullable=True)  # Datum des Versands
    delivered_date = db.Column(db.DateTime, nullable=True)  # Datum der Lieferung
    canceled_at = db.Column(db.DateTime, nullable=True)  # Datum der Stornierung (falls storniert)
    status = db.Column(db.String(50), nullable=False, default='pending')  # Status der Bestellung (z.B. "pending")
    delivery_time = db.Column(db.Integer, nullable=True)  # Lieferzeit in Minuten
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Beziehung zu den Produkten in der Bestellung (über die Zwischentabelle order_items)
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')

    # Beziehung zum Benutzer und zum Client
    user = db.relationship('User', backref='orders', lazy=True)
    client = db.relationship('Client', backref='client_order_list', lazy=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.order_number:
            self.order_number = self.generate_order_number()
        if not self.invoice_no:
            self.invoice_no = self.generate_invoice_number()

    def generate_order_number(self):
        """
        Generiert eine eindeutige Bestellnummer, die mit 'ORD' beginnt und eine UUID enthält.
        """
        return f"ORD-{uuid.uuid4().hex[:8].upper()}"

    def generate_invoice_number(self):
        """
        Generiert eine eindeutige Rechnungsnummer, die mit 'INV' beginnt und eine UUID enthält.
        """
        return f"INV-{uuid.uuid4().hex[:8].upper()}"

    def __repr__(self):
        return f'<Order {self.order_number}>'
