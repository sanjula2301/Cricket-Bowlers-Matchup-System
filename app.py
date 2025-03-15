from flask import Flask,render_template
from flask_cors import CORS
from routes.auth import auth_bp
from routes.predictions import predictions_bp
from routes.comparison import comparison_bp
from routes.rankings import rankings_bp

# Initialize Flask App
app = Flask(__name__, template_folder="templates")
CORS(app)

# Register Blueprints (Modular Routes)
app.register_blueprint(auth_bp)
app.register_blueprint(predictions_bp)
app.register_blueprint(comparison_bp)
app.register_blueprint(rankings_bp)

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/prediction_result')
def prediction_result_page():
    return render_template("prediction_result.html")

# Serve other HTML pages
@app.route('/prediction')
def prediction_page():
    return render_template("prediction.html")

@app.route('/comparison')
def comparison_page():
    return render_template("comparison.html")

@app.route('/signup')
def signup_page():
    return render_template("signup.html")

@app.route('/login')
def login_page():
    return render_template("login.html")

if __name__ == "__main__":
    app.run(debug=True)