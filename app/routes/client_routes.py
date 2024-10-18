from flask import Blueprint, render_template, request, redirect, session, url_for, flash, current_app, request
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
from app.models.order import Order
from app.models.lieferzeiten import Lieferzeiten
from app.models.opening_hours import OpeningHours
from geopy.geocoders import Nominatim







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


# client Dashboard
@client_bp.route("/allgemein")
def allgemein():
    if "clientname" not in session:
        return redirect(url_for('client_bp.login'))
    
    # Lade das Client-Objekt
    client = Client.query.get(session['client_id'])
    opening_hours = OpeningHours.query.filter_by(client_id=client.id).all()
    lieferzeiten = Lieferzeiten.query.filter_by(client_id=client.id).all()
    return render_template("client_allgemein.html", client=client, opening_hours=opening_hours, lieferzeiten=lieferzeiten, page_name="allgemein")






# Profil-Seite anzeigen
@client_bp.route("/profile", methods=["GET", "POST"])
def profile():
    if "client_id" not in session:
        return redirect(url_for('client_bp.login'))
    
    client = Client.query.get(session['client_id'])
    
    if request.method == "POST":
        # Hole die neue Stadt-ID aus dem Formular (Angenommen, city enthält die ID)
        new_city_id = request.form.get("city")
        
        # Überprüfen, ob der Benutzer die Stadt ändern möchte
        if new_city_id and int(new_city_id) != client.city.id:  # Vergleiche die IDs, ohne sie zuzuweisen
            flash("Das Ändern der Stadt ist nicht erlaubt.", "error")
            return redirect(url_for('client_bp.profile'))  # Um zu vermeiden, dass das Formular erneut gesendet wird

    return render_template("client_profile.html", client=client, page_name="Profil")






@client_bp.route("/profile_update", methods=["POST"])
def profile_update():
    if "client_id" not in session:
        return redirect(url_for('client_bp.login'))

    client = Client.query.get(session['client_id'])

    # Hole die neue Stadt aus dem Formular
    new_city = request.form.get('city')

    # Prüfe, ob der Benutzer versucht, die Stadt zu ändern
    if new_city and new_city != client.city.name:  # Vergleiche den Namen der Stadt
        flash("Das Ändern der Stadt ist nicht erlaubt.", "error")
        return redirect(url_for('client_bp.profile'))  # Verhindere die weitere Bearbeitung

    # Aktualisiere die Felder mit den Formulardaten, aber ignoriere die Stadt
    client.clientname = request.form.get('clientname')
    client.email = request.form.get('email')
    client.phone_number = request.form.get('phone_number')
    client.street = request.form.get('street')
    client.house_number = request.form.get('house_number')
    client.postal_code = request.form.get('postal_code')
    # client.city.name bleibt unverändert

    # Überprüfe, ob ein neues Bild hochgeladen wurde
    if 'photo' in request.files:
        file = request.files['photo']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_ext = filename.rsplit('.', 1)[1].lower()
            new_filename = f"{int(time.time())}.{file_ext}"  # Einzigartiger Dateiname basierend auf Zeitstempel

            # Verwende den richtigen Pfad relativ zum app-Ordner
            upload_folder = os.path.join(current_app.root_path, 'static', 'upload', 'client_bilder', 'client_profile')
            os.makedirs(upload_folder, exist_ok=True)  # Prüfe, ob das Verzeichnis existiert, wenn nicht, erstelle es

            file_path = os.path.join(upload_folder, new_filename)
            file.save(file_path)

            # Speichere den relativen Pfad in der Datenbank
            client.photo = os.path.join('upload', 'client_bilder', 'client_profile', new_filename).replace('\\', '/')

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




@client_bp.route('/view_order/<int:order_id>', methods=['GET'])
def view_order(order_id):
    if "clientname" not in session:
        return redirect(url_for('client_bp.login'))
    
    client = Client.query.get(session['client_id'])

    # Lade die Bestellung basierend auf der übergebenen order_id und überprüfe, ob sie zum Client gehört
    order = Order.query.filter_by(id=order_id, client_id=client.id).first_or_404()

    # Berechnungen im Backend
    total_netto = 0
    total_brutto = 0
    total_tax = 0

    # Berechne die Summen für die Bestellung
    for item in order.items:
        netto_price = item.price / (1 + (item.product.tax_rate / 100))  # Netto-Preis pro Produkt
        tax_amount = item.price - netto_price  # Steuerbetrag pro Produkt
        total_netto += netto_price * item.quantity  # Netto-Summe
        total_brutto += item.price * item.quantity  # Brutto-Summe
        total_tax += tax_amount * item.quantity  # Steuer-Summe

    # Rundung der Summen auf 2 Dezimalstellen
    total_netto = round(total_netto, 2)
    total_brutto = round(total_brutto, 2)
    total_tax = round(total_tax, 2)

    return render_template('bestellungen/client_view_order.html', client=client, order=order, 
                           total_netto=total_netto, total_brutto=total_brutto, 
                           total_tax=total_tax)


@client_bp.route('/edit_order/<int:order_id>', methods=['GET', 'POST'])
def edit_order(order_id):
    if "clientname" not in session:
        return redirect(url_for('client_bp.login'))
    
    client = Client.query.get(session['client_id'])
    
    order = Order.query.filter_by(id=order_id, client_id=client.id).first_or_404()
    
    total_netto = 0
    total_brutto = 0
    total_tax = 0

    for item in order.items:
        netto_price = item.price / (1 + (item.product.tax_rate / 100))
        tax_amount = item.price - netto_price
        total_netto += netto_price * item.quantity
        total_brutto += item.price * item.quantity
        total_tax += tax_amount * item.quantity

    total_netto = round(total_netto, 2)
    total_brutto = round(total_brutto, 2)
    total_tax = round(total_tax, 2)

    if request.method == 'POST':
        order.phone = request.form.get('phone')
        order.address = request.form.get('address')
        order.payment_type = request.form.get('payment_type')
        order.amount = request.form.get('amount')
        order.total_amount = request.form.get('total_amount')

        new_status = request.form.get('status')
        if new_status:
            order.status = new_status
        
        db.session.commit()
        flash('Bestellung erfolgreich aktualisiert!', 'success')
        return redirect(url_for('client_bp.view_order', order_id=order_id))
    
    return render_template('bestellungen/client_edit_order.html', client=client, order=order, 
                           total_netto=total_netto, total_brutto=total_brutto, 
                           total_tax=total_tax)


@client_bp.route('/delete_order/<int:order_id>', methods=['POST'])
def delete_order(order_id):
    if "clientname" not in session:
        return redirect(url_for('client_bp.login'))
    
    client = Client.query.get(session['client_id'])
    order = Order.query.filter_by(id=order_id, client_id=client.id).first_or_404()

    db.session.delete(order)
    db.session.commit()
    
    flash('Bestellung erfolgreich gelöscht!', 'success')
    return redirect(url_for('client_bp.all_orders'))


@client_bp.route('/all_orders', methods=['GET'])
def all_orders():
    if "clientname" not in session:
        return redirect(url_for('client_bp.login'))

    client = Client.query.get(session['client_id'])

    # Hol alle Bestellungen für diesen Client
    orders = Order.query.filter_by(client_id=client.id).all()

    return render_template('bestellungen/client_all_orders.html', allData=orders, client=client, enumerate=enumerate, page_name="Alle Bestellungen")


@client_bp.route('/confirmed_orders', methods=['GET'])
def confirmed_orders():
    if "clientname" not in session:
        return redirect(url_for('client_bp.login'))

    client = Client.query.get(session['client_id'])

    confirmed_orders = Order.query.filter_by(client_id=client.id, status='confirmed').all()

    return render_template('bestellungen/client_confirmed_orders.html', allData=confirmed_orders, client=client, enumerate=enumerate, page_name="Confirmed Orders")


@client_bp.route('/pending_orders', methods=['GET'])
def pending_orders():
    if "clientname" not in session:
        return redirect(url_for('client_bp.login'))

    client = Client.query.get(session['client_id'])

    pending_orders = Order.query.filter_by(client_id=client.id, status='pending').all()

    return render_template('bestellungen/client_pending_orders.html', allData=pending_orders, client=client, enumerate=enumerate, page_name="Pending Orders")


@client_bp.route('/delivered_orders', methods=['GET'])
def delivered_orders():
    if "clientname" not in session:
        return redirect(url_for('client_bp.login'))

    client = Client.query.get(session['client_id'])

    delivered_orders = Order.query.filter_by(client_id=client.id, status='delivered').all()

    return render_template('bestellungen/client_delivered_orders.html', allData=delivered_orders, client=client, enumerate=enumerate, page_name="Delivered Orders")


@client_bp.route('/update_order_status/<int:order_id>', methods=['POST'])
def update_order_status(order_id):
    client = Client.query.get(session['client_id'])
    order = Order.query.filter_by(id=order_id, client_id=client.id).first_or_404()

    new_status = request.form.get('status')
    if new_status:
        order.status = new_status
        db.session.commit()
        flash('Bestellstatus erfolgreich aktualisiert!', 'success')
    else:
        flash('Fehler beim Aktualisieren des Status.', 'error')

    return redirect(url_for('client_bp.view_order', order_id=order_id))








# Route für die Suchseite (search_page)
@client_bp.route('/search_page', methods=['GET'])
def search_page():
    return render_template('backend/client_templates/search_page.html')

# Route zum Suchen von Restaurants
@client_bp.route('/search_restaurants', methods=['GET'])
def search_restaurants():
    search_address = request.args.get('search_address')

    if not search_address:
        flash('Bitte geben Sie eine Adresse ein.', 'warning')
        return redirect(url_for('client_bp.search_page'))

    # Geocoding der Adresse in Breitengrad und Längengrad
    geolocator = Nominatim(user_agent="restaurant_search_app")
    
    try:
        location = geolocator.geocode(search_address)
    except Exception:
        flash('Fehler bei der Geocodierung. Bitte versuchen Sie es erneut.', 'danger')
        return redirect(url_for('client_bp.search_page'))

    if location:
        latitude = location.latitude
        longitude = location.longitude

        # Suche Restaurants in der Nähe basierend auf der Entfernung
        nearby_clients = Client.query.filter(
            db.func.sqrt(
                db.func.pow(Client.latitude - latitude, 2) +
                db.func.pow(Client.longitude - longitude, 2)
            ) < 0.1  # Radius in km
        ).all()

        return render_template('backend/client_templates/search_results.html', clients=nearby_clients, search_address=search_address)
    else:
        flash('Adresse nicht gefunden. Bitte versuchen Sie es erneut.', 'warning')
        return redirect(url_for('client_bp.search_page'))

# Route zur Suche nach Restaurants anhand von Koordinaten
@client_bp.route('/find_nearby_restaurants', methods=['GET'])
def find_nearby_restaurants():
    latitude = request.args.get('lat', type=float)
    longitude = request.args.get('lon', type=float)

    if latitude and longitude:
        # Finde nahegelegene Restaurants basierend auf Koordinaten
        nearby_clients = Client.query.filter(
            db.func.sqrt(
                db.func.pow(Client.latitude - latitude, 2) +
                db.func.pow(Client.longitude - longitude, 2)
            ) < 0.1  # Radius in km
        ).all()

        return render_template('backend/client_templates/search_results.html', clients=nearby_clients)
    else:
        flash('Standort konnte nicht ermittelt werden.', 'warning')
        return redirect(url_for('client_bp.search_page'))


