# app/routes/checkout.py

from flask import Blueprint, render_template, session, redirect, url_for, flash
from app.routes.add_to_cart import get_total_cost  # Importiere die get_total_cost Funktion für die Berechnung
from app.models.product import Product
from app.models.client_model import Client
from datetime import datetime

# Blueprint für Checkout erstellen
checkout_bp = Blueprint('checkout_bp', __name__, template_folder='templates/frontend')

@checkout_bp.route('/checkout', methods=['GET'])
def checkout():
    """
    Zeigt die Checkout-Seite mit den Inhalten des Warenkorbs und den Berechnungen für Gesamtkosten und Steuer.
    """
    client = Client.query.get(id)
    current_time = datetime.now()
    # Warenkorbdaten aus der Session holen
    cart = session.get('cart', {})
    if not cart:
        flash('Ihr Warenkorb ist leer. Fügen Sie zuerst Produkte hinzu.', 'warning')
        return redirect(url_for('frontend_bp.home'))

    # Berechnung der Gesamtkosten und Steuer mit der vorhandenen Route
    response = get_total_cost()
    data = response.json

    total_cost = data['total_cost']  # Gesamtkosten
    total_tax = data['tax']          # Steuerbetrag
    grand_total = data['grand_total']  # Gesamtsumme inkl. Steuer
    tax_details = {}  # Steuerdetails initialisieren

    # Berechnung der Steuerdetails basierend auf den Produkten im Warenkorb
    for product_id, item in cart.items():
        tax_rate = item.get('tax_rate', 0)
        item_total = item['price'] * item['quantity']
        
        # Steuer berechnen
        tax = item_total * (tax_rate / (100 + tax_rate))
        
        # Steuerbetrag pro Steuerkategorie sammeln
        if tax_rate in tax_details:
            tax_details[tax_rate] += tax
        else:
            tax_details[tax_rate] = tax

    return render_template('frontend/checkout.html', cart=cart, total_cost=total_cost, total_tax=total_tax, grand_total=grand_total, tax_details=tax_details, client=client, current_time=current_time)

@checkout_bp.route('/process_checkout', methods=['POST'])
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

    # Beispiel für das Speichern der Bestellung in der Datenbank (ggf. ein `Order`-Modell erstellen und speichern)
    # order = Order(total_cost=total_cost, total_tax=total_tax, ...)
    # db.session.add(order)
    # db.session.commit()

    # Erfolgsnachricht anzeigen und Warenkorb leeren
    flash('Bestellung erfolgreich abgeschlossen!', 'success')
    session.pop('cart', None)  # Warenkorb nach Abschluss leeren
    session.pop('cart_client_id', None)  # Setze auch den `cart_client_id` zurück
    session.pop('tax_details', None)  # Steuerinformationen ebenfalls zurücksetzen

    return redirect(url_for('frontend_bp.home'))
