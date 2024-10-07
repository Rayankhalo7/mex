# app/models/banner.py

from app import db

class Banner(db.Model):
    __tablename__ = 'banner'  # Tabellennamen explizit angeben
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(150), nullable=False)  # Pfad zum Bild relativ zu 'static'
    url = db.Column(db.String(255), nullable=True)  # URL, auf die das Banner verlinkt
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)  # Beziehung zu Client

    # Beziehung zu Client definieren, mit einem eindeutigen backref-Namen
    client = db.relationship('Client', backref=db.backref('banner_client', lazy=True))  # Ändere den `backref` Namen zu `banner_client`
