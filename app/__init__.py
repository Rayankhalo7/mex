from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
import os
from itsdangerous import URLSafeTimedSerializer

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
mail = Mail()

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')

    
    
    # Secret key configuration
    app.config["SECRET_KEY"] = os.urandom(24)

    # Database configuration
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///mahlzeit.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Flask-Mail configuration
    app.config["MAIL_SERVER"] = "smtp.gmail.com"
    app.config["MAIL_PORT"] = 587
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USERNAME"] = 'expressmahlzeit@gmail.com'
    app.config["MAIL_PASSWORD"] = 'albl ddwj xvdn junn'
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    # Set up URLSafeTimedSerializer for generating secure tokens
    app.serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])

    # Register blueprints
    from app.routes.user_routes import user_bp
    app.register_blueprint(user_bp, url_prefix='/user')

    return app
