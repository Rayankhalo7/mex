from flask import Blueprint, render_template, request, redirect, session, url_for, flash, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Message
from app.models.client_model import Client
from app import db, mail
from itsdangerous import URLSafeTimedSerializer
from werkzeug.utils import secure_filename
import time
import os




# Definiere den Blueprint
client_bp = Blueprint('client_bp', __name__, template_folder='../templates/backend/client_templates')

# Definiere die erlaubten Dateitypen
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Hilfsfunktion zum Löschen des alten Bildes
def delete_old_image(old_photo_path):
    full_path = os.path.join('static/uploads/client_bilder/client_trash', old_photo_path)
    if os.path.exists(full_path):
        os.remove(full_path)


# Login Route für client
@client_bp.route("/login", methods=["GET", "POST"])
def login():
    if "clientname" in session:
        return redirect(url_for('client_bp.dashboard'))

    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        
        client = Client.query.filter_by(email=email).first()  
        if client and client.check_password(password):
            session['client_id'] = client.id
            session['clientname'] = client.clientname
            return redirect(url_for('client_bp.dashboard'))
        else:
            return render_template("client_login.html", error="Ungültige E-Mail oder Passwort")

    return render_template("client_login.html")


# Register Route für client
@client_bp.route('/register', methods=["GET", "POST"])
def register():
    if "clientname" in session:
        return redirect(url_for('client_bp.dashboard'))

    if request.method == "POST":
        clientname = request.form['clientname']
        email = request.form['email']
        password = request.form['password']
        
        client = Client.query.filter((Client.clientname == clientname) | (Client.email == email)).first()  

        if client:
            return render_template("client_register.html", error="Benutzername oder E-Mail bereits vergeben")
        else:
            new_client = Client(clientname=clientname, email=email) 
            new_client.set_password(password)
            db.session.add(new_client)
            db.session.commit()
            session['clientname'] = clientname
            return redirect(url_for('client_bp.dashboard'))

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



# client Dashboard
@client_bp.route("/dashboard")
def dashboard():
    if "clientname" not in session:
        return redirect(url_for('client_bp.login'))
    
    # Lade das Client-Objekt
    client = Client.query.filter_by(clientname=session['clientname']).first()
    return render_template("client_dashboard.html", client=client, page_name="Dashboard")




# Profil-Seite anzeigen
@client_bp.route("/profile", methods=["GET"])
def profile():
    if "client_id" not in session:
        return redirect(url_for('client_bp.login'))
    
    client = Client.query.get(session['client_id'])
    
    return render_template("client_profile.html", client=client, page_name="Profil")





# Route zum Aktualisieren des Profils
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
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_ext = filename.rsplit('.', 1)[1].lower()
            new_filename = f"{int(time.time())}.{file_ext}"  # Einzigartiger Dateiname basierend auf Zeitstempel
            upload_folder = os.path.join('static', 'uploads', 'client_bilder', 'client_profile')

            # Prüfe, ob das Verzeichnis existiert, wenn nicht, erstelle es
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            # Speichere die Datei
            file_path = os.path.join(upload_folder, new_filename)
            file.save(file_path)

            # Speichere den relativen Pfad in der Datenbank
            client.photo = os.path.join('uploads', 'client_bilder', 'client_profile', new_filename).replace('\\', '/')

            # Debug-Ausgabe
            print(f"Datei gespeichert: {file_path}")

    # Speichere die Änderungen in der Datenbank
    db.session.commit()

    flash('Profil erfolgreich aktualisiert!')
    return redirect(url_for('client_bp.profile'))










# Logout Route für client
@client_bp.route("/logout")
def logout():
    session.pop('clientname', None)
    return redirect(url_for('client_bp.login'))
