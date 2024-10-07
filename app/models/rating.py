# app/models/rating.py
from app import db
from datetime import datetime

class Rating(db.Model):
    __tablename__ = 'rating'

    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)  # Bewertungswert (1-5 Sterne)
    comment = db.Column(db.Text, nullable=True)  # Optionaler Kommentar
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)

    # Beziehung zu anderen Modellen
    client = db.relationship('Client', backref='client_reviews')  # Geänderter `backref`-Name
    user = db.relationship('User', backref='user_reviews')

    def __repr__(self):
        return f"<Rating {self.rating} for Client {self.client_id}>"
