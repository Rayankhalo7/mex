from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def hello():
    return render_template('index.html')  # Nur den Dateinamen übergeben, kein Pfad!

if __name__ == '__main__':
    app.run(debug=True)
