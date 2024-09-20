#user_routes.py
from flask import Blueprint, render_template, request, redirect, session, url_for, flash, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Message
from app.models.user_model import User
from app import db, mail
from itsdangerous import URLSafeTimedSerializer

# Definiere den Blueprint
user_bp = Blueprint('user_bp', __name__, template_folder='../templates/backend/user_templates')

# Login Route für User
@user_bp.route("/login", methods=["GET", "POST"])
def login():
    if "username" in session:
        return redirect(url_for('user_bp.dashboard'))

    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['username'] = user.username
            return redirect(url_for('user_bp.dashboard'))
        else:
            return render_template("user_login.html", error="Ungültige E-Mail oder Passwort")

    return render_template("user_login.html")


# Register Route für User
@user_bp.route('/register', methods=["GET", "POST"])
def register():
    if "username" in session:
        return redirect(url_for('user_bp.dashboard'))

    if request.method == "POST":
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter((User.username == username) | (User.email == email)).first()

        if user:
            return render_template("user_register.html", error="Benutzername oder E-Mail bereits vergeben")
        else:
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username
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

            flash('Eine E-Mail zum Zurücksetzen des Passworts wurde gesendet.')
            return redirect(url_for('user_bp.password_reset_request'))
        else:
            # Wenn die E-Mail nicht gefunden wurde
            flash('Diese E-Mail ist nicht registriert.')
            return redirect(url_for('user_bp.password_reset_request'))

    return render_template("user_password_reset_request.html")

# Passwort zurücksetzen
@user_bp.route('/password_reset/<token>', methods=["GET", "POST"])
def password_reset_token(token):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=3600)
    except:
        flash('Der Token ist ungültig oder abgelaufen.')
        return redirect(url_for('user_bp.password_reset_request'))

    if request.method == "POST":
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user:
            user.set_password(password)
            db.session.commit()
            flash('Dein Passwort wurde erfolgreich geändert.')
            return redirect(url_for('user_bp.password_reset_request'))
        else:
            flash('Benutzer nicht gefunden.')
            return redirect(url_for('user_bp.password_reset_request'))

    return render_template('backend/user_templates/user_password_reset_form.html', token=token)



# User Dashboard
@user_bp.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for('user_bp.login'))
    return render_template("user_dashboard.html", username=session['username'])


# Logout Route für User
@user_bp.route("/logout")
def logout():
    session.pop('username', None)
    return redirect(url_for('user_bp.login'))
