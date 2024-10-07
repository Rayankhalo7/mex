import os
import uuid  # UUID für eindeutige Dateinamen und URLs
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from app import db
from app.models.banner import Banner
from app.models.client_model import Client

# Blueprint für Banner definieren
client_banner_bp = Blueprint('client_banner_bp', __name__)

# Verzeichnis für das Speichern der hochgeladenen Banner
BANNER_UPLOAD_FOLDER = 'app/static/upload/client_banner'

# Überprüft, ob die Datei eine gültige Bilddatei ist
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Generiert einen eindeutigen Dateinamen für das hochgeladene Bild
def generate_unique_filename(filename):
    ext = filename.rsplit('.', 1)[1].lower()  # Dateiendung extrahieren
    unique_filename = f"{uuid.uuid4().hex}.{ext}"  # UUID als neuer Dateiname
    return unique_filename

# Route zum Anzeigen aller Banner des aktuellen Clients
@client_banner_bp.route('/banner')
def view_banners():
    client_id = session.get('client_id')
    if not client_id:
        flash('Bitte als Client einloggen.', 'danger')
        return redirect(url_for('client_bp.login'))

    client = Client.query.get(client_id)
    if not client:
        flash('Client nicht gefunden oder Zugriff verweigert.', 'danger')
        return redirect(url_for('client_bp.login'))

    banners = Banner.query.filter_by(client_id=client.id).all()
    return render_template('banner_list.html', banners=banners, client=client)

# Route zum Hinzufügen eines neuen Banners
@client_banner_bp.route('/banner/add', methods=['GET', 'POST'])
def add_banner():
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
            # Generiere einen eindeutigen Dateinamen und speichere die Datei
            filename = generate_unique_filename(file.filename)
            if not os.path.exists(BANNER_UPLOAD_FOLDER):
                os.makedirs(BANNER_UPLOAD_FOLDER)

            filepath = os.path.join(BANNER_UPLOAD_FOLDER, filename)
            file.save(filepath)

            # Generiere eine eindeutige URL basierend auf UUID
            unique_url = f"/client/{client.id}/banner/{uuid.uuid4().hex}"

            # Speichere das Banner in der Datenbank mit der generierten URL
            new_banner = Banner(image=os.path.relpath(filepath, 'app/static'), url=unique_url, client_id=client.id)
            db.session.add(new_banner)
            db.session.commit()
            flash('Banner erfolgreich hinzugefügt.', 'success')
            return redirect(url_for('client_banner_bp.view_banners'))

    return render_template('add_banner.html', client=client)

# Route zum Löschen eines Banners
@client_banner_bp.route('/banner/delete/<int:id>', methods=['POST'])
def delete_banner(id):
    client_id = session.get('client_id')
    if not client_id:
        flash('Bitte als Client einloggen.', 'danger')
        return redirect(url_for('client_bp.login'))

    banner = Banner.query.get_or_404(id)
    if banner.client_id != client_id:
        flash('Zugriff verweigert.', 'danger')
        return redirect(url_for('client_banner_bp.view_banners'))

    # Lösche das Bild aus dem Dateisystem
    if os.path.exists(f'app/static/{banner.image}'):
        os.remove(f'app/static/{banner.image}')

    db.session.delete(banner)
    db.session.commit()
    flash('Banner erfolgreich gelöscht.', 'success')
    return redirect(url_for('client_banner_bp.view_banners'))

# Route zum Bearbeiten eines Banners
@client_banner_bp.route('/banner/edit/<int:id>', methods=['GET', 'POST'])
def edit_banner(id):
    client_id = session.get('client_id')
    if not client_id:
        flash('Bitte als Client einloggen.', 'danger')
        return redirect(url_for('client_bp.login'))

    banner = Banner.query.get_or_404(id)
    client = Client.query.get(client_id)
    if banner.client_id != client_id:
        flash('Zugriff verweigert.', 'danger')
        return redirect(url_for('client_banner_bp.view_banners'))

    if request.method == 'POST':
        file = request.files.get('image')
        if file and allowed_file(file.filename):
            # Lösche das alte Bild, falls vorhanden
            if os.path.exists(f'app/static/{banner.image}'):
                os.remove(f'app/static/{banner.image}')

            # Generiere neuen Dateinamen und speichere das neue Bild
            filename = generate_unique_filename(file.filename)
            filepath = os.path.join(BANNER_UPLOAD_FOLDER, filename)
            file.save(filepath)
            banner.image = os.path.relpath(filepath, 'app/static')

        # Bei einer Änderung wird die URL ebenfalls neu generiert
        banner.url = f"/client/{client_id}/banner/{uuid.uuid4().hex}"
        db.session.commit()
        flash('Banner erfolgreich aktualisiert.', 'success')
        return redirect(url_for('client_banner_bp.view_banners'))

    # `client` an das Template übergeben
    return render_template('edit_banner.html', banner=banner, client=client)

