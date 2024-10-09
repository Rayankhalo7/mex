# app/models/rating.py #Bewertung von restaurants
from app import db
from datetime import datetime

class Rating(db.Model):
    __tablename__ = 'rating'

    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)  # Bewertung (1 bis 5 Sterne)
    comment = db.Column(db.Text, nullable=True)  # Kommentar
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # Beziehung zur Benutzer
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False) #Beziehung zur Client

    # Beziehung zu anderen Modellen
    client = db.relationship('Client', backref='client_reviews') 
    user = db.relationship('User', backref=db.backref('user_ratings', lazy=True))

    def __repr__(self):
        return f"<Rating {self.rating} for Client {self.client_id}>"
