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

        # Überprüfe, ob der clientname oder die email bereits existieren
        existing_client = Client.query.filter((Client.clientname == clientname) | (Client.email == email)).first()
        if existing_client:
            flash(f"Ein Client mit dem Namen '{clientname}' oder der E-Mail '{email}' existiert bereits. Bitte wählen Sie einen anderen Namen oder eine andere E-Mail-Adresse.", "danger")
            return render_template('admin_add_restaurants.html', admin=admin, page_name="Restaurant hinzufügen")

        # Erstelle einen temporären md5-Hash
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