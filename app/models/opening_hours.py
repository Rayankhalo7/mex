# app/models/opening_hours.py
from app import db

class OpeningHours(db.Model):
    __tablename__ = 'opening_hours'
    id = db.Column(db.Integer, primary_key=True)
    day_of_week = db.Column(db.String(20), nullable=False)  # z.B., Montag, Dienstag, etc.
    open_time = db.Column(db.Time, nullable=False)  # Öffnungszeit
    close_time = db.Column(db.Time, nullable=False)  # Schließzeit
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)  # Verknüpfung zum Client
