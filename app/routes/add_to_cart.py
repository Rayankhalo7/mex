from flask import Blueprint, session, redirect, url_for, flash, request, jsonify
from flask_login import current_user
from app.models.product import Product  # Importiere das Produktmodell

# Blueprint für den Warenkorb erstellen
cart_bp = Blueprint('cart', __name__)

# Route zum Hinzufügen von Produkten zum Warenkorb
@cart_bp.route('/add_to_cart/<int:product_id>', methods=['GET', 'POST'])
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)

    if 'cart' not in session:
        session['cart'] = {}

    cart = session['cart']

    # Setze den `tax_rate` für das Produkt
    tax_rate = product.tax_rate if product.tax_rate else 0.0

    
    if 'cart_client_id' in session and session['cart_client_id'] != product.client_id:
        # Leere den Warenkorb und setze den Client ID neu
        session['cart'] = {}
        session['cart_client_id'] = product.client_id
        flash('Der Warenkorb wurde geleert, da Sie zu einem anderen Client gewechselt haben.', 'info')

    
    if 'cart_client_id' not in session:
        session['cart_client_id'] = product.client_id

    
    if str(product_id) in cart:
        cart[str(product_id)]['quantity'] += 1
    else:
        cart[str(product_id)] = {
            'quantity': 1,
            'name': product.name,
            'price': product.price,
            'image': product.image,
            'client_id': product.client_id,
            'tax_rate': tax_rate,  
            'is_must_popular': product.is_must_popular,
            'is_bestseller': product.is_bestseller
        }

    session['cart'] = cart
    flash(f"{product.name} erfolgreich zum Warenkorb hinzugefügt!", 'success')
    return redirect(request.referrer or url_for('frontend_bp.client_detail', client_id=product.client_id))


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


# Route zum Abrufen der Gesamtkosten des Warenkorbs
@cart_bp.route('/get_total_cost', methods=['GET'])
def get_total_cost():
    cart = session.get('cart', {})
    total_cost = 0.0  # Gesamtkosten der Artikel im Warenkorb (inkl. Steuer)
    total_tax = 0.0  # Gesamtsteuerbetrag

    # Berechne die Gesamtkosten und Steuern basierend auf dem Preis, der die Steuer enthält
    for product_id, item in cart.items():
        product = Product.query.get(product_id)
        if product:
            item_total = item['price'] * item['quantity']
            total_cost += item_total
            
            # Berechne den Steueranteil basierend auf dem Preis, der die Steuer enthält
            tax_rate = product.tax_rate if product.tax_rate is not None else 0.0
            # Steuer aus dem Gesamtpreis herausrechnen: (Preis * Steuerprozentsatz) / (100 + Steuerprozentsatz)
            tax = item_total * (tax_rate / (100 + tax_rate))
            total_tax += tax


        

    grand_total = total_cost  # Da der Steuerbetrag bereits im Preis enthalten ist

    return jsonify({
        "total_cost": total_cost,  # Gesamtkosten (inkl. Steuer)
        "tax": total_tax,  # Steueranteil aus dem Preis herausgerechnet
        "grand_total": grand_total  # Grand Total = Subtotal, da die Steuer schon enthalten ist

        

    })

