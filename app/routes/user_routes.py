# app/routes/user_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
from flask_mail import Message
from flask_login import login_user, logout_user, login_required, current_user
from itsdangerous import URLSafeTimedSerializer
from werkzeug.utils import secure_filename
import time
import os
from app.models.user_model import User
from app import db, mail
from app.models.order import Order
from flask import request
from werkzeug.exceptions import NotFound
from app.models.order_item import OrderItem
from app.models.client_model import Client
from app.models.cities import City

# Definiere die erlaubten Dateiendungen
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Definiere die Funktion allowed_file
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Definiere den Blueprint
user_bp = Blueprint('user_bp', __name__, template_folder='../templates/backend/user_templates')



@user_bp.context_processor
def inject_current_path():
    return {
        'current_path': request.path,  # Der aktuelle Pfad, z.B. /user/dashboard
        'current_rule': str(request.url_rule),  # Die URL-Regel, z.B. /dashboard
        'current_blueprint': request.blueprint  # Der aktuelle Blueprint, z.B. user_bp
    }



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


from app.routes.frontend import calculate_total_cost_and_tax

# Dashboard
@user_bp.route("/dashboard")
@login_required
def dashboard():
    clients = Client.query.all()
    cities = City.query.all()

    # Falls keine Clients vorhanden sind, leere Seite anzeigen
    if not clients:
        return render_template('backend/user_templates/dashboard/dashboard.html', cities=cities)

    client = None
    # Überprüfen, ob eine Client-ID im Warenkorb gespeichert ist
    if 'cart_client_id' in session:
        # Den Client basierend auf der Client-ID im Warenkorb abrufen
        client = Client.query.filter_by(id=session['cart_client_id']).first()

    # Warenkorb aus der Session abrufen
    cart = session.get('cart', {})

    # Berechnung der Gesamtkosten, Steuern und Steuerdetails
    total_cost, total_tax, tax_details = calculate_total_cost_and_tax(cart)

    # Berechnung der Gesamtartikelanzahl
    total_items = sum(item['quantity'] for item in cart.values())

    return render_template(
        "backend/user_templates/dashboard/dashboard.html", 
        user=current_user,
        clients=clients,
        client=client,
        cart=cart,
        total_cost=total_cost,
        tax_details=tax_details,
        total_tax=total_tax,
        total_items=total_items,
        page_name="Dashboard"  # Korrektur: Komma hinzugefügt
    )





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



@user_bp.route("/passwort_aendern", methods=["GET", "POST"])
@login_required
def passwort_aendern():
    user = current_user  # Verwende den aktuell eingeloggenen Benutzer
    errors = {}  # Fehlerdictionary zum Speichern von Fehlern während der Überprüfung

    client = None
    # Überprüfen, ob eine Client-ID im Warenkorb gespeichert ist
    if 'cart_client_id' in session:
        # Den Client basierend auf der Client-ID im Warenkorb abrufen
        client = Client.query.filter_by(id=session['cart_client_id']).first()

    cart = session.get('cart', {})

    # Berechnung der Gesamtkosten, Steuern und Steuerdetails
    total_cost, total_tax, tax_details = calculate_total_cost_and_tax(cart)

    total_items = sum(item['quantity'] for item in cart.values())


    if request.method == 'POST':
        # Hole die eingegebenen Werte aus dem Formular
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # Debugging: Geben Sie die eingegebenen Werte aus, um zu sehen, ob das Formular korrekt übermittelt wird
        print(f"Aktuelles Passwort: {current_password}")
        print(f"Neues Passwort: {new_password}")
        print(f"Passwortbestätigung: {confirm_password}")

        # Überprüfung des aktuellen Passworts
        if not user.check_password(current_password):
            errors['current_password'] = 'Das aktuelle Passwort ist falsch.'
            flash('Das aktuelle Passwort ist falsch.', 'danger')
            print("Fehler: Das aktuelle Passwort ist falsch")

        # Überprüfung, ob das neue Passwort mit der Bestätigung übereinstimmt
        if new_password != confirm_password:
            errors['confirm_password'] = 'Die neuen Passwörter stimmen nicht überein.'
            flash('Die neuen Passwörter stimmen nicht überein.', 'danger')
            print("Fehler: Die neuen Passwörter stimmen nicht überein")

        # Überprüfen, ob das neue Passwort bestimmten Kriterien entspricht (optional)
        if len(new_password) < 6:
            errors['new_password'] = 'Das neue Passwort muss mindestens 6 Zeichen lang sein.'
            flash('Das neue Passwort muss mindestens 6 Zeichen lang sein.', 'danger')
            print("Fehler: Das neue Passwort ist zu kurz")

        # Wenn keine Fehler vorhanden sind, aktualisiere das Passwort
        if not errors:
            try:
                user.set_password(new_password)  # Neues verschlüsseltes Passwort setzen (MD5)
                db.session.commit()  # Speichern in der Datenbank
                flash('Passwort erfolgreich aktualisiert!', 'success')
                print("Passwort erfolgreich aktualisiert und gespeichert")
                return redirect(url_for('user_bp.passwort_aendern'))
            except Exception as e:
                # Fange alle möglichen Fehler beim Speichern ab
                print(f"Fehler beim Speichern des neuen Passworts: {e}")
                flash('Fehler beim Speichern des neuen Passworts. Bitte versuche es erneut.', 'danger')

    # Rendere die Seite mit eventuellen Fehlern, falls das Formular nicht korrekt ausgefüllt wurde
    return render_template('backend/user_templates/dashboard/passwort_aendern.html',total_items=total_items,cart=cart,total_cost=total_cost, total_tax=total_tax, tax_details=tax_details, user=user, errors=errors,client=client, page_name="Passwort ändern")


@user_bp.route("/meine_bestellungen", methods=["GET"])
@login_required
def meine_bestellungen():
    user = current_user  # Der aktuell eingeloggte Benutzer

    # Überprüfen, ob eine Client-ID im Warenkorb gespeichert ist
    client = None
    if 'cart_client_id' in session:
        # Den Client basierend auf der Client-ID im Warenkorb abrufen
        client = Client.query.filter_by(id=session['cart_client_id']).first()

    # Warenkorb aus der Session abrufen
    cart = session.get('cart', {})

    # Berechnung der Gesamtkosten, Steuern und Steuerdetails für den Warenkorb
    total_cost, total_tax, tax_details = calculate_total_cost_and_tax(cart)

    # Berechnung der Gesamtartikelanzahl im Warenkorb
    total_items = sum(item['quantity'] for item in cart.values())

    try:
        # Bestellungen des aktuellen Benutzers aus der Datenbank abrufen
        orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.order_date.desc()).all()
        
        # Template mit den Bestellungen und zusätzlichen Informationen (Warenkorb, Kosten, Steuern) rendern
        return render_template(
            'backend/user_templates/dashboard/meine_bestellungen.html',
            user=user,
            orders=orders,
            client=client,
            cart=cart,
            total_cost=total_cost,
            total_tax=total_tax,
            tax_details=tax_details,
            total_items=total_items,
            page_name="Meine Bestellungen"
        )
    except Exception as e:
        # Fehler abfangen und anzeigen, falls etwas schiefgeht
        flash(f'Fehler beim Abrufen der Bestellungen: {str(e)}', 'danger')
        print(f"Fehler beim Abrufen der Bestellungen: {e}")
        return render_template(
            'backend/user_templates/dashboard/meine_bestellungen.html',
            user=user,
            orders=[],  # Leere Bestellungen im Fehlerfall
            client=client,
            cart=cart,
            total_cost=total_cost,
            total_tax=total_tax,
            tax_details=tax_details,
            total_items=total_items,
            page_name="Meine Bestellungen"
        )




@user_bp.route("/meine_bestellung/<int:order_id>", methods=["GET"])
@login_required
def meine_bestellung(order_id):
    try:
        user = current_user
        
        # Debugging: Prüfe, ob der Benutzer korrekt geladen wird
        print(f"Benutzer ID: {user.id}")
        
        # Versuche, die Bestellung zu laden
        order = Order.query.filter_by(id=order_id, user_id=user.id).first_or_404()
        print(f"Bestellung gefunden: {order.id}")
        
        # Lade die Bestellpositionen
        order_items = OrderItem.query.filter_by(order_id=order.id).all()
        print(f"Anzahl der Bestellpositionen: {len(order_items)}")

        if not order_items:
            print("Keine Bestellpositionen gefunden")

        # Berechnung der Gesamtkosten, Steuern und Steuerdetails für den Warenkorb
        cart = session.get('cart', {})  # Warenkorb aus der Session holen
        total_cost, total_tax, tax_details = calculate_total_cost_and_tax(cart)

        # Berechnungen im Backend für die Bestellung
        total_netto = 0
        total_brutto = 0
        total_tax_order = 0

        for item in order_items:
            netto_price = item.price / (1 + (item.product.tax_rate / 100))  # Netto-Preis pro Produkt
            tax_amount = item.price - netto_price  # Steuerbetrag pro Produkt
            total_netto += netto_price * item.quantity  # Netto-Summe
            total_brutto += item.price * item.quantity  # Brutto-Summe
            total_tax_order += tax_amount * item.quantity  # Steuer-Summe

        # Summen auf 2 Dezimalstellen runden
        total_netto = round(total_netto, 2)
        total_brutto = round(total_brutto, 2)
        total_tax_order = round(total_tax_order, 2)

        # Debugging: Überprüfe die berechneten Werte
        print(f"Total Netto: {total_netto}, Total Brutto: {total_brutto}, Total Steuer: {total_tax_order}")

        # Den Client aus der Session laden, falls er vorhanden ist
        client = None
        if 'cart_client_id' in session:
            client = Client.query.filter_by(id=session['cart_client_id']).first()

        return render_template(
            'backend/user_templates/dashboard/view_meine_bestellung.html',
            user=user,
            order=order,
            order_items=order_items,
            total_price=total_brutto,
            page_name="Bestelldetails",
            total_tax=total_tax_order,
            total_netto=total_netto,
            cart=cart,  # Den Warenkorb dem Template übergeben
            total_cost=total_cost,
            tax_details=tax_details,
            total_items=sum(item['quantity'] for item in cart.values()),  # Anzahl der Artikel im Warenkorb berechnen
            client=client  # Den Client dem Template übergeben
        )

    except NotFound:
        print("Bestellung wurde nicht gefunden!")
        flash('Bestellung nicht gefunden.', 'danger')
        return redirect(url_for('user_bp.meine_bestellungen'))
    except Exception as e:
        print(f"Fehler beim Abrufen der Bestelldetails: {e}")
        flash('Fehler beim Abrufen der Bestelldetails. Bitte versuche es erneut.', 'danger')
        return redirect(url_for('user_bp.meine_bestellungen'))














    
    

   
    















# Logout Route für User
@user_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Du hast dich erfolgreich ausgeloggt.", "success")
    return redirect(url_for('user_bp.login'))
