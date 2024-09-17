from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user
from .models import Client, db
from werkzeug.security import check_password_hash

client_bp = Blueprint('client_bp', __name__, url_prefix='/client')

@client_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        client = Client.query.filter_by(email=email).first()
        if client and check_password_hash(client.password, password):
            login_user(client)
            return redirect(url_for('client_bp.dashboard'))
        else:
            flash('Ungültige Anmeldeinformationen')

    return render_template('client/login.html')

@client_bp.route('/dashboard')
def dashboard():
    return "Client Dashboard"
