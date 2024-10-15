from flask import Blueprint, render_template, request, redirect, session, url_for, flash, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Message
from app.models.admin_model import Admin
from app import db, mail
from itsdangerous import URLSafeTimedSerializer
from werkzeug.utils import secure_filename
import time
import os
from app.models.client_model import Client
from hashlib import md5
from app import serializer
from flask import flash
from app.models.order import Order




# Definieren von Blueprint
admin_bp = Blueprint('admin_bp', __name__, template_folder='../templates/backend/admin_templates')

# Definiere die erlaubten Dateitypen für hochladen von DAteien beispiel ProfilBilder
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# funktion zum Löschen des alten Bildes
def delete_old_image(old_photo_path):
    full_path = os.path.join(current_app.root_path, 'static', 'upload', 'admin_bilder', 'admin_profile', old_photo_path)
    if os.path.exists(full_path):
        os.remove(full_path)
        print(f"Altes Bild gelöscht: {full_path}")  # Debugging-Information
    else:
        print(f"Bild nicht gefunden: {full_path}")  # Debugging-Information


# Login Route für admin
@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if "adminname" in session:
        return redirect(url_for('admin_bp.dashboard'))

    errors = {}

    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        
        admin = Admin.query.filter_by(email=email).first()

        # Fehler bei Emailadresse 
        if not admin:
            errors['email'] = 'Ungültige E-Mail-Adresse.'

        # Fehler beim Passwort
        if admin and not admin.check_password(password):
            errors['password'] = 'Ungültiges Passwort.'

        # Wenn keine Fehler vorhanden sind, logge den Admin ein
        if not errors:
            session['admin_id'] = admin.id
            session['adminname'] = admin.adminname
            return redirect(url_for('admin_bp.dashboard'))

    return render_template("admin_login.html", errors=errors)


# Register Route für admin # Das muss später Weg
@admin_bp.route('/register', methods=["GET", "POST"])
def register():
    if "adminname" in session:
        return redirect(url_for('admin_bp.dashboard'))
    else:
        if request.method == "POST":
            adminname = request.form['adminname']
            email = request.form['email']
            password = request.form['password']
        
            admin = Admin.query.filter((Admin.adminname == adminname) | (Admin.email == email)).first()

            if admin:
                return render_template("admin_register.html", error="Benutzername oder E-Mail bereits vergeben")
            else:
                new_admin = Admin(adminname=adminname, email=email)
                new_admin.set_password(password)
                db.session.add(new_admin)
                db.session.commit()
                session['adminname'] = adminname
                session['admin_id'] = new_admin.id  # Hier bekommt Admin einID
                return redirect(url_for('admin_bp.dashboard'))

    return render_template("admin_register.html")



# Passwort zurücksetzen Anfrage 
@admin_bp.route('/password_reset_request', methods=["GET", "POST"])
def password_reset_request():
    if request.method == "POST":
        email = request.form['email']
        admin = Admin.query.filter_by(email=email).first() 

        if admin:
            s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
            token = s.dumps(admin.email, salt='password-reset-salt')
            reset_url = url_for('admin_bp.password_reset_token', token=token, _external=True)

            msg = Message('Password Reset Request',
                          sender='expressmahlzeit@gmail.com',
                          recipients=[admin.email])
            msg.body = f"Bitte klicke auf den folgenden Link, um dein Passwort zurückzusetzen: {reset_url}"
            mail.send(msg)

            flash('Eine E-Mail zum Zurücksetzen des Passworts wurde gesendet.')
            return redirect(url_for('admin_bp.password_reset_request'))

    return render_template("admin_password_reset_request.html")

# Passwort zurücksetzen
@admin_bp.route('/password_reset/<token>', methods=["GET", "POST"])
def password_reset_token(token):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=3600)
    except:
        flash('Der Token ist ungültig oder abgelaufen.')
        return redirect(url_for('admin_bp.password_reset_request'))

    if request.method == "POST":
        password = request.form['password']
        admin = Admin.query.filter_by(email=email).first() 

        if admin:
            admin.set_password(password)
            db.session.commit()
            flash('Dein Passwort wurde erfolgreich geändert.')
            return redirect(url_for('admin_bp.password_reset_request'))
        else:
            flash('Benutzer nicht gefunden.')
            return redirect(url_for('admin_bp.password_reset_request'))

    return render_template('backend/admin_templates/admin_password_reset_form.html', token=token)



# admin Dashboard
@admin_bp.route("/dashboard")
def dashboard():
    if "adminname" not in session:
        return redirect(url_for('admin_bp.login'))
    
    
    admin = Admin.query.get(session['admin_id'])
    return render_template("admin_dashboard.html", admin=admin, page_name="Dashboard")




# Profil-Seite anzeigen
@admin_bp.route("/profile", methods=["GET", "POST"])
def profile():
    if "admin_id" not in session:
        return redirect(url_for('admin_bp.login'))
    
    admin = Admin.query.get(session['admin_id'])
    
    return render_template("admin_profile.html", admin=admin, page_name="Profil")




# Profil daten bon Admin Bearbeiten
@admin_bp.route("/profile_update", methods=["POST"])
def profile_update():
    if "admin_id" not in session:
        return redirect(url_for('admin_bp.login'))

    admin = Admin.query.get(session['admin_id'])

    # Aktualisiere die Felder mit den Formulardaten
    admin.adminname = request.form.get('adminname')
    admin.email = request.form.get('email')
    admin.phone_number = request.form.get('phone_number')
    admin.street = request.form.get('street')
    admin.house_number = request.form.get('house_number')
    admin.postal_code = request.form.get('postal_code')
    admin.city = request.form.get('city')

    # Überprüfe, ob ein neues Bild hochgeladen wurde
    if 'photo' in request.files:
        file = request.files['photo']
        if file and file.filename != '' and allowed_file(file.filename):
            print(f"Dateiname: {file.filename}")  # Debugging-Information
            filename = secure_filename(file.filename)
            file_ext = filename.rsplit('.', 1)[1].lower()
            new_filename = f"{int(time.time())}.{file_ext}"  # Einzigartiger Dateiname basierend auf Zeitstempel

            # Verwende den richtigen Pfad relativ zum app-Ordner
            upload_folder = os.path.join(current_app.root_path, 'static', 'upload', 'admin_bilder', 'admin_profile')

            # Prüfe, ob das Verzeichnis existiert, wenn nicht, erstelle es
            os.makedirs(upload_folder, exist_ok=True)

            # Speichere die Datei
            file_path = os.path.join(upload_folder, new_filename)
            print(f"Speicherpfad: {file_path}")  # Debugging-Information
            file.save(file_path)

            # Speichere den relativen Pfad in der Datenbank
            admin.photo = os.path.join('upload', 'admin_bilder', 'admin_profile', new_filename).replace('\\', '/')
            print(f"Relativer Pfad in der DB: {admin.photo}")  # Debugging-Information

            # Debug-Ausgabe
            print(f"Datei gespeichert: {file_path}")
        else:
            print("Keine gültige Datei hochgeladen oder Dateityp nicht erlaubt")  # Debugging-Information

    # Speichere die Änderungen in der Datenbank
    db.session.commit()

    

    flash('Profil erfolgreich aktualisiert!', 'success')
    return redirect(url_for('admin_bp.profile'))




# admin Password ändern im Profil
@admin_bp.route("/change_password", methods=["GET", "POST"])
def change_password():
    if "admin_id" not in session:
        return redirect(url_for('admin_bp.login'))

    admin = Admin.query.get(session['admin_id'])
    errors = {}

    if request.method == 'POST':
        # Hol die eingegebenen Werte aus dem Formular
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # Überprüfung des aktuellen Passworts
        if not admin.check_password(current_password):
            errors['current_password'] = 'Das aktuelle Passwort ist falsch.'

        # Überprüfung, ob das neue Passwort mit der Bestätigung übereinstimmt
        if new_password != confirm_password:
            errors['confirm_password'] = 'Die neuen Passwörter stimmen nicht überein.'

        # Wenn keine Fehler vorhanden sind, aktualisiere das Passwort
        if not errors:
            admin.set_password(new_password)
            db.session.commit()

            flash('Passwort erfolgreich aktualisiert!', 'success')
            return redirect(url_for('admin_bp.change_password'))

    return render_template('admin_change_password.html', admin=admin, errors=errors, page_name="Passwort ändern")










@admin_bp.route("/logout")
def logout():
    session.pop('adminname', None)
    session.pop('admin_id', None)
    
    return redirect(url_for('admin_bp.login'))


@admin_bp.route('/all_restaurants', methods=['GET'])
def all_restaurants():
    if "adminname" not in session:
        return redirect(url_for('admin_bp.login'))

    # Lade das Admin-Objekt anhand der Admin-ID in der Sitzung
    admin = Admin.query.get(session['admin_id'])

    # Hol alle Clients aus der Datenbank
    clients = Client.query.all()

    # Übergabe der `admin`-Variable an das Template
    return render_template('admin_all_restaurants.html', clients=clients, admin=admin, page_name="Alle Restaurants")



# Restaurants hinzufügen
@admin_bp.route('/add_restaurants', methods=['GET', 'POST'])
def add_restaurants():
    if "admin_id" not in session:
        return redirect(url_for('admin_bp.login'))

    # Lade das Admin-Objekt anhand der Admin-ID in der Sitzung
    admin = Admin.query.get(session['admin_id'])

    if request.method == 'POST':
        clientname = request.form['clientname']
        email = request.form['email']
        phone_number = request.form.get('phone_number')
        street = request.form.get('street')
        house_number = request.form.get('house_number')
        postal_code = request.form.get('postal_code')
        city = request.form.get('city')
        status = request.form.get('status', type=int)  # 1 für aktiv, 0 für inaktiv

        # Überprüfe, ob der `clientname` oder die `email` bereits existieren
        existing_client = Client.query.filter((Client.clientname == clientname) | (Client.email == email)).first()
        if existing_client:
            flash(f"Ein Client mit dem Namen '{clientname}' oder der E-Mail '{email}' existiert bereits. Bitte wählen Sie einen anderen Namen oder eine andere E-Mail-Adresse.", "danger")
            return render_template('admin_add_restaurants.html', admin=admin, page_name="Restaurant hinzufügen")

        # Erstelle einen temporären `md5`-Hash
        temporary_password = "temporary_password"
        temporary_md5_hash = f'md5${md5(temporary_password.encode()).hexdigest()}'

        # Erstelle einen neuen Client mit dem temporären Passwort-Hash
        new_client = Client(
            clientname=clientname,
            email=email,
            phone_number=phone_number,
            street=street,
            house_number=house_number,
            postal_code=postal_code,
            city=city,
            status=status,
            password_hash=temporary_md5_hash  # Setze den temporären md5-Hash
        )

        # Füge den neuen Client zur Datenbank hinzu und speichere ihn
        db.session.add(new_client)
        db.session.commit()  # Dies sorgt dafür, dass die client.id verfügbar ist

        # Sende eine E-Mail an den Client, um das Passwort festzulegen
        send_password_set_email(new_client)

        flash('Neuer Client wurde erfolgreich hinzugefügt. Eine E-Mail zur Passworterstellung wurde gesendet.', 'success')
        return redirect(url_for('admin_bp.all_restaurants'))  # Gehe zurück zur Übersicht

    return render_template('admin_add_restaurants.html', admin=admin, page_name="Restaurant hinzufügen")

def send_password_set_email(client):
    """Funktion zum Senden der E-Mail, um ein Passwort festzulegen."""
    # Erstelle einen sicheren Token basierend auf der Client-ID
    token = serializer.dumps(client.id, salt='password-set')

    # Erstelle die URL für das Zurücksetzen des Passworts
    password_set_url = url_for('client_bp.client_password_set_admin', token=token, _external=True)

    # Erstelle die E-Mail-Nachricht
    msg = Message("Passwort festlegen", sender="expressmahlzeit@gmail.com", recipients=[client.email])
    msg.body = render_template('email/password_set_email.txt', client=client, password_set_url=password_set_url)
    msg.html = render_template('email/password_set_email.html', client=client, password_set_url=password_set_url)

    # Sende die E-Mail
    mail.send(msg)




@admin_bp.route('/view_order/<int:order_id>', methods=['GET'])
def view_order(order_id):
    if "adminname" not in session:
        return redirect(url_for('admin_bp.login'))
    
    admin = Admin.query.get(session['admin_id'])

    # Lade die Bestellung basierend auf der übergebenen order_id
    order = Order.query.get_or_404(order_id)

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

    # Übergebe die Bestellung und die berechneten Summen an das Template
    return render_template('bestellungen/admin_view_order.html', admin=admin, order=order, 
                           total_netto=total_netto, total_brutto=total_brutto, 
                           total_tax=total_tax)


@admin_bp.route('/edit_order/<int:order_id>', methods=['GET', 'POST'])
def edit_order(order_id):
    if "adminname" not in session:
        return redirect(url_for('admin_bp.login'))
    
    admin = Admin.query.get(session['admin_id'])
    
    order = Order.query.get_or_404(order_id)
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

    if request.method == 'POST':
        # Aktualisiere die Bestellinformationen
        order.phone = request.form.get('phone')
        order.address = request.form.get('address')
        order.payment_type = request.form.get('payment_type')
        order.amount = request.form.get('amount')
        order.total_amount = request.form.get('total_amount')  # Falls du den Gesamtbetrag ändern möchtest

        # Status aktualisieren, wenn vorhanden
        new_status = request.form.get('status')
        if new_status:
            order.status = new_status
        
        # Speichere die Änderungen in der Datenbank
        db.session.commit()
        flash('Bestellung erfolgreich aktualisiert!', 'success')
        return redirect(url_for('admin_bp.view_order', order_id=order_id))
    
    return render_template('bestellungen/admin_edit_order.html',admin=admin, order=order, 
                           total_netto=total_netto, total_brutto=total_brutto, 
                           total_tax=total_tax)


@admin_bp.route('/delete_order/<int:order_id>', methods=['POST'])
def delete_order(order_id):
    if "adminname" not in session:
        return redirect(url_for('admin_bp.login'))
    
    order = Order.query.get_or_404(order_id)
    
    # Lösche die Bestellung
    db.session.delete(order)
    db.session.commit()
    
    flash('Bestellung erfolgreich gelöscht!', 'success')
    return redirect(url_for('admin_bp.all_orders'))







# Route für alle Bestellungen
@admin_bp.route('/all_orders', methods=['GET'])
def all_orders():
    if "adminname" not in session:
        return redirect(url_for('admin_bp.login'))

    # Lade das Admin-Objekt anhand der Admin-ID in der Sitzung
    admin = Admin.query.get(session['admin_id'])

    # Hol alle Bestellungen aus der Datenbank
    orders = Order.query.all()

    # Übergabe der `admin`-Variable und `orders`-Liste an das Template
    return render_template('bestellungen/admin_all_orders.html', allData=orders, admin=admin, enumerate=enumerate, page_name="Alle Bestellungen")


# Route für bestätigte Bestellungen
@admin_bp.route('/confirmed_orders', methods=['GET'])
def confirmed_orders():
    if "adminname" not in session:
        return redirect(url_for('admin_bp.login'))

    # Lade das Admin-Objekt anhand der Admin-ID in der Sitzung
    admin = Admin.query.get(session['admin_id'])

    # Hol alle bestätigten Bestellungen aus der Datenbank
    confirmed_orders = Order.query.filter_by(status='confirmed').all()

    # Übergabe der `admin`-Variable und der bestätigten Bestellungen an das Template
    return render_template('bestellungen/admin_confirmed_orders.html', allData=confirmed_orders, admin=admin, enumerate=enumerate, page_name="Confirmed Orders")


# Route für ausstehende (Pending) Bestellungen
@admin_bp.route('/pending_orders', methods=['GET'])
def pending_orders():
    if "adminname" not in session:
        return redirect(url_for('admin_bp.login'))

    # Lade alle Bestellungen mit dem Status 'pending'
    pending_orders = Order.query.filter_by(status='pending').all()

    # Lade das Admin-Objekt anhand der Admin-ID in der Sitzung
    admin = Admin.query.get(session['admin_id'])

    # Übergabe der `admin`-Variable und `pending_orders`-Liste an das Template
    return render_template('bestellungen/admin_pending_orders.html', allData=pending_orders, admin=admin, enumerate=enumerate, page_name="Pending Orders")


# Route für ausgelieferte Bestellungen
@admin_bp.route('/delivered_orders', methods=['GET'])
def delivered_orders():
    if "adminname" not in session:
        return redirect(url_for('admin_bp.login'))

    # Lade das Admin-Objekt anhand der Admin-ID in der Sitzung
    admin = Admin.query.get(session['admin_id'])

    # Hol alle ausgelieferten Bestellungen aus der Datenbank
    delivered_orders = Order.query.filter_by(status='delivered').all()

    # Übergabe der `admin`-Variable und der ausgelieferten Bestellungen an das Template
    return render_template('bestellungen/admin_delivered_orders.html', allData=delivered_orders, admin=admin, enumerate=enumerate, page_name="Delivered Orders")


@admin_bp.route('/update_order_status/<int:order_id>', methods=['POST'])
def update_order_status(order_id):
    # Bestellstatus aktualisieren
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')  # Nimm den neuen Status aus dem Formular

    if new_status:
        order.status = new_status  # Aktualisiere den Status
        db.session.commit()  # Speichere die Änderung in der Datenbank
        flash('Bestellstatus erfolgreich aktualisiert!', 'success')
    else:
        flash('Fehler beim Aktualisieren des Status.', 'error')

    return redirect(url_for('admin_bp.view_order', order_id=order_id))  # Zurück zur Bestelldetailseite

