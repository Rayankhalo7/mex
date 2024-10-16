# app/routes/paypal_sandbox.py
from flask import Blueprint, request, redirect, url_for, session, flash  # session hier importiert
from paypalrestsdk import Payment
from app.models.order import Order
from app import db
import paypalrestsdk
import os
from flask_login import current_user

# Blueprint für PayPal Sandbox
paypal_sandbox_bp = Blueprint('paypal_sandbox_bp', __name__)

# PayPal SDK konfigurieren
paypalrestsdk.configure({
    "mode": "sandbox",  # Verwende den Sandbox-Modus
    "client_id": os.getenv("PAYPAL_CLIENT_ID"),
    "client_secret": os.getenv("PAYPAL_CLIENT_SECRET")
})

@paypal_sandbox_bp.route('/paypal/checkout/<int:order_id>', methods=['GET'])
def checkout(order_id):
    # Sicherstellen, dass der Benutzer eingeloggt ist
    if not current_user.is_authenticated:
        return redirect(url_for('user_bp.login'))

    # Lade die Bestellung basierend auf der order_id
    order = Order.query.get_or_404(order_id)

    # Überprüfe, ob die Bestellung bereits bestätigt wurde
    if order.status != 'pending':
        flash('Diese Bestellung wurde bereits verarbeitet.', 'warning')
        return redirect(url_for('frontend_bp.home'))

    # Erstelle eine neue PayPal-Zahlung
    payment = Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"
        },
        "redirect_urls": {
            "return_url": url_for('paypal_sandbox_bp.payment_success', _external=True, order_id=order.id),
            "cancel_url": url_for('paypal_sandbox_bp.payment_cancel', _external=True)
        },
        "transactions": [{
            "item_list": {
                "items": [{
                    "name": f"Bestellung Nr. {order.order_number}",
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
            "description": f"Zahlung für Bestellung Nr. {order.order_number}"
        }]
    })

    if payment.create():
        for link in payment.links:
            if link.rel == "approval_url":
                approval_url = str(link.href)
                return redirect(approval_url)
    else:
        error_message = payment.error.get('message', 'Unbekannter Fehler')
        flash(f'Fehler bei der Erstellung der Zahlung: {error_message}', 'danger')
        return redirect(url_for('checkout_bp.checkout'))

@paypal_sandbox_bp.route('/paypal/payment_success', methods=['GET'])
def payment_success():
    payment_id = request.args.get('paymentId')
    payer_id = request.args.get('PayerID')
    order_id = request.args.get('order_id')

    if payment_id and payer_id:
        # Finde das Zahlung-Objekt von PayPal
        payment = Payment.find(payment_id)

        if payment.execute({"payer_id": payer_id}):
            # Bestellung basierend auf der order_id abrufen
            order = Order.query.get(order_id)

            if not order:
                flash('Bestellung konnte nicht gefunden werden.', 'danger')
                return redirect(url_for('checkout_bp.checkout'))

            # Bestellung aktualisieren
            order.status = 'confirmed'
            order.payment_type = 'PayPal'
            order.payment_method = 'Online'
            order.transaction_id = payment.id
            db.session.commit()

            # Warenkorb leeren
            session.pop('cart', None)
            session.pop('cart_client_id', None)
            session.pop('tax_details', None)

            flash('Zahlung erfolgreich abgeschlossen!', 'success')
            return redirect(url_for('frontend_bp.thank_you'))
        else:
            error_message = payment.error.get('message', 'Unbekannter Fehler')
            flash(f'Zahlung konnte nicht abgeschlossen werden: {error_message}', 'danger')
    else:
        flash('Zahlung konnte nicht verarbeitet werden.', 'danger')

    return redirect(url_for('checkout_bp.checkout'))

@paypal_sandbox_bp.route('/paypal/payment_cancel', methods=['GET'])
def payment_cancel():
    flash('Zahlung wurde abgebrochen.', 'warning')
    return redirect(url_for('checkout_bp.checkout'))
