from flask import Blueprint, jsonify, request, session, url_for, redirect
from app.models.order import Order
from app import db
from sqlalchemy import func
from datetime import datetime, timedelta

# Definiere den Blueprint für Statistiken
statistics_bp = Blueprint('statistics_bp', __name__)

@statistics_bp.route('/admin/statistics', methods=['GET'])
def show_statistics():
    # Sicherstellen, dass der Admin eingeloggt ist
    if "adminname" not in session:
        return redirect(url_for('admin_bp.login'))
    
    # Gesamtzahl der Bestellungen
    total_orders = db.session.query(func.count(Order.id)).scalar() or 0
    
    # Gesamteinnahmen
    total_revenue = db.session.query(func.sum(Order.total_amount)).scalar() or 0
    
    # Bestellungen und Einnahmen des letzten Monats
    one_month_ago = datetime.utcnow() - timedelta(days=30)
    last_month_orders = db.session.query(func.count(Order.id)).filter(Order.order_date >= one_month_ago).scalar() or 0
    last_month_revenue = db.session.query(func.sum(Order.total_amount)).filter(Order.order_date >= one_month_ago).scalar() or 0
    
    # Durchschnittlicher Bestellwert
    average_order_value = total_revenue / total_orders if total_orders > 0 else 0
    
    # Offene Bestellungen (nur Bestellungen mit Status 'pending')
    pending_orders = db.session.query(func.count(Order.id)).filter(Order.status == 'pending').scalar() or 0

    # Bestellungen der letzten 7 Tage
    today = datetime.utcnow()
    last_week = [today - timedelta(days=i) for i in range(6, -1, -1)]
    orders_per_day = {}
    for day in last_week:
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
        orders_count = db.session.query(func.count(Order.id)).filter(Order.order_date.between(day_start, day_end)).scalar() or 0
        orders_per_day[day.strftime('%A')] = orders_count
    
    # Bestellungen nach Status gruppieren
    status_counts = db.session.query(
        Order.status,
        func.count(Order.id)
    ).group_by(Order.status).all()
    
    order_status = {
        "pending": 0,
        "confirmed": 0,
        "delivered": 0,
        "canceled": 0
    }

    for status, count in status_counts:
        if status in order_status:
            order_status[status] = count

    # Alle Bestellungen für die Tabelle abrufen
    orders = Order.query.order_by(Order.order_date.desc()).all()
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
