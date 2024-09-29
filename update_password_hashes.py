from app import db
from app.models.client_model import Client  # Importiere das Client-Modell
import hashlib

def update_password_hashes():
    # Hole alle Clients aus der Datenbank
    clients = Client.query.all()

    for client in clients:
        # Prüfe, ob der aktuelle Passwort-Hash nicht bereits ein md5-Hash ist
        if not client.password_hash.startswith('md5$'):
            # Angenommen, client.password_hash ist aktuell ein Klartext-Passwort oder ein anderer Hash
            # Erstelle den neuen md5-Hash des Passworts
            md5_hash = hashlib.md5(client.password_hash.encode()).hexdigest()
            # Speichere den neuen Hash in der Datenbank im Format 'md5$<hash>'
            client.password_hash = f'md5${md5_hash}'
            print(f"Updated client {client.email} with md5 hash: {client.password_hash}")

    # Änderungen in der Datenbank speichern
    db.session.commit()
    print("Alle Passwort-Hashes wurden erfolgreich aktualisiert.")

# Funktion aufrufen, um die Aktualisierung durchzuführen
update_password_hashes()
