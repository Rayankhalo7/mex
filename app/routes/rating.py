from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from app import db
from app.models.rating import Rating
from app.models.client_model import Client

# Blueprint definieren
rating_bp = Blueprint('rating_bp', __name__)

# Route zum Anzeigen der Bewertungen im Client-Dashboard
@rating_bp.route('/client/dashboard/ratings', methods=['GET'])
def client_dashboard_ratings():
    # Überprüfen, ob 'client_id' in der Session vorhanden ist
    client_id = session.get('client_id')
    if not client_id:
        flash('Bitte melden Sie sich an, um Bewertungen zu sehen.', 'danger')
        return redirect(url_for('client_bp.login'))

    # Hole den Client basierend auf der Client-ID aus der Session
    client = Client.query.get(client_id)
    if not client:
        flash('Client nicht gefunden.', 'danger')
        return redirect(url_for('client_bp.login'))

    # Alle Bewertungen für den aktuellen Client abrufen
    ratings = Rating.query.filter_by(client_id=client_id).all()
    return render_template('client_dashboard_ratings.html', client=client, ratings=ratings)
