# app/routes/user_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_mail import Message
from flask_login import login_user, logout_user, login_required, current_user
from itsdangerous import URLSafeTimedSerializer
from werkzeug.utils import secure_filename
import time
import os
from app.models.user_model import User
from app import db, mail

# Definiere die erlaubten Dateiendungen
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Definiere die Funktion allowed_file
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Definiere den Blueprint
user_bp = Blueprint('user_bp', __name__, template_folder='../templates/backend/user_templates')

# Login Route für User
@user_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('user_bp.dashboard'))

    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            if user.status != 'active':
                flash('Dein Account ist momentan deaktiviert. Bitte kontaktiere den Support.', 'danger')
                return render_template("user_login.html")

            login_user(user)  # Benutzer anmelden
            flash(f"Willkommen zurück, {user.username}!", "success")
            return redirect(url_for('user_bp.dashboard'))
        else:
            flash('Ungültige E-Mail oder Passwort. Bitte versuche es erneut.', 'danger')
            return render_template("user_login.html")

    return render_template("user_login.html")


# Register Route für User
@user_bp.route('/register', methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('user_bp.dashboard'))

    if request.method == "POST":
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        password_confirmation = request.form['password_confirmation']

        if password != password_confirmation:
            flash('Passwort und Passwortbestätigung stimmen nicht überein. Bitte erneut versuchen.', 'danger')
            return redirect(url_for('user_bp.register'))

        user = User.query.filter((User.username == username) | (User.email == email)).first()

        if user:
            flash('Benutzername oder E-Mail bereits vergeben. Bitte wähle einen anderen Benutzernamen oder eine andere E-Mail-Adresse.', 'danger')
            return redirect(url_for('user_bp.register'))
        else:
            new_user = User(username=username, email=email)
            new_user.set_password(password)  # Verschlüsseltes Passwort setzen
            db.session.add(new_user)
            db.session.commit()
            
            login_user(new_user)  # Benutzer nach Registrierung automatisch anmelden
            flash(f"Registrierung erfolgreich! Willkommen, {username}!", 'success')
            return redirect(url_for('user_bp.dashboard'))

    return render_template("user_register.html")


# Passwort zurücksetzen Anfrage
@user_bp.route('/password_reset_request', methods=["GET", "POST"])
def password_reset_request():
    if request.method == "POST":
        email = request.form['email']
        user = User.query.filter_by(email=email).first()

        if user:
            s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
            token = s.dumps(user.email, salt='password-reset-salt')
            reset_url = url_for('user_bp.password_reset_token', token=token, _external=True)

            msg = Message('Password Reset Request',
                          sender='expressmahlzeit@gmail.com',
                          recipients=[user.email])
            msg.body = f"Bitte klicke auf den folgenden Link, um dein Passwort zurückzusetzen: {reset_url}"
            mail.send(msg)

            flash('Eine E-Mail zum Zurücksetzen des Passworts wurde gesendet. Bitte überprüfe dein Postfach.', 'success')
            return redirect(url_for('user_bp.password_reset_request'))
        else:
            flash('Diese E-Mail ist nicht registriert. Bitte versuche es erneut.', 'danger')
            return redirect(url_for('user_bp.password_reset_request'))

    return render_template("user_password_reset_request.html")


# Passwort zurücksetzen
@user_bp.route('/password_reset/<token>', methods=["GET", "POST"])
def password_reset_token(token):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=3600)
    except:
        flash('Der Token ist ungültig oder abgelaufen.', 'danger')
        return redirect(url_for('user_bp.password_reset_request'))

    if request.method == "POST":
        password = request.form['password']
        password_confirmation = request.form['password_confirmation']

        if password != password_confirmation:
            flash('Passwort und Passwortbestätigung stimmen nicht überein. Bitte erneut versuchen.', 'danger')
            return redirect(url_for('user_bp.password_reset_token', token=token))

        user = User.query.filter_by(email=email).first()

        if user:
            user.set_password(password)
            db.session.commit()
            flash('Dein Passwort wurde erfolgreich geändert.', 'success')
            return redirect(url_for('user_bp.login'))
        else:
            flash('Benutzer nicht gefunden.', 'danger')
            return redirect(url_for('user_bp.password_reset_request'))

    return render_template('backend/user_templates/user_password_reset_form.html', token=token)


# Dashboard
@user_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("backend/user_templates/dashboard/dashboard.html", user=current_user, page_name="Dashboard")


# Profil bearbeiten
@user_bp.route("/profile_edit", methods=["GET", "POST"])
@login_required
def profile_edit():
    if request.method == "POST":
        current_user.username = request.form.get('username')
        current_user.email = request.form.get('email')
        current_user.phone_number = request.form.get('phone_number')
        current_user.street = request.form.get('street')
        current_user.house_number = request.form.get('house_number')
        current_user.postal_code = request.form.get('postal_code')
        current_user.city = request.form.get('city')

        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_ext = filename.rsplit('.', 1)[1].lower()
                new_filename = f"{int(time.time())}.{file_ext}"
                upload_folder = os.path.join(current_app.root_path, 'static', 'upload', 'user_bilder', 'user_profile')
                os.makedirs(upload_folder, exist_ok=True)

                file_path = os.path.join(upload_folder, new_filename)
                file.save(file_path)

                current_user.photo = os.path.join('upload', 'user_bilder', 'user_profile', new_filename).replace('\\', '/')

        db.session.commit()
        flash('Profil erfolgreich aktualisiert!', 'success')

    return render_template("backend/user_templates/dashboard/dashboard.html", user=current_user)


# Logout Route für User
@user_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Du hast dich erfolgreich ausgeloggt.", "success")
    return redirect(url_for('user_bp.login'))
