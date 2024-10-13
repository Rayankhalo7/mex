# app/routes/checkout.py

from flask import Blueprint, render_template, session, redirect, url_for, flash
from flask_login import login_required, current_user  # Um sicherzustellen, dass der Benutzer eingeloggt ist
from app.models.client_model import Client
from app.routes.add_to_cart import get_total_cost  # Importiere die get_total_cost Funktion für die Berechnung
from datetime import datetime

# Blueprint für Checkout erstellen
checkout_bp = Blueprint('checkout_bp', __name__, template_folder='templates/frontend')

@checkout_bp.route('/checkout', methods=['GET'])
@login_required  # Nur eingeloggte Benutzer dürfen den Checkout durchführen
def checkout():
    """
    Zeigt die Checkout-Seite mit den Inhalten des Warenkorbs und den Berechnungen für Gesamtkosten und Steuer.
    """
    # Warenkorbdaten aus der Session holen
    cart = session.get('cart', {})
    
    if not cart:
        flash('Ihr Warenkorb ist leer. Fügen Sie zuerst Produkte hinzu.', 'warning')
        return redirect(url_for('frontend_bp.home'))

    # Berechne die Gesamtkosten und Steuer mit der vorhandenen Funktion
    response = get_total_cost()
    data = response.json

    total_cost = data['total_cost']  # Gesamtkosten
    total_tax = data['tax']          # Steuerbetrag
    grand_total = data['grand_total']  # Gesamtsumme inkl. Steuer
    tax_details = data['tax_details']  # Steuerdetails für unterschiedliche Steuersätze
    total_items = data['total_items']  # Gesamtartikelanzahl im Warenkorb

    client = Client.query.get(session.get('cart_client_id'))  # Hole den Client anhand der Client-ID
    current_time = datetime.now()

    return render_template('frontend/checkout.html', 
                           cart=cart, 
                           total_cost=total_cost, 
                           total_tax=total_tax, 
                           grand_total=grand_total, 
                           tax_details=tax_details,
                           total_items=total_items,
                           client=client,
                           current_time=current_time)


@checkout_bp.route('/process_checkout', methods=['POST'])
@login_required  # Nur eingeloggte Benutzer dürfen den Checkout durchführen
def process_checkout():
    """
    Verarbeitet die Bestellung, speichert die Bestelldaten und leert den Warenkorb nach Abschluss.
    """
    # Stelle sicher, dass der Warenkorb nicht leer ist
    cart = session.get('cart', {})
    if not cart:
        flash('Ihr Warenkorb ist leer. Fügen Sie zuerst Produkte hinzu.', 'warning')
        return redirect(url_for('frontend_bp.home'))

    # Berechne die Gesamtkosten und Steuer erneut zur Sicherheit
    response = get_total_cost()
    data = response.json
    total_cost = data['total_cost']
    total_tax = data['tax']

    # Erfolgsnachricht anzeigen und Warenkorb leeren
    flash('Bestellung erfolgreich abgeschlossen!', 'success')
    session.pop('cart', None)  # Warenkorb nach Abschluss leeren
    session.pop('cart_client_id', None)  # Setze auch den `cart_client_id` zurück
    session.pop('tax_details', None)  # Steuerinformationen ebenfalls zurücksetzen

    return redirect(url_for('frontend_bp.home'))
