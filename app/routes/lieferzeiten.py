from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from app import db
from app.models.lieferzeiten import Lieferzeiten
from app.models.client_model import Client

client_lieferzeiten_bp = Blueprint('client_lieferzeiten_bp', __name__)

# Route zum Anzeigen aller Lieferzeiten
@client_lieferzeiten_bp.route('/lieferzeiten', methods=['GET'])
def view_lieferzeiten():
    if 'client_id' not in session:
        flash("Bitte loggen Sie sich ein", "danger")
        return redirect(url_for('client_bp.login'))

    client = Client.query.get(session['client_id'])
    lieferzeiten = Lieferzeiten.query.filter_by(client_id=client.id).all()
    return render_template('lieferzeiten_list.html', lieferzeiten=lieferzeiten, client=client)

# Route zum Hinzufügen neuer Lieferzeiten
@client_lieferzeiten_bp.route('/lieferzeiten/add', methods=['GET', 'POST'])
def add_lieferzeiten():
    if 'client_id' not in session:
        flash("Bitte loggen Sie sich ein", "danger")
        return redirect(url_for('client_bp.login'))
    
    client = Client.query.get(session['client_id'])
    if request.method == 'POST':
        zeit_von = request.form.get('zeit_von')
        zeit_bis = request.form.get('zeit_bis')

        if zeit_von and zeit_bis:
            new_hours = Lieferzeiten(
                zeit_von=zeit_von,
                zeit_bis=zeit_bis,
                client_id=client.id
            )
            db.session.add(new_hours)
            db.session.commit()
            flash('Lieferzeiten erfolgreich hinzugefügt', 'success')
            return redirect(url_for('client_lieferzeiten_bp.view_lieferzeiten'))
        
        flash('Bitte füllen Sie beide Felder aus.', 'danger')

    return render_template('add_lieferzeiten.html', client=client)

# Route zum Bearbeiten von Lieferzeiten
@client_lieferzeiten_bp.route('/lieferzeiten/edit/<int:id>', methods=['GET', 'POST'])
def edit_lieferzeiten(id):
    if 'client_id' not in session:
        flash("Bitte loggen Sie sich ein", "danger")
        return redirect(url_for('client_bp.login'))

    client = Client.query.get(session['client_id'])
    lieferzeiten = Lieferzeiten.query.filter_by(id=id, client_id=client.id).first()
    if not lieferzeiten:
        flash('Lieferzeiten nicht gefunden oder Zugriff verweigert.', 'danger')
        return redirect(url_for('client_lieferzeiten_bp.view_lieferzeiten'))

    if request.method == 'POST':
        lieferzeiten.zeit_von = request.form.get('zeit_von')
        lieferzeiten.zeit_bis = request.form.get('zeit_bis')
        db.session.commit()
        flash('Lieferzeiten erfolgreich aktualisiert.', 'success')
        return redirect(url_for('client_lieferzeiten_bp.view_lieferzeiten'))

    return render_template('edit_lieferzeiten.html', lieferzeiten=lieferzeiten, client=client)

# Route zum Löschen von Lieferzeiten
@client_lieferzeiten_bp.route('/lieferzeiten/delete/<int:id>', methods=['POST'])
def delete_lieferzeiten(id):
    if 'client_id' not in session:
        flash("Bitte loggen Sie sich ein.", "danger")
        return redirect(url_for('client_bp.login'))
    
    client = Client.query.get(session['client_id'])
    lieferzeiten = Lieferzeiten.query.filter_by(id=id, client_id=client.id).first()
    if lieferzeiten:
        db.session.delete(lieferzeiten)
        db.session.commit()
        flash('Lieferzeiten erfolgreich gelöscht.', 'success')
    else:
        flash('Lieferzeiten nicht gefunden oder Zugriff verweigert.', 'danger')
    return redirect(url_for('client_lieferzeiten_bp.view_lieferzeiten'))
