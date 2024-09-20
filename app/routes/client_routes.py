from flask import Blueprint, render_template, request, redirect, session, url_for, flash, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Message
from app.models.client_model import Client
from app import db, mail
from itsdangerous import URLSafeTimedSerializer
from werkzeug.utils import secure_filename

# Definiere den Blueprint
client_bp = Blueprint('client_bp', __name__, template_folder='../templates/backend/client_templates')

# Upload-Ordner
PROFILE_UPLOAD_FOLDER = 'static/uploads/client_bilder/client_profile'
GALLERY_UPLOAD_FOLDER = 'static/uploads/client_bilder/client_galerie'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Hilfsfunktion zur Dateiendungsüberprüfung
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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



import os

# Profil-Seite 
@client_bp.route("/profile", methods=["GET", "POST"])
def profile():
    if "client_id" not in session:
        return redirect(url_for('client_bp.login'))
    
    client = Client.query.get(session['client_id'])

    if request.method == "POST":
        # Andere Logik, falls nötig (z.B. Profil-Daten aktualisieren)
        flash('Profil aktualisiert!')
        return redirect(url_for('client_bp.profile'))

    return render_template("client_profile.html", client=client, page_name="Profil")








# Logout Route für client
@client_bp.route("/logout")
def logout():
    session.pop('clientname', None)
    return redirect(url_for('client_bp.login'))
