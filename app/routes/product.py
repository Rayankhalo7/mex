from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from app import db
from app.models.product import Product
from app.models.category import Category
from app.models.client_model import Client

# Blueprint für Produkte definieren
client_product_bp = Blueprint('client_product_bp', __name__)

# Route zum Anzeigen aller Produkte
@client_product_bp.route('/products')
def view_products():
    if 'client_id' not in session:
        flash("Bitte loggen Sie sich ein.", "danger")
        return redirect(url_for('client_bp.login'))

    client = Client.query.get(session['client_id'])
    products = Product.query.filter_by(client_id=client.id).all()
    return render_template('product_list.html', products=products, client=client)

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
        category_id = request.form.get('category_id')  # Kategorie-ID aus dem Formular holen

        print("Gewählte Kategorie-ID:", category_id)  # Debugging-Ausgabe

        # Überprüfe, ob die Kategorie zur aktuellen Client-ID gehört
        category = Category.query.filter_by(id=category_id, client_id=client.id).first()
        if not category:
            flash('Ungültige Kategorie ausgewählt. Bitte wählen Sie eine gültige Kategorie aus.', 'danger')
            return redirect(url_for('client_product_bp.add_product'))

        # Neues Produkt hinzufügen
        if name and category_id:
            new_product = Product(
                name=name,
                description=description,
                price=price,
                category_id=category.id,
                client_id=client.id
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

        print("Gewählte Kategorie-ID:", product.category_id)  # Debugging-Ausgabe

        # Überprüfe, ob die Kategorie zur aktuellen Client-ID gehört
        category = Category.query.filter_by(id=product.category_id, client_id=client.id).first()
        if not category:
            flash('Ungültige Kategorie ausgewählt. Bitte wählen Sie eine gültige Kategorie aus.', 'danger')
            return redirect(url_for('client_product_bp.edit_product', id=id))

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
        db.session.delete(product)
        db.session.commit()
        flash('Produkt erfolgreich gelöscht.', 'success')
    else:
        flash('Produkt nicht gefunden oder Zugriff verweigert.', 'danger')
    return redirect(url_for('client_product_bp.view_products'))
