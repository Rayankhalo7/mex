# app/__init__.py

from flask import Flask, g
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_caching import Cache
from flask_login import LoginManager, current_user
import os
from itsdangerous import URLSafeTimedSerializer
from dotenv import load_dotenv

# Initialisiere den Serializer als globale Variable
serializer = None

# Lade die Umgebungsvariablen aus der .env-Datei
load_dotenv()

# Initialisierung von Extensions
db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
cache = Cache()
login_manager = LoginManager()
login_manager.login_view = "user_bp.login"  # Definiere die Login-Route

def create_app():
    global serializer
    
    app = Flask(__name__, template_folder='templates', static_folder='static')

    # Cache-Konfiguration hinzufügen
    app.config['CACHE_TYPE'] = os.getenv('CACHE_TYPE', 'simple')  # Mögliche Typen: 'redis', 'filesystem', 'memcached', etc.
    app.config['CACHE_DEFAULT_TIMEOUT'] = int(os.getenv('CACHE_DEFAULT_TIMEOUT', 300))  # Optional: Timeout für Cache in Sekunden festlegen
    cache.init_app(app)

    # Konfiguration Secret Key (aus .env laden oder generieren)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", os.urandom(24).hex())

    # Konfiguration Datenbank (aus .env laden)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI", "mysql://root:@localhost/mahlzeit_db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Konfiguration Flask-E-Mail (aus .env laden)
    app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", 587))
    app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS", "True") == "True"
    app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD") 

    # Konfiguration für Datei-Upload
    app.config['CLIENT_UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'upload', 'client_bilder', 'client_profile')
    app.config['ADMIN_UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'upload', 'admin_bilder', 'admin_profile')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB maximale Dateigröße

    # Initialisierung von Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    login_manager.init_app(app)  # Initialisierung von Flask-Login

    # Einstellung URLSafeTimedSerializer für das Generieren von sicheren Tokens
    app.serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])

    # Flask-Login Konfiguration
    login_manager.login_view = "user_bp.login"  # Login-Seite für nicht authentifizierte Benutzer
    login_manager.login_message_category = "info"  # Kategorie für Login-Meldungen

    # Callback-Funktion für Flask-Login: Laden des Benutzers anhand der ID
    from app.models.user_model import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # before_request-Hook, um aktuellen Benutzer global in `g` zu setzen
    @app.before_request
    def before_request():
        g.user = current_user

    serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])

    # Blueprint-Registrierungen innerhalb von `app.app_context()` vornehmen, um Zirkularimporte zu vermeiden
    with app.app_context():
        # Register blueprints für user
        from app.routes.user_routes import user_bp
        app.register_blueprint(user_bp, url_prefix='/user')

        # Register blueprints für Client
        from app.routes.client_routes import client_bp
        app.register_blueprint(client_bp, url_prefix='/client')

        # Register blueprints für Admin
        from app.routes.admin_routes import admin_bp
        app.register_blueprint(admin_bp, url_prefix='/admin')

        # Blueprint für das Frontend (importiere hier, um den Kreislauf zu brechen)
        from app.routes.frontend import frontend_bp
        app.register_blueprint(frontend_bp, url_prefix='/')

        # Registriere Blueprints für Kategorien, Produkte und weitere Module
        from app.routes.category import client_category_bp
        from app.routes.product import client_product_bp
        from app.routes.opening_hours import client_opening_hours_bp  # Importiere das Blueprint für Öffnungszeiten
        from app.routes.rating import rating_bp
        from app.routes.banner import client_banner_bp
        from app.routes.client_galerie import client_galerie_bp
        from app.routes.lieferzeiten import client_lieferzeiten_bp

        app.register_blueprint(client_category_bp, url_prefix='/client')
        app.register_blueprint(client_product_bp, url_prefix='/client')
        app.register_blueprint(client_opening_hours_bp, url_prefix='/client')  # Registriere das Blueprint für Öffnungszeiten
        app.register_blueprint(rating_bp, url_prefix='/client')
        app.register_blueprint(client_banner_bp, url_prefix='/client')
        app.register_blueprint(client_galerie_bp, url_prefix='/client')
        app.register_blueprint(client_lieferzeiten_bp, url_prefix='/client')



        # Registriere Blueprint für Warenkorb-Funktionalität
        from app.routes.add_to_cart import cart_bp  # Importiere den neuen Warenkorb-Blueprint
        app.register_blueprint(cart_bp, url_prefix='/cart')

        from app.routes.checkout import checkout_bp
        app.register_blueprint(checkout_bp, url_prefix='/')


        from app.models.order import Order 
        from app.models.order_item import OrderItem

    return app
