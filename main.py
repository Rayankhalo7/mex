from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from app.admin.routes import admin_bp
from app.client.routes import client_bp
from app.user.routes import user_bp
from app.admin.models import db as admin_db
from app.client.models import db as client_db
from app.user.models import db as user_db

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SECRET_KEY'] = 'mysecret'

# Initialisiere Datenbanken
admin_db.init_app(app)
client_db.init_app(app)
user_db.init_app(app)

# Flask-Login initialisieren
login_manager = LoginManager()
login_manager.init_app(app)

# Blueprints registrieren
app.register_blueprint(admin_bp)
app.register_blueprint(client_bp)
app.register_blueprint(user_bp)

if __name__ == '__main__':
    app.run(debug=True)
