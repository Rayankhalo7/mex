import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from app import db
from app.models.product import Product
from app.models.category import Category
from app.models.client_model import Client

# Blueprint für Produkte definieren
client_product_bp = Blueprint('client_product_bp', __name__)

# Definiere den Basis-Upload-Ordner
UPLOAD_FOLDER_BASE = 'app/static/upload/client_produktbilder'

# Route zum Anzeigen aller Produkte
@client_product_bp.route('/products')
def view_products():
    if 'client_id' not in session:
        flash("Bitte loggen Sie sich ein.", "danger")
        return redirect(url_for('client_bp.login'))

    client = Client.query.get(session['client_id'])
    
    # Alle Produkte des Clients abfragen
    products = Product.query.filter_by(client_id=client.id).all()
    
    # Filtere die "Most Popular"-Produkte des Clients
    most_popular_products = Product.query.filter_by(client_id=client.id, is_must_popular=True).all()
    
    return render_template('product_list.html', products=products, most_popular_products=most_popular_products, client=client)


# Route zum Hinzufügen eines neuen Produkts
@client_product_bp.route('/product/add', methods=['GET', 'POST'])
def add_product():
    if 'client_id' not in session:
        flash("Bitte loggen Sie sich ein.", "danger")
        return redirect(url_for('client_bp.login'))

    client = Client.query.get(session['client_id'])
    categories = Category.query.filter_by(client_id=client.id).all()

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')
        category_id = request.form.get('category_id')
        image_file = request.files['image']
        is_must_popular = 'is_must_popular' in request.form  # Checkbox für "Must Popular"
        is_bestseller = 'is_bestseller' in request.form      # Checkbox für "Bestseller"
        tax_rate = request.form.get('tax_rate', 0.0)

        # Ordner für Client erstellen, falls nicht vorhanden
        client_folder = os.path.join(UPLOAD_FOLDER_BASE, str(client.id))
        if not os.path.exists(client_folder):
            os.makedirs(client_folder)

        # Speichern des Bildes im Client-Ordner
        filename = None
        if image_file and image_file.filename != '':
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(client_folder, filename)
            image_file.save(image_path)

        # Neues Produkt hinzufügen
        new_product = Product(
            name=name,
            description=description,
            price=price,
            image=filename,
            category_id=category_id,
            client_id=client.id,
            is_must_popular=is_must_popular,
            is_bestseller=is_bestseller,
            tax_rate=tax_rate
        )
        db.session.add(new_product)
        db.session.commit()
        flash('Produkt erfolgreich hinzugefügt.', 'success')
        return redirect(url_for('client_product_bp.view_products'))

    return render_template('add_product.html', categories=categories, client=client)


# Route zum Bearbeiten eines bestehenden Produkts
@client_product_bp.route('/product/edit/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    if 'client_id' not in session:
        flash("Bitte loggen Sie sich ein.", "danger")
        return redirect(url_for('client_bp.login'))

    client = Client.query.get(session['client_id'])
    product = Product.query.filter_by(id=id, client_id=client.id).first()
    categories = Category.query.filter_by(client_id=client.id).all()

    if not product:
        flash('Produkt nicht gefunden oder Zugriff verweigert.', 'danger')
        return redirect(url_for('client_product_bp.view_products'))

    if request.method == 'POST':
        product.name = request.form.get('name')
        product.description = request.form.get('description')
        product.price = request.form.get('price')
        product.category_id = request.form.get('category_id')
        product.is_must_popular = 'is_must_popular' in request.form
        product.is_bestseller = 'is_bestseller' in request.form
        product.tax_rate = float(request.form.get('tax_rate', 0.0))

        image_file = request.files['image']
        if image_file and image_file.filename != '':
            client_folder = os.path.join(UPLOAD_FOLDER_BASE, str(client.id))
            if not os.path.exists(client_folder):
                os.makedirs(client_folder)

            filename = secure_filename(image_file.filename)
            image_path = os.path.join(client_folder, filename)
            image_file.save(image_path)
            product.image = filename

        db.session.commit()
        flash('Produkt erfolgreich aktualisiert.', 'success')
        return redirect(url_for('client_product_bp.view_products'))

    return render_template('edit_product.html', product=product, categories=categories, client=client)


# Route zum Löschen eines Produkts
@client_product_bp.route('/product/delete/<int:id>', methods=['POST'])
def delete_product(id):
    if 'client_id' not in session:
        flash("Bitte loggen Sie sich ein.", "danger")
        return redirect(url_for('client_bp.login'))

    client = Client.query.get(session['client_id'])
    product = Product.query.filter_by(id=id, client_id=client.id).first()
    if product:
        # Lösche das Produktbild aus dem Client-Ordner, falls vorhanden
        if product.image:
            image_path = os.path.join(UPLOAD_FOLDER_BASE, str(client.id), product.image)
            if os.path.exists(image_path):
                os.remove(image_path)

        db.session.delete(product)
        db.session.commit()
        flash('Produkt erfolgreich gelöscht.', 'success')
    else:
        flash('Produkt nicht gefunden oder Zugriff verweigert.', 'danger')
    return redirect(url_for('client_product_bp.view_products'))


