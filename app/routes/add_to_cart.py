# app/routes/add_to_cart.py
from flask import Blueprint, session, redirect, url_for, flash, request, jsonify, render_template
from flask_login import current_user
from app.models.product import Product  # Importiere das Produktmodell
from app.models.client_model import Client  # Importiere das Client-Modell
from app.models.cities import City


# Blueprint für den Warenkorb erstellen
cart_bp = Blueprint('cart', __name__)

# Route zum Hinzufügen von Produkten zum Warenkorb
# Route zum Hinzufügen von Produkten zum Warenkorb
@cart_bp.route('/add_to_cart/<int:client_id>/<int:product_id>', methods=['GET', 'POST'])
def add_to_cart(client_id, product_id):
    # Abrufen des Produkts
    product = Product.query.get_or_404(product_id)
    
    # Falls das Produkt nicht zum angegebenen Client gehört, einen Fehler zurückgeben
    if product.client_id != client_id:
        flash('Das Produkt gehört zu einem anderen Client.', 'danger')
        return redirect(request.referrer or url_for('frontend_bp.client_detail', client_id=client_id))

    # Warenkorb aus der Session holen oder einen neuen erstellen
    cart = session.get('cart', {})

    # Überprüfen, ob ein Client im Warenkorb existiert
    if 'cart_client_id' not in session:
        session['cart_client_id'] = client_id
    # Wenn der Client im Warenkorb nicht übereinstimmt, Warenkorb leeren und Client wechseln
    elif session['cart_client_id'] != client_id:
        flash("Du kannst nur Produkte von einem Client gleichzeitig im Warenkorb haben. Der Warenkorb wurde geleert.", "danger")
        session['cart'] = {}
        session['cart_client_id'] = client_id

    # Produkt zum Warenkorb hinzufügen oder die Menge erhöhen
    if str(product_id) in cart:
        cart[str(product_id)]['quantity'] += 1
    else:
        cart[str(product_id)] = {
            'quantity': 1,
            'name': product.name,
            'price': product.price,
            'image': product.image,
            'client_id': client_id,
            'tax_rate': product.tax_rate,
            'is_must_popular': product.is_must_popular,
            'is_bestseller': product.is_bestseller
        }

    # Warenkorb in der Session speichern und Session als verändert markieren
    session['cart'] = cart
    session.modified = True  # Markiert die Session als modifiziert

    # Erfolgsmeldung
    flash(f"{product.name} erfolgreich zum Warenkorb hinzugefügt!", 'success')

    # Weiterleitung zur Detailseite des Clients (ohne `cities` als separates Argument)
    return redirect(request.referrer or url_for('frontend_bp.client_detail', client_id=client_id))



# Route zum Erhöhen der Produktmenge im Warenkorb
@cart_bp.route('/increase_quantity/<int:product_id>', methods=['POST'])
def increase_quantity(product_id):
    cart = session.get('cart', {})

    if str(product_id) in cart:
        cart[str(product_id)]['quantity'] += 1
        session['cart'] = cart
        return jsonify({"status": "success", "message": "Menge erhöht", "quantity": cart[str(product_id)]['quantity']})

    return jsonify({"status": "error", "message": "Produkt nicht im Warenkorb"})


# Route zum Verringern der Produktmenge im Warenkorb
@cart_bp.route('/decrease_quantity/<int:product_id>', methods=['POST'])
def decrease_quantity(product_id):
    cart = session.get('cart', {})

    if str(product_id) in cart:
        if cart[str(product_id)]['quantity'] > 1:
            cart[str(product_id)]['quantity'] -= 1
            session['cart'] = cart
            return jsonify({"status": "success", "message": "Menge verringert", "quantity": cart[str(product_id)]['quantity']})
        else:
            del cart[str(product_id)]  # Produkt aus dem Warenkorb entfernen, wenn Menge auf 0 geht
            session['cart'] = cart

            # Überprüfe, ob der Warenkorb jetzt leer ist und die `cart_client_id` zurücksetzen
            if len(cart) == 0:
                session.pop('cart_client_id', None)

            return jsonify({"status": "success", "message": "Produkt entfernt"})

    return jsonify({"status": "error", "message": "Produkt nicht im Warenkorb"})


# Route zum Entfernen eines Produkts aus dem Warenkorb
@cart_bp.route('/remove_from_cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    cart = session.get('cart', {})

    if str(product_id) in cart:
        del cart[str(product_id)]  # Produkt aus dem Warenkorb löschen
        session['cart'] = cart  # Warenkorb in der Session aktualisieren

        # Überprüfe, ob der Warenkorb jetzt leer ist und die `cart_client_id` zurücksetzen
        if len(cart) == 0:
            session.pop('cart_client_id', None)

        return jsonify({"status": "success", "message": "Produkt erfolgreich entfernt"})

    return jsonify({"status": "error", "message": "Produkt nicht im Warenkorb"})


@cart_bp.route('/cart')
def show_cart():
    cart = session.get('cart', {})
    client_id = session.get('cart_client_id')

    if client_id:
        client = Client.query.get(client_id)
    else:
        flash('Kein Client zugeordnet. Bitte wähle einen gültigen Client.', 'warning')
        client = None
    
    # Berechne die Anzahl der Artikel
    total_items = sum(item['quantity'] for item in cart.values())
    
    # Rendere das Template und übergebe `cart`, `total_items`, und `client`
    return render_template('cart.html', cart=cart, total_items=total_items, client=client)


# API-Route, die JSON zurückgibt
@cart_bp.route('/get_total_cost', methods=['GET'])
def get_total_cost_api():
    cart = session.get('cart', {})
    total_cost, total_tax, tax_details, total_items = calculate_cart_totals(cart)

    return jsonify({
        "total_cost": total_cost,
        "tax": total_tax,
        "grand_total": total_cost,
        "tax_details": tax_details,
        "cart": cart,
        "total_items": total_items
    })

# Hilfsfunktion zur Berechnung der Gesamtkosten für Templates
def calculate_cart_totals(cart):
    total_cost = 0.0
    total_tax = 0.0
    tax_details = {}
    total_items = 0

    # Berechne die Gesamtkosten und Steuern basierend auf dem Preis
    for product_id, item in cart.items():
        product = Product.query.get(product_id)
        if product:
            item_total = item['price'] * item['quantity']
            total_cost += item_total
            tax_rate = product.tax_rate if product.tax_rate is not None else 0.0
            tax = item_total * (tax_rate / (100 + tax_rate))
            total_tax += tax
            if tax_rate in tax_details:
                tax_details[tax_rate] += tax
            else:
                tax_details[tax_rate] = tax
            total_items += item['quantity']
        else:
            print(f"Product with ID {product_id} not found")

    return total_cost, total_tax, tax_details, total_items


def calculate_cart_totals(cart):
    total_cost = 0.0
    total_tax = 0.0
    tax_details = {}
    total_items = 0

    # Berechne die Gesamtkosten und Steuern basierend auf dem Preis
    for product_id, item in cart.items():
        product = Product.query.get(product_id)
        if product:
            item_total = item['price'] * item['quantity']
            total_cost += item_total
            tax_rate = product.tax_rate if product.tax_rate is not None else 0.0
            tax = item_total * (tax_rate / (100 + tax_rate))
            total_tax += tax
            if tax_rate in tax_details:
                tax_details[tax_rate] += tax
            else:
                tax_details[tax_rate] = tax

            total_items += item['quantity']
        else:
            print(f"Product with ID {product_id} not found")

    return total_cost, total_tax, tax_details, total_items