from app import create_app, db
from flask_migrate import Migrate
from flask import render_template
from app.models.client_model import Client

# App erstellen
app = create_app()


# Home-Route
@app.route("/")
def home():
    clients = Client.query.filter_by(status=1).all()
    return render_template('frontend/home.html', clients=clients)

# Initializierung für Flask-Migrate
migrate = Migrate(app, db)

if __name__ == "__main__":
    with app.app_context():
        # Erstellen von Datenbaneken
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5001)
