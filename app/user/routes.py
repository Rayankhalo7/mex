from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user
from .models import User, db
from werkzeug.security import check_password_hash

user_bp = Blueprint('user_bp', __name__, url_prefix='/user')

@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('user_bp.dashboard'))
        else:
            flash('Ungültige Anmeldeinformationen')

    return render_template('user/login.html')

@user_bp.route('/dashboard')
def dashboard():
    return "User Dashboard"
