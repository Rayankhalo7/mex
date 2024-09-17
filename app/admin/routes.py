from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user
from .models import Admin, db
from werkzeug.security import check_password_hash

admin_bp = Blueprint('admin_bp', __name__, url_prefix='/admin')

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        admin = Admin.query.filter_by(email=email).first()
        if admin and check_password_hash(admin.password, password):
            login_user(admin)
            return redirect(url_for('admin_bp.dashboard'))
        else:
            flash('Ungültige Anmeldeinformationen')

    return render_template('admin/login.html')

@admin_bp.route('/dashboard')
def dashboard():
    return "Admin Dashboard"
