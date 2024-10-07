import os
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from app import db
from app.models.client_model import Client
from app.models.galerie import Galerie  # Angenommen, dass es ein Galerie-Modell gibt

# Blueprint für Galerie definieren
client_galerie_bp = Blueprint('client_galerie_bp', __name__)

# Hauptverzeichnis für Client-Galerien
GALERIE_UPLOAD_FOLDER = 'app/static/upload/client_galerie'

# Überprüft, ob die Datei eine gültige Bilddatei ist
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Generiert einen eindeutigen Dateinamen für das hochgeladene Bild
def generate_unique_filename(filename):
    ext = filename.rsplit('.', 1)[1].lower()  # Dateiendung extrahieren
    unique_filename = f"{uuid.uuid4().hex}.{ext}"  # UUID als neuer Dateiname
    return unique_filename

# Route zum Anzeigen der Galerie des aktuellen Clients
@client_galerie_bp.route('/galerie')
def view_galerie():
    client_id = session.get('client_id')
    if not client_id:
        flash('Bitte als Client einloggen.', 'danger')
        return redirect(url_for('client_bp.login'))

    client = Client.query.get(client_id)
    if not client:
        flash('Client nicht gefunden oder Zugriff verweigert.', 'danger')
        return redirect(url_for('client_bp.login'))

    galerie = Galerie.query.filter_by(client_id=client.id).all()
    return render_template('galerie_list.html', galerie=galerie, client=client)

# Route zum Hinzufügen neuer Bilder zur Galerie
@client_galerie_bp.route('/galerie/add', methods=['GET', 'POST'])
def add_galerie_image():
    client_id = session.get('client_id')
    if not client_id:
        flash('Bitte als Client einloggen.', 'danger')
        return redirect(url_for('client_bp.login'))

    client = Client.query.get(client_id)
    if not client:
        flash('Client nicht gefunden oder Zugriff verweigert.', 'danger')
        return redirect(url_for('client_bp.login'))

    if request.method == 'POST':
        file = request.files.get('image')
        if not file or file.filename == '':
            flash('Kein Bild ausgewählt.', 'danger')
            return redirect(request.url)

        if allowed_file(file.filename):
            filename = generate_unique_filename(file.filename)

            # Erstelle das Verzeichnis für die Galerie des Clients, falls es noch nicht existiert
            client_galerie_folder = os.path.join(GALERIE_UPLOAD_FOLDER, f"client_{client_id}")
            if not os.path.exists(client_galerie_folder):
                os.makedirs(client_galerie_folder)

            filepath = os.path.join(client_galerie_folder, filename)
            file.save(filepath)

            # Speichere das Bild in der Galerie-Datenbank
            new_galerie_image = Galerie(image=os.path.relpath(filepath, 'app/static'), client_id=client.id)
            db.session.add(new_galerie_image)
            db.session.commit()
            flash('Bild erfolgreich zur Galerie hinzugefügt.', 'success')
            return redirect(url_for('client_galerie_bp.view_galerie'))

    return render_template('add_galerie.html', client=client)

# Route zum Löschen eines Bildes aus der Galerie
@client_galerie_bp.route('/galerie/delete/<int:id>', methods=['POST'])
def delete_galerie_image(id):
    client_id = session.get('client_id')
    if not client_id:
        flash('Bitte als Client einloggen.', 'danger')
        return redirect(url_for('client_bp.login'))

    image = Galerie.query.get_or_404(id)
    if image.client_id != client_id:
        flash('Zugriff verweigert.', 'danger')
        return redirect(url_for('client_galerie_bp.view_galerie'))

    # Lösche das Bild aus dem Dateisystem
    if os.path.exists(f'app/static/{image.image}'):
        os.remove(f'app/static/{image.image}')

    db.session.delete(image)
    db.session.commit()
    flash('Bild erfolgreich aus der Galerie gelöscht.', 'success')
    return redirect(url_for('client_galerie_bp.view_galerie'))

