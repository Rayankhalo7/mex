from flask import Blueprint, jsonify, request, session, url_for, redirect
from app.models.order import Order
from app.models.client_model import Client  # Stellen Sie sicher, dass das Client-Modell importiert ist
from app import db
from sqlalchemy import func
from datetime import datetime, timedelta

# Definiere den Blueprint für Client-Statistiken
client_statistics_bp = Blueprint('client_statistics_bp', __name__)

@client_statistics_bp.route('/client/statistics', methods=['GET'])
def show_client_statistics():
    # Sicherstellen, dass der Client eingeloggt ist
    if "clientname" not in session:
        return redirect(url_for('client_bp.login'))
    
    client = Client.query.get(session['client_id'])

    # Gesamtzahl der Bestellungen des Clients
    total_orders = db.session.query(func.count(Order.id)).filter(Order.client_id == client.id).scalar() or 0
    
    # Gesamteinnahmen des Clients
    total_revenue = db.session.query(func.sum(Order.total_amount)).filter(Order.client_id == client.id).scalar() or 0
    
    # Bestellungen und Einnahmen des letzten Monats des Clients
    one_month_ago = datetime.utcnow() - timedelta(days=30)
    last_month_orders = db.session.query(func.count(Order.id)).filter(Order.client_id == client.id, Order.order_date >= one_month_ago).scalar() or 0
    last_month_revenue = db.session.query(func.sum(Order.total_amount)).filter(Order.client_id == client.id, Order.order_date >= one_month_ago).scalar() or 0
    
    # Durchschnittlicher Bestellwert des Clients
    average_order_value = total_revenue / total_orders if total_orders > 0 else 0
    
    # Offene Bestellungen (nur Bestellungen mit Status 'pending' des Clients)
    pending_orders = db.session.query(func.count(Order.id)).filter(Order.client_id == client.id, Order.status == 'pending').scalar() or 0

    # Bestellungen der letzten 7 Tage des Clients
    today = datetime.utcnow()
    last_week = [today - timedelta(days=i) for i in range(6, -1, -1)]
    orders_per_day = {}
    for day in last_week:
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
        orders_count = db.session.query(func.count(Order.id)).filter(
            Order.client_id == client.id,
            Order.order_date.between(day_start, day_end)
        ).scalar() or 0
        orders_per_day[day.strftime('%A')] = orders_count
    
    # Bestellungen nach Status gruppieren für den Client
    status_counts = db.session.query(
        Order.status,
        func.count(Order.id)
    ).filter(Order.client_id == client.id).group_by(Order.status).all()
    
    order_status = {
        "pending": 0,
        "confirmed": 0,
        "delivered": 0,
        "canceled": 0
    }

    for status, count in status_counts:
        if status in order_status:
            order_status[status] = count

    # Alle Bestellungen des Clients für die Tabelle abrufen
    orders = Order.query.filter_by(client_id=client.id).order_by(Order.order_date.desc()).all()
    orders_list = [
        {
            "order_number": order.order_number,
            "order_date": order.order_date.isoformat(),
            "status": order.status,
            "total_amount": order.total_amount
        }
        for order in orders
    ]

    # JSON-Antwort
    return jsonify({
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "last_month_orders": last_month_orders,
        "last_month_revenue": last_month_revenue,
        "average_order_value": round(average_order_value, 2),
        "pending_orders": pending_orders,
        "orders_per_day": orders_per_day,
        "order_status": order_status,
        "orders": orders_list
    })
