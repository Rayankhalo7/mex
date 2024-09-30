import smtplib

# SMTP-Konfiguration
MAIL_SERVER = "smtp.gmail.com"
MAIL_PORT = 587
MAIL_USERNAME = "rayankhalo7@gmail.com"
MAIL_PASSWORD = "dydt dbvp wfte nffm"  # App-spezifisches Passwort hier einfügen

try:
    # Verbinde mit dem SMTP-Server
    server = smtplib.SMTP(MAIL_SERVER, MAIL_PORT)
    server.starttls()
    server.login(MAIL_USERNAME, MAIL_PASSWORD)
    print("Verbindung erfolgreich! Anmeldeinformationen sind korrekt.")
    server.quit()
except smtplib.SMTPAuthenticationError as e:
    print(f"SMTPAuthenticationError: {e}")
except Exception as ex:
    print(f"Fehler: {ex}")
