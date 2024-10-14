# app/routes/checkout.py

from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from flask_login import login_required, current_user  # Um sicherzustellen, dass der Benutzer eingeloggt ist
from app.models.client_model import Client
from app.routes.add_to_cart import get_total_cost  # Importiere die get_total_cost Funktion für die Berechnung
from datetime import datetime
from app.models.order import Order
from app.models.order_item import OrderItem
from app import db


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

    # Client-ID aus der Session holen und Client-Objekt abrufen
    client_id = session.get('cart_client_id')
    client = Client.query.get(client_id) if client_id else None

    if not client:
        flash('Kein Client zugeordnet. Bitte wähle einen gültigen Client.', 'warning')
        return redirect(url_for('frontend_bp.home'))

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

    # Zahlungsart (z.B. bar, PayPal) aus dem Formular
    payment_type = request.form.get('payment_type')

    # Client-ID aus der Session holen
    client_id = session.get('cart_client_id')
    client = Client.query.get(client_id) if client_id else None

    if not client:
        flash('Kein Client zugeordnet. Bitte wähle einen gültigen Client.', 'warning')
        return redirect(url_for('frontend_bp.home'))

    # Bestellung erstellen
    order = Order(
        user_id=current_user.id,
        client_id=client.id,
        name=current_user.username,   # Benutzername wird in der Bestellung gespeichert
        email=current_user.email,
        phone=current_user.phone_number,     # Telefonnummer des Benutzers (korrektes Feld)
        address=f"{current_user.street} {current_user.house_number}, {current_user.postal_code} {current_user.city}",  # Adresse des Benutzers
        payment_type=payment_type,
        amount=total_cost,            # Gesamtkosten der Bestellung
        total_amount=total_cost + total_tax,  # Gesamtsumme inklusive Steuern
        status='pending'  # Status der Bestellung, standardmäßig "pending"
    )

    db.session.add(order)
    db.session.commit()

    # Bestellung erfolgreich erstellt, jetzt die bestellten Produkte hinzufügen
    for product_id, item in cart.items():
        if product_id != 'client_id':  # Ignoriere die client_id im Warenkorb
            order_item = OrderItem(
                order_id=order.id,
                product_id=product_id,
                client_id=client.id,  # Der Client, der das Produkt anbietet
                quantity=item['quantity'],
                price=item['price']  # Einzelpreis des Produkts
            )
            db.session.add(order_item)

    db.session.commit()

    # Speichere den aktuellen Warenkorb und Client-ID für die Thank-You-Seite
    session['thank_you_cart_client_id'] = client.id
    session['thank_you_cart'] = cart  # Den aktuellen Warenkorb in der Session für Thank-You speichern

    # Erfolgsnachricht anzeigen und Warenkorb leeren
    flash('Bestellung erfolgreich abgeschlossen!', 'success')
    session.pop('cart', None)  # Warenkorb nach Abschluss leeren
    session.pop('cart_client_id', None)  # Setze auch den `cart_client_id` zurück
    session.pop('tax_details', None)  # Steuerinformationen ebenfalls zurücksetzen

    return redirect(url_for('frontend_bp.thank_you'))



