from app import create_app, db
from flask_migrate import Migrate
from flask import render_template

# Create the app using the factory function
app = create_app()


# Home-Route
@app.route("/")
def home():
    return render_template("frontend/home.html")

# Initialize Flask-Migrate
migrate = Migrate(app, db)

if __name__ == "__main__":
    with app.app_context():
        # Ensure the database tables are created
        db.create_all()
    app.run(debug=True)
