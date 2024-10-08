from app import db

class Lieferzeiten(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    zeit_von = db.Column(db.Time, nullable=False)           # Lieferzeit von
    zeit_bis = db.Column(db.Time, nullable=False)           # Lieferzeit bis
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)

    def __repr__(self):
        return f"<Lieferzeiten von {self.zeit_von} bis {self.zeit_bis}>"
