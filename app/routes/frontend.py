# app/routes/frontend.py

from flask import Blueprint, render_template, redirect, url_for, request, abort, session, flash
from app.models.client_model import Client
from app.models.user_model import User
from app import db
from flask_login import current_user
from app.models.banner import Banner
from app.models.rating import Rating
from app.models.lieferzeiten import Lieferzeiten
from datetime import datetime
from app.models.product import Product
from app.models.client_model import Client

# Blueprint für das Frontend erstellen
frontend_bp = Blueprint('frontend_bp', __name__, template_folder='templates/frontend')

def calculate_total_cost_and_tax(cart):
    """
    Berechnet die Gesamtkosten, Steuern und Details für den Warenkorb.
    """
    total_cost = 0.0
    total_tax = 0.0
    tax_details = {}

    for item in cart.values():
        item_cost = item['price'] * item['quantity']
        total_cost += item_cost

        if item.get('tax_rate'):
            tax_rate = item['tax_rate']
            # Berechne die Steuer für dieses Produkt
            item_tax = item_cost * (tax_rate / (100 + tax_rate))
            total_tax += item_tax

            # Steuersatz in die Steuerdetails aufnehmen
            if tax_rate in tax_details:
                tax_details[tax_rate] += item_tax
            else:
                tax_details[tax_rate] = item_tax

    return total_cost, total_tax, tax_details

# Route für die Startseite
@frontend_bp.route('/')
def home():
    # Alle Clients aus der Datenbank abrufen
    clients = Client.query.all()
    if not clients:
        return render_template('frontend/no_clients.html')  # Falls keine Clients vorhanden sind, andere Seite anzeigen

    return render_template('frontend/home.html', clients=clients)

# Route für die Client-Detailseite
@frontend_bp.route('/client/<int:client_id>')
def client_detail(client_id):
    client = Client.query.get_or_404(client_id)

    # Überprüfe, ob ein Warenkorb existiert und ob er zu einem anderen Client gehört
    if 'cart_client_id' in session and session['cart_client_id'] != client_id:
        session.pop('cart', None)
        session.pop('cart_client_id', None)
        flash('Der Warenkorb wurde geleert, da Sie zu einem anderen Client gewechselt haben.', 'info')

    if 'cart_client_id' not in session:
        session['cart_client_id'] = client_id

    ratings = client.ratings if hasattr(client, 'ratings') else []
    total_ratings = len(ratings)
    average_rating = round(sum(rating.rating for rating in ratings) / total_ratings, 1) if total_ratings > 0 else 0
    opening_hours = client.opening_hours if hasattr(client, 'opening_hours') else []
    lieferzeiten = client.lieferzeiten if hasattr(client, 'lieferzeiten') else []
    categories = client.categories if hasattr(client, 'categories') else []
    user = current_user if current_user.is_authenticated else None
    banner = Banner.query.filter_by(client_id=client.id).first()
    total_reviews = sum(1 for rating in ratings if rating.comment)
    current_time = datetime.now()
    most_popular_products = Product.query.filter_by(client_id=client.id, is_must_popular=True).all()
    bestseller_products = Product.query.filter_by(client_id=client.id, is_bestseller=True).all()

    cart = session.get('cart', {})
    total_cost, total_tax, tax_details = calculate_total_cost_and_tax(cart)

    return render_template(
        'frontend/client_detail.html',
        client=client,
        ratings=ratings,
        opening_hours=opening_hours,
        user=user,
        banner=banner,
        categories=categories,
        current_time=current_time,
        total_ratings=total_ratings,
        average_rating=average_rating,
        total_reviews=total_reviews,
        lieferzeiten=lieferzeiten,
        most_popular_products=most_popular_products, 
        bestseller_products=bestseller_products,
        cart=cart,
        total_cost=total_cost,
        total_tax=total_tax,
        tax_details=tax_details  # Übergabe der Steuerdetails an das Template
    )


@frontend_bp.route('/thank_you')
def thank_you():
    # Client-ID aus der Session holen
    client_id = session.get('thank_you_cart_client_id')
    client = Client.query.get(client_id) if client_id else None

    if not client:
        #flash('Kein Client zugeordnet. Bitte wähle einen gültigen Client.', 'warning')
        return redirect(url_for('frontend_bp.home'))

    cart = session.get('thank_you_cart', {})

    if not cart:
        flash('Dein Warenkorb ist leer.', 'warning')
        return redirect(url_for('frontend_bp.home'))

    # Berechne die Gesamtkosten, Steuern und Steuerdetails
    total_cost = 0.0
    total_tax = 0.0
    tax_details = {}
    
    if cart:
        total_cost, total_tax, tax_details = calculate_total_cost_and_tax(cart)

    # Session-Daten nach der Bestätigung löschen
    session.pop('thank_you_cart_client_id', None)
    session.pop('thank_you_cart', None)

    return render_template('frontend/thank_you.html', client=client, cart=cart, total_cost=total_cost, total_tax=total_tax, tax_details=tax_details)


 
    



