# app/routes/opening_hours.py
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from app import db
from app.models.client_model import Client, OpeningHours

# Blueprint für Öffnungszeiten definieren
client_opening_hours_bp = Blueprint('client_opening_hours_bp', __name__)

# Route zum Anzeigen der Öffnungszeiten
@client_opening_hours_bp.route('/opening_hours')
def view_opening_hours():
    if 'client_id' not in session:
        flash("Bitte loggen Sie sich ein.", "danger")
        return redirect(url_for('client_bp.login'))

    client = Client.query.get(session['client_id'])
    opening_hours = OpeningHours.query.filter_by(client_id=client.id).all()
    return render_template('opening_hours_list.html', opening_hours=opening_hours, client=client)

# Route zum Hinzufügen neuer Öffnungszeiten
@client_opening_hours_bp.route('/opening_hours/add', methods=['GET', 'POST'])
def add_opening_hours():
    if 'client_id' not in session:
        flash("Bitte loggen Sie sich ein.", "danger")
        return redirect(url_for('client_bp.login'))

    client = Client.query.get(session['client_id'])
    if request.method == 'POST':
        day_of_week = request.form.get('day_of_week')
        open_time = request.form.get('open_time')
        close_time = request.form.get('close_time')
        
        # Neue Öffnungszeit hinzufügen
        if day_of_week and open_time and close_time:
            new_hours = OpeningHours(
                day_of_week=day_of_week,
                open_time=open_time,
                close_time=close_time,
                client_id=client.id
            )
            db.session.add(new_hours)
            db.session.commit()
            flash('Öffnungszeiten erfolgreich hinzugefügt.', 'success')
            return redirect(url_for('client_opening_hours_bp.view_opening_hours'))

    return render_template('add_opening_hours.html', client=client)

# Route zum Bearbeiten bestehender Öffnungszeiten
@client_opening_hours_bp.route('/opening_hours/edit/<int:id>', methods=['GET', 'POST'])
def edit_opening_hours(id):
    if 'client_id' not in session:
        flash("Bitte loggen Sie sich ein.", "danger")
        return redirect(url_for('client_bp.login'))

    client = Client.query.get(session['client_id'])
    opening_hours = OpeningHours.query.filter_by(id=id, client_id=client.id).first()
    if not opening_hours:
        flash('Öffnungszeiten nicht gefunden oder Zugriff verweigert.', 'danger')
        return redirect(url_for('client_opening_hours_bp.view_opening_hours'))

    if request.method == 'POST':
        opening_hours.day_of_week = request.form.get('day_of_week')
        opening_hours.open_time = request.form.get('open_time')
        opening_hours.close_time = request.form.get('close_time')
        db.session.commit()
        flash('Öffnungszeiten erfolgreich aktualisiert.', 'success')
        return redirect(url_for('client_opening_hours_bp.view_opening_hours'))

    return render_template('edit_opening_hours.html', opening_hours=opening_hours, client=client)

# Route zum Löschen bestehender Öffnungszeiten
@client_opening_hours_bp.route('/opening_hours/delete/<int:id>', methods=['POST'])
def delete_opening_hours(id):
    if 'client_id' not in session:
        flash("Bitte loggen Sie sich ein.", "danger")
        return redirect(url_for('client_bp.login'))

    client = Client.query.get(session['client_id'])
    opening_hours = OpeningHours.query.filter_by(id=id, client_id=client.id).first()
    if opening_hours:
        db.session.delete(opening_hours)
        db.session.commit()
        flash('Öffnungszeiten erfolgreich gelöscht.', 'success')
    else:
        flash('Öffnungszeiten nicht gefunden oder Zugriff verweigert.', 'danger')
    return redirect(url_for('client_opening_hours_bp.view_opening_hours'))
