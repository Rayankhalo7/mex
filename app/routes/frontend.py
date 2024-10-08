# app/routes/frontend.py

from flask import Blueprint, render_template, request, abort
from app.models.client_model import Client
from app.models.user_model import User
from app import db
from flask_login import current_user
from app.models.banner import Banner
from app.models.rating import Rating
from datetime import datetime

# Blueprint für das Frontend erstellen
frontend_bp = Blueprint('frontend_bp', __name__, template_folder='templates/frontend')

# Route für die Startseite
@frontend_bp.route('/')
def home():
    # Alle Clients aus der Datenbank abrufen
    clients = Client.query.all()
    # Überprüfen, ob Clients vorhanden sind
    if not clients:
        return render_template('frontend/no_clients.html')  # Falls keine Clients vorhanden sind, andere Seite anzeigen

    return render_template('frontend/home.html', clients=clients)

# Route für die Client-Detailseite
@frontend_bp.route('/client/<int:client_id>')
def client_detail(client_id):
    # Spezifischen Client anhand der ID abrufen
    client = Client.query.get_or_404(client_id)

    # Überprüfen, ob der Client Bewertungen hat und diese abrufen
    ratings = client.ratings if hasattr(client, 'ratings') else []
    total_ratings = len(ratings)

    # Berechne die durchschnittliche Bewertung, falls Bewertungen vorhanden sind
    average_rating = round(sum(rating.rating for rating in ratings) / total_ratings, 1) if total_ratings > 0 else 0

    # Überprüfen, ob Öffnungszeiten vorhanden sind, um Fehler in der Vorlage zu vermeiden
    opening_hours = client.opening_hours if hasattr(client, 'opening_hours') else []

    categories = client.categories if hasattr(client, 'categories') else []

    user = current_user if current_user.is_authenticated else None

    banner = Banner.query.filter_by(client_id=client.id).first()
    
    # Berechne die Anzahl der Kommentare
    total_reviews = sum(1 for rating in ratings if rating.comment)

    current_time = datetime.now()

    return render_template(
        'frontend/client_detail.html',
        client=client,
        ratings=ratings,
        opening_hours=opening_hours,
        user=user,
        banner=banner,
        categories=categories,
        current_time=current_time,
        total_ratings=total_ratings,  # Hinzufügen von total_ratings
        average_rating=average_rating,  # Hinzufügen von average_rating
        total_reviews=total_reviews  # Hinzufügen von total_reviews
    )

