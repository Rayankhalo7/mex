from app import db

class Banner(db.Model):
    __tablename__ = 'banner'  # Tabellennamen in Datenbanken
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(150), nullable=False)  
    url = db.Column(db.String(255), nullable=True)  
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)  # Beziehung zur Client

    # Beziehung zur Client, jeder Client hat eigener Banner
    client = db.relationship('Client', backref=db.backref('banner_client', lazy=True))