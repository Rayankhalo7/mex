# app/routes/city.py
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from app import db
from app.models.category import Category
from app.models.client_model import Client

# Blueprint definieren
city_bp = Blueprint('city_bp', __name__)

# Route zum Anzeigen von Städte
@city_bp.route
