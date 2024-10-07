from app import db

class Galerie(db.Model):
    __tablename__ = 'galerie'
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(150), nullable=False)  # Pfad zum Bild
    description = db.Column(db.String(255), nullable=True)  # Beschreibung des Bildes (optional)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)  # Beziehung zu Client

    # Beziehung zu Client mit einem eindeutigen `backref`
    client = db.relationship('Client', backref=db.backref('galerie_client', lazy=True))
