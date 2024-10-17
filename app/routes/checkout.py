from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from paypalrestsdk import Payment
from app.models.client_model import Client
from app.routes.add_to_cart import get_total_cost
from app.models.order import Order
from app.models.order_item import OrderItem
from app import db
import paypalrestsdk
from datetime import datetime
import os
from app.routes.forms import PaymentForm  # Importieren Sie das Formular korrekt

# Blueprint für Checkout erstellen
checkout_bp = Blueprint('checkout_bp', __name__, template_folder='templates/frontend')

# PayPal SDK konfigurieren
paypalrestsdk.configure({
    "mode": "sandbox",  # Verwende den Sandbox-Modus
    "client_id": os.getenv("PAYPAL_CLIENT_ID"),
    "client_secret": os.getenv("PAYPAL_CLIENT_SECRET")
})




@checkout_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart = session.get('cart', {})
    if not cart:
        flash('Ihr Warenkorb ist leer. Fügen Sie zuerst Produkte hinzu.', 'warning')
        return redirect(url_for('frontend_bp.home'))

    response = get_total_cost()
    data = response.json

    total_cost = data.get('total_cost', 0)
    total_tax = data.get('tax', 0)
    grand_total = data.get('grand_total', 0)
    tax_details = data.get('tax_details', {})
    total_items = data.get('total_items', 0)

    client_id = session.get('cart_client_id')
    client = Client.query.get(client_id) if client_id else None

    if not client:
        flash('Kein Client zugeordnet. Bitte wähle einen gültigen Client.', 'warning')
        return redirect(url_for('frontend_bp.home'))

    current_time = datetime.now()

    # Separate Formularinstanzen erstellen
    cash_form = PaymentForm()
    paypal_form = PaymentForm()

    return render_template('frontend/checkout.html',
                           cart=cart,
                           total_cost=total_cost,
                           total_tax=total_tax,
                           grand_total=grand_total,
                           tax_details=tax_details,
                           total_items=total_items,
                           client=client,
                           current_time=current_time,
                           cash_form=cash_form,
                           paypal_form=paypal_form)

@checkout_bp.route('/process_checkout', methods=['POST'])
@login_required
def process_checkout():
    form = PaymentForm()
    if not form.validate_on_submit():
        flash('Ungültige Formularübermittlung. Bitte versuchen Sie es erneut.', 'danger')
        return redirect(url_for('checkout_bp.checkout'))

    payment_type = request.form.get('payment_type')
    if payment_type not in ['cash', 'paypal']:
        flash('Ungültige Zahlungsart.', 'danger')
        return redirect(url_for('checkout_bp.checkout'))

    # Warenkorb aus der Session abrufen
    cart = session.get('cart', {})
    if not cart:
        flash('Ihr Warenkorb ist leer. Fügen Sie zuerst Produkte hinzu.', 'warning')
        return redirect(url_for('frontend_bp.home'))

    response = get_total_cost()
    data = response.json
    total_cost = data.get('total_cost', 0)
    total_tax = data.get('tax', 0)
    grand_total = data.get('grand_total', 0)

    client_id = session.get('cart_client_id')
    client = Client.query.get(client_id) if client_id else None

    if not client:
        flash('Kein Client zugeordnet. Bitte wähle einen gültigen Client.', 'warning')
        return redirect(url_for('frontend_bp.home'))

    if not (current_user.street and current_user.house_number and current_user.postal_code and current_user.city):
        flash("Bitte geben Sie eine vollständige Adresse an, um fortzufahren.", "warning")
        return redirect(url_for('checkout_bp.checkout'))

    phone = current_user.phone_number

    # Erstelle die Bestellung
    order = Order(
        user_id=current_user.id,
        client_id=client.id,
        name=current_user.username,
        email=current_user.email,
        phone=phone,
        address=f"{current_user.street} {current_user.house_number}, {current_user.postal_code} {current_user.city}",
        payment_method=payment_type,
        amount=total_cost,
        total_amount=grand_total,
        status='pending',
        currency='EUR'
    )
    db.session.add(order)
    db.session.commit()  # Nach dem Commit wird order.id generiert

    # Bestellartikel hinzufügen
    for product_id, item in cart.items():
        if product_id != 'client_id':
            product_id_int = int(product_id)  # Konvertieren Sie product_id in Integer
            order_item = OrderItem(
                order_id=order.id,
                product_id=product_id_int,
                client_id=client.id,
                quantity=item['quantity'],
                price=item['price']
            )
            db.session.add(order_item)

    db.session.commit()
    # Setzen der Session-Daten für die "thank_you" Seite
    session['thank_you_cart_client_id'] = client.id
    session['thank_you_cart'] = cart

    # Falls PayPal als Zahlungsart gewählt wurde
    if payment_type == 'paypal':
        return redirect(url_for('checkout_bp.paypal_checkout', order_id=order.id))

    # Barzahlung
    order.status = 'confirmed'
    db.session.commit()

    # Warenkorb leeren
    session.pop('cart', None)
    session.pop('cart_client_id', None)
    session.pop('tax_details', None)

    flash('Bestellung erfolgreich abgeschlossen!', 'success')
    return redirect(url_for('frontend_bp.thank_you'))

@checkout_bp.route('/paypal/checkout/<int:order_id>', methods=['GET'])
@login_required
def paypal_checkout(order_id):
    order = Order.query.get_or_404(order_id)

    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"
        },
        "redirect_urls": {
            "return_url": url_for('checkout_bp.payment_success', _external=True),
            "cancel_url": url_for('checkout_bp.payment_cancel', _external=True)
        },
        "transactions": [{
            "item_list": {
                "items": [{
                    "name": f"Bestellung Nr. {order.id}",
                    "sku": "item",
                    "price": f"{order.total_amount:.2f}",
                    "currency": order.currency,
                    "quantity": 1
                }]
            },
            "amount": {
                "total": f"{order.total_amount:.2f}",
                "currency": order.currency
            },
            "description": f"Zahlung für Bestellung Nr. {order.id}"
        }]
    })

    if payment.create():
        # Speichern des order_id in der Sitzung
        session['paypal_order_id'] = order.id
        for link in payment.links:
            if link.rel == "approval_url":
                approval_url = str(link.href)
                return redirect(approval_url)
    else:
        error_message = payment.error.get('message', 'Unbekannter Fehler') if payment.error else 'Unbekannter Fehler'
        flash(f'Fehler bei der Erstellung der Zahlung: {error_message}', 'danger')
        return redirect(url_for('checkout_bp.checkout'))

@checkout_bp.route('/payment_success', methods=['GET'])
@login_required
def payment_success():
    payment_id = request.args.get('paymentId')
    payer_id = request.args.get('PayerID')
    order_id = session.get('paypal_order_id')

    if payment_id and payer_id and order_id:
        payment = Payment.find(payment_id)

        if payment.execute({"payer_id": payer_id}):
            order = Order.query.get(order_id)

            if not order:
                flash('Bestellung konnte nicht gefunden werden.', 'danger')
                return redirect(url_for('checkout_bp.checkout'))

            order.status = 'confirmed'
            order.payment_method = 'PayPal'
            order.transaction_id = payment.id
            db.session.commit()

            # Warenkorb und paypal_order_id aus der Sitzung löschen
            session.pop('cart', None)
            session.pop('cart_client_id', None)
            session.pop('tax_details', None)
            session.pop('paypal_order_id', None)

            flash('Zahlung erfolgreich abgeschlossen!', 'success')
            return redirect(url_for('frontend_bp.thank_you'))
        else:
            error_message = payment.error.get('message', 'Unbekannter Fehler') if payment.error else 'Unbekannter Fehler'
            flash(f'Zahlung konnte nicht abgeschlossen werden: {error_message}', 'danger')
    else:
        flash('Zahlung konnte nicht verarbeitet werden.', 'danger')

    return redirect(url_for('checkout_bp.checkout'))

@checkout_bp.route('/payment_cancel', methods=['GET'])
@login_required
def payment_cancel():
    # Löschen des order_id aus der Sitzung, wenn die Zahlung abgebrochen wird
    session.pop('paypal_order_id', None)
    flash('Zahlung wurde abgebrochen.', 'warning')
    return redirect(url_for('checkout_bp.checkout'))



@checkout_bp.route('/cart/increase_quantity/<int:product_id>', methods=['POST'])
@login_required
def increase_quantity(product_id):
    cart = session.get('cart', {})
    if str(product_id) in cart:
        cart[str(product_id)]['quantity'] += 1
        session['cart'] = cart
        return jsonify({'status': 'success', 'quantity': cart[str(product_id)]['quantity']})
    return jsonify({'status': 'error', 'message': 'Produkt nicht gefunden'}), 404

@checkout_bp.route('/cart/decrease_quantity/<int:product_id>', methods=['POST'])
@login_required
def decrease_quantity(product_id):
    cart = session.get('cart', {})
    if str(product_id) in cart:
        if cart[str(product_id)]['quantity'] > 1:
            cart[str(product_id)]['quantity'] -= 1
            session['cart'] = cart
            return jsonify({'status': 'success', 'quantity': cart[str(product_id)]['quantity']})
        else:
            return jsonify({'status': 'error', 'message': 'Menge kann nicht weiter verringert werden'}), 400
    return jsonify({'status': 'error', 'message': 'Produkt nicht gefunden'}), 404

@checkout_bp.route('/cart/remove_from_cart/<int:product_id>', methods=['POST'])
@login_required
def remove_from_cart(product_id):
    cart = session.get('cart', {})
    if str(product_id) in cart:
        del cart[str(product_id)]
        session['cart'] = cart
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Produkt nicht gefunden'}), 404