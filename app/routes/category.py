from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from app import db
from app.models.category import Category
from app.models.client_model import Client

# Blueprint definieren
client_category_bp = Blueprint('client_category_bp', __name__)

# Route zum Anzeigen der Kategorien
@client_category_bp.route('/categories')
def view_categories():
    # Überprüfe, ob der Benutzer eingeloggt ist
    if 'client_id' not in session:
        flash("Bitte loggen Sie sich ein.", "danger")
        return redirect(url_for('client_bp.login'))

    # Hole den aktuellen Client basierend auf der gespeicherten client_id in der Session
    client = Client.query.get(session['client_id'])
    if client is None:
        flash("Client nicht gefunden oder Zugriff verweigert. Bitte loggen Sie sich erneut ein.", "danger")
        return redirect(url_for('client_bp.login'))

    # Hole alle Kategorien für diesen Client
    categories = Category.query.filter_by(client_id=client.id).all()
    return render_template('category_list.html', categories=categories, client=client)

# Route zum Hinzufügen einer neuen Kategorie
@client_category_bp.route('/category/add', methods=['GET', 'POST'])
def add_category():
    # Überprüfe, ob der Benutzer eingeloggt ist
    if 'client_id' not in session:
        flash("Bitte loggen Sie sich ein.", "danger")
        return redirect(url_for('client_bp.login'))

    # Hole den aktuellen Client basierend auf der gespeicherten client_id in der Session
    client = Client.query.get(session['client_id'])
    if client is None:
        flash("Client nicht gefunden oder Zugriff verweigert. Bitte loggen Sie sich erneut ein.", "danger")
        return redirect(url_for('client_bp.login'))

    if request.method == 'POST':
        name = request.form.get('name')
        if name:
            # Erstelle eine neue Kategorie und ordne sie dem aktuellen Client zu
            new_category = Category(name=name, client_id=client.id)
            db.session.add(new_category)
            db.session.commit()
            flash('Kategorie erfolgreich hinzugefügt.', 'success')
            return redirect(url_for('client_category_bp.view_categories'))

    return render_template('add_category.html', client=client)

# Route zum Bearbeiten einer bestehenden Kategorie
@client_category_bp.route('/category/edit/<int:id>', methods=['GET', 'POST'])
def edit_category(id):
    # Überprüfe, ob der Benutzer eingeloggt ist
    if 'client_id' not in session:
        flash("Bitte loggen Sie sich ein.", "danger")
        return redirect(url_for('client_bp.login'))

    # Hole den aktuellen Client basierend auf der gespeicherten client_id in der Session
    client = Client.query.get(session['client_id'])
    if client is None:
        flash("Client nicht gefunden oder Zugriff verweigert. Bitte loggen Sie sich erneut ein.", "danger")
        return redirect(url_for('client_bp.login'))

    # Finde die Kategorie, die bearbeitet werden soll, und prüfe, ob sie zum aktuellen Client gehört
    category = Category.query.filter_by(id=id, client_id=client.id).first()
    if not category:
        flash('Kategorie nicht gefunden oder Zugriff verweigert.', 'danger')
        return redirect(url_for('client_category_bp.view_categories'))

    if request.method == 'POST':
        category.name = request.form.get('name')
        db.session.commit()
        flash('Kategorie erfolgreich aktualisiert.', 'success')
        return redirect(url_for('client_category_bp.view_categories'))

    return render_template('edit_category.html', category=category, client=client)

# Route zum Löschen einer bestehenden Kategorie
@client_category_bp.route('/category/delete/<int:id>', methods=['POST'])
def delete_category(id):
    # Überprüfe, ob der Benutzer eingeloggt ist
    if 'client_id' not in session:
        flash("Bitte loggen Sie sich ein.", "danger")
        return redirect(url_for('client_bp.login'))

    # Hole den aktuellen Client basierend auf der gespeicherten client_id in der Session
    client = Client.query.get(session['client_id'])
    if client is None:
        flash("Client nicht gefunden oder Zugriff verweigert. Bitte loggen Sie sich erneut ein.", "danger")
        return redirect(url_for('client_bp.login'))

    # Finde die Kategorie, die gelöscht werden soll, und prüfe, ob sie zum aktuellen Client gehört
    category = Category.query.filter_by(id=id, client_id=client.id).first()
    if category:
        db.session.delete(category)
        db.session.commit()
        flash('Kategorie erfolgreich gelöscht.', 'success')
    else:
        flash('Kategorie nicht gefunden oder Zugriff verweigert.', 'danger')

    return redirect(url_for('client_category_bp.view_categories'))
