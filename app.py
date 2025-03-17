from flask import Flask, render_template, session, redirect, url_for, request, jsonify
from flask_cors import CORS
from flask_session import Session
from routes.auth import auth_bp
from routes.predictions import predictions_bp
from routes.comparison import comparison_bp
from routes.rankings import rankings_bp
from routes.overall_performance import overall_bp
import os

# Initialize Flask App
app = Flask(__name__, template_folder="templates")
app.secret_key = os.urandom(24)  # Secret key for session encryption

# Flask-Session Configuration
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True
app.config["SESSION_FILE_DIR"] = "./flask_session"

# Initialize Session
Session(app)
CORS(app, supports_credentials=True)  # Enable CORS with credentials

# Register Blueprints (Modular Routes)
app.register_blueprint(auth_bp)
app.register_blueprint(predictions_bp)
app.register_blueprint(comparison_bp)
app.register_blueprint(rankings_bp)
app.register_blueprint(overall_bp)

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/dashboard')
def dashboard_page():
    if "user_id" not in session:
        return redirect(url_for("login_page"))  # Redirect to login if not authenticated
    return render_template("dashboard.html")

@app.route('/logout')
def logout():
    session.pop("user_id", None)  # Remove user session
    return redirect(url_for("home"))  # Redirect to home page

@app.route('/prediction_result')
def prediction_result_page():
    return render_template("prediction_result.html")

@app.route('/prediction')
def prediction_page():
    if "user_id" not in session:
        return redirect(url_for("login_page"))  
    return render_template("prediction.html")

@app.route('/comparison')
def comparison_page():
    if "user_id" not in session:
        return redirect(url_for("login_page"))  
    return render_template("comparison.html")

@app.route('/signup')
def signup_page():
    return render_template("signup.html")

@app.route('/login')
def login_page():
    return render_template("login.html")

@app.route('/overall_performance')
def overall_performance():
    if "user_id" not in session:
        return redirect(url_for("login_page"))
    return render_template("overall_performance.html")

if __name__ == "__main__":
    app.run(debug=True)
