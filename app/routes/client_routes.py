from flask import Blueprint, render_template, request, redirect, session, url_for, flash, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Message
from app.models.client_model import Client
from app import db, mail
from itsdangerous import URLSafeTimedSerializer
from werkzeug.utils import secure_filename
import time
import os
from app import serializer
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask import flash




# Definiere den Blueprint
client_bp = Blueprint('client_bp', __name__, template_folder='../templates/backend/client_templates')

# Definiere die erlaubten Dateitypen
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Hilfsfunktion zum Löschen des alten Bildes
def delete_old_image(old_photo_path):
    full_path = os.path.join(current_app.root_path, 'static', 'upload', 'client_bilder', 'client_profile', old_photo_path)
    if os.path.exists(full_path):
        os.remove(full_path)
        print(f"Altes Bild gelöscht: {full_path}")  # Debugging-Information
    else:
        print(f"Bild nicht gefunden: {full_path}")  # Debugging-Information


# Login Route für client
@client_bp.route("/login", methods=["GET", "POST"])
def login():
    if "clientname" in session:
        return redirect(url_for('client_bp.dashboard'))

    errors = {}

    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        
        client = Client.query.filter_by(email=email).first()

        # Fehler bei der Email-Adresse
        if not client:
            errors['email'] = 'Ungültige E-Mail-Adresse.'

        # Fehler beim Passwort
        if client and not client.check_password(password):
            errors['password'] = 'Ungültiges Passwort.'

        # Wenn keine Fehler vorhanden sind, logge den Benutzer ein
        if not errors:
            session['client_id'] = client.id
            session['clientname'] = client.clientname
            return redirect(url_for('client_bp.dashboard'))

    return render_template("client_login.html", errors=errors)


# Register Route für Clients
@client_bp.route('/register', methods=["GET", "POST"])
def register():
    # Überprüfe, ob der Client bereits eingeloggt ist
    if "clientname" in session:
        return redirect(url_for('client_bp.dashboard'))
    
    if request.method == "POST":
        # Erhalte die Formulardaten
        clientname = request.form['clientname']
        email = request.form['email']
        password = request.form['password']
    
        # Überprüfe, ob der Benutzername oder die E-Mail bereits existieren
        client = Client.query.filter((Client.clientname == clientname) | (Client.email == email)).first()
        
        if client:
            # Benutzername oder E-Mail bereits vorhanden
            flash("Benutzername oder E-Mail bereits vergeben", "danger")  # Fehler-Meldung mit Kategorie "danger"
            return redirect(url_for('client_bp.register'))
        else:
            # Neuen Client erstellen
            new_client = Client(clientname=clientname, email=email)
            new_client.set_password(password)  # Passwort-Hash generieren und speichern
            db.session.add(new_client)
            db.session.commit()
            
            # Setze die Session-Variablen
            session['clientname'] = clientname
            session['client_id'] = new_client.id
            
            flash("Registrierung erfolgreich! Sie wurden eingeloggt.", "success")  # Erfolgreiche Registrierung
            return redirect(url_for('client_bp.dashboard'))

    # Renders the registration template
    return render_template("client_register.html")



# Passwort zurücksetzen Anfrage
@client_bp.route('/password_reset_request', methods=["GET", "POST"])
def password_reset_request():
    if request.method == "POST":
        email = request.form['email']
        client = Client.query.filter_by(email=email).first() 

        if client:
            s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
            token = s.dumps(client.email, salt='password-reset-salt')
            reset_url = url_for('client_bp.password_reset_token', token=token, _external=True)

            msg = Message('Password Reset Request',
                          sender='expressmahlzeit@gmail.com',
                          recipients=[client.email])
            msg.body = f"Bitte klicke auf den folgenden Link, um dein Passwort zurückzusetzen: {reset_url}"
            mail.send(msg)

            flash('Eine E-Mail zum Zurücksetzen des Passworts wurde gesendet.')
            return redirect(url_for('client_bp.password_reset_request'))

    return render_template("client_password_reset_request.html")

# Passwort zurücksetzen
@client_bp.route('/password_reset/<token>', methods=["GET", "POST"])
def password_reset_token(token):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=3600)
    except:
        flash('Der Token ist ungültig oder abgelaufen.')
        return redirect(url_for('client_bp.password_reset_request'))

    if request.method == "POST":
        password = request.form['password']
        client = Client.query.filter_by(email=email).first()  # Hier Client statt client verwenden

        if client:
            client.set_password(password)
            db.session.commit()
            flash('Dein Passwort wurde erfolgreich geändert.')
            return redirect(url_for('client_bp.password_reset_request'))
        else:
            flash('Benutzer nicht gefunden.')
            return redirect(url_for('client_bp.password_reset_request'))

    return render_template('backend/client_templates/client_password_reset_form.html', token=token)

@client_bp.route('/password_set_admin/<token>', methods=['GET', 'POST'])
def client_password_set_admin(token):
    """Verarbeitet das Setzen des Passworts durch den Admin-Link."""
    try:
        # Überprüfe den Token und hole die Client-ID heraus
        client_id = serializer.loads(token, salt='password-set', max_age=3600)  # 1 Stunde gültig
    except SignatureExpired:
        flash('Der Link ist abgelaufen. Bitte fordere eine neue E-Mail an.', 'danger')
        return redirect(url_for('client_bp.login'))
    except BadSignature:
        flash('Ungültiger Link. Bitte fordere eine neue E-Mail an.', 'danger')
        return redirect(url_for('client_bp.login'))

    # Suche den Client anhand der ID in der Datenbank
    client = Client.query.get(client_id)
    if not client:
        flash('Ungültiger Client.', 'danger')
        return redirect(url_for('client_bp.login'))

    if request.method == 'POST':
        # Lese die E-Mail und das Passwort aus dem Formular
        entered_email = request.form['email']
        password = request.form['password']

        # Überprüfe, ob die eingegebene E-Mail-Adresse mit der vom Admin festgelegten E-Mail übereinstimmt
        if entered_email != client.email:
            flash('Die eingegebene E-Mail-Adresse stimmt nicht mit der vom Admin festgelegten E-Mail überein.', 'danger')
            return render_template('client_password_set_admin.html', client=client, token=token)

        # Überprüfe, ob die E-Mail in der Datenbank existiert
        email_exists = Client.query.filter_by(email=entered_email).first()
        if not email_exists:
            flash('Die eingegebene E-Mail-Adresse existiert nicht in der Datenbank. Bitte überprüfen Sie die E-Mail-Adresse.', 'danger')
            return render_template('client_password_set_admin.html', client=client, token=token)

        # Setze das neue Passwort
        client.set_password(password)

        # Speichere das neue Passwort in der Datenbank
        db.session.commit()
        flash('Passwort erfolgreich gesetzt. Sie können sich jetzt einloggen.', 'success')
        return redirect(url_for('client_bp.login'))

    return render_template('client_password_set_admin.html', client=client, token=token)





# client Dashboard
@client_bp.route("/dashboard")
def dashboard():
    if "clientname" not in session:
        return redirect(url_for('client_bp.login'))
    
    # Lade das Client-Objekt
    client = Client.query.get(session['client_id'])
    return render_template("client_dashboard.html", client=client, page_name="Dashboard")




# Profil-Seite anzeigen
@client_bp.route("/profile", methods=["GET", "POST"])
def profile():
    if "client_id" not in session:
        return redirect(url_for('client_bp.login'))
    
    client = Client.query.get(session['client_id'])
    
    return render_template("client_profile.html", client=client, page_name="Profil")





@client_bp.route("/profile_update", methods=["POST"])
def profile_update():
    if "client_id" not in session:
        return redirect(url_for('client_bp.login'))

    client = Client.query.get(session['client_id'])

    # Aktualisiere die Felder mit den Formulardaten
    client.clientname = request.form.get('clientname')
    client.email = request.form.get('email')
    client.phone_number = request.form.get('phone_number')
    client.street = request.form.get('street')
    client.house_number = request.form.get('house_number')
    client.postal_code = request.form.get('postal_code')
    client.city = request.form.get('city')

    # Überprüfe, ob ein neues Bild hochgeladen wurde
    if 'photo' in request.files:
        file = request.files['photo']
        if file and file.filename != '' and allowed_file(file.filename):
            print(f"Dateiname: {file.filename}")  # Debugging-Information
            filename = secure_filename(file.filename)
            file_ext = filename.rsplit('.', 1)[1].lower()
            new_filename = f"{int(time.time())}.{file_ext}"  # Einzigartiger Dateiname basierend auf Zeitstempel

            # Verwende den richtigen Pfad relativ zum app-Ordner
            upload_folder = os.path.join(current_app.root_path, 'static', 'upload', 'client_bilder', 'client_profile')

            # Prüfe, ob das Verzeichnis existiert, wenn nicht, erstelle es
            os.makedirs(upload_folder, exist_ok=True)

            # Speichere die Datei
            file_path = os.path.join(upload_folder, new_filename)
            print(f"Speicherpfad: {file_path}")  # Debugging-Information
            file.save(file_path)

            # Speichere den relativen Pfad in der Datenbank
            client.photo = os.path.join('upload', 'client_bilder', 'client_profile', new_filename).replace('\\', '/')
            print(f"Relativer Pfad in der DB: {client.photo}")  # Debugging-Information

            # Debug-Ausgabe
            print(f"Datei gespeichert: {file_path}")
        else:
            print("Keine gültige Datei hochgeladen oder Dateityp nicht erlaubt")  # Debugging-Information

    # Speichere die Änderungen in der Datenbank
    db.session.commit()

    

    flash('Profil erfolgreich aktualisiert!', 'success')
    return redirect(url_for('client_bp.profile'))




# Client Password ändern im Profil
@client_bp.route("/change_password", methods=["GET", "POST"])
def change_password():
    if "client_id" not in session:
        return redirect(url_for('client_bp.login'))

    client = Client.query.get(session['client_id'])
    errors = {}

    if request.method == 'POST':
        # Hol die eingegebenen Werte aus dem Formular
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # Überprüfung des aktuellen Passworts
        if not client.check_password(current_password):
            errors['current_password'] = 'Das aktuelle Passwort ist falsch.'

        # Überprüfung, ob das neue Passwort mit der Bestätigung übereinstimmt
        if new_password != confirm_password:
            errors['confirm_password'] = 'Die neuen Passwörter stimmen nicht überein.'

        # Wenn keine Fehler vorhanden sind, aktualisiere das Passwort
        if not errors:
            client.set_password(new_password)
            db.session.commit()

            flash('Passwort erfolgreich aktualisiert!', 'success')
            return redirect(url_for('client_bp.change_password'))

    return render_template('client_change_password.html', client=client, errors=errors, page_name="Passwort ändern")










@client_bp.route("/logout")
def logout():
    session.pop('clientname', None)
    session.pop('client_id', None)
    
    return redirect(url_for('client_bp.login'))

