# app/routes/rating.py
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_required, current_user
from app import db
from app.models.rating import Rating
from app.models.client_model import Client

# Blueprint definieren
rating_bp = Blueprint('rating_bp', __name__)

# Route zum Anzeigen der Bewertungen im Client-Dashboard
@rating_bp.route('/client/dashboard/ratings', methods=['GET'])
def client_dashboard_ratings():
    client_id = session.get('client_id')
    if not client_id:
        flash('Bitte melden Sie sich an, um Bewertungen zu sehen.', 'danger')
        return redirect(url_for('client_bp.login'))

    client = Client.query.get(client_id)
    if not client:
        flash('Client nicht gefunden.', 'danger')
        return redirect(url_for('client_bp.login'))

    ratings = Rating.query.filter_by(client_id=client_id).all()
    return render_template('client_dashboard_ratings.html', client=client, ratings=ratings)

# Route zum Hinzufügen einer neuen Bewertung
@rating_bp.route('/client/<int:client_id>/rate', methods=['POST'])
@login_required
def rate_client(client_id):
    client = Client.query.get_or_404(client_id)

    # Überprüfen, ob der Benutzer bereits eine Bewertung für diesen Client abgegeben hat
    existing_rating = Rating.query.filter_by(client_id=client_id, user_id=current_user.id).first()
    if existing_rating:
        flash('Sie haben diesen Ort bereits bewertet.', 'warning')
        return redirect(url_for('frontend_bp.client_detail', client_id=client_id))

    rating_value = request.form.get('rating')
    comment = request.form.get('comment')

    if not rating_value:
        flash('Bitte geben Sie eine Bewertung ab.', 'danger')
        return redirect(url_for('frontend_bp.client_detail', client_id=client_id))

    # Erstelle eine neue Bewertung
    new_rating = Rating(
        rating=int(rating_value),
        comment=comment,
        user_id=current_user.id,
        client_id=client.id
    )
    db.session.add(new_rating)
    db.session.commit()
    flash('Bewertung erfolgreich abgegeben.', 'success')
    return redirect(url_for('frontend_bp.client_detail', client_id=client_id))
