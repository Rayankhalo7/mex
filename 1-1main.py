
@@ -1,10 +1,10 @@
from flask import Flask, render_template
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return render_template('index.html')  # Nur den Dateinamen übergeben, kein Pfad!
def hello_world():
    return 'Hello, World!'

if __name__ == '__main__':
1    app.run(debug=True)
if __name__ == "__main__":
    app.run(debug=True)