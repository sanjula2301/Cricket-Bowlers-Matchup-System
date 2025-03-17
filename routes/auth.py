from flask import Blueprint, request, jsonify, session
from firebase_admin import auth
from services.firebase_service import get_user
from services.firebase_service import store_prediction

auth_bp = Blueprint("auth", __name__)

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.json
    print("Received Signup Data:", data)  # Debugging print
    try:
        user = auth.create_user(email=data["email"], password=data["password"], display_name=data["username"])
        return jsonify({"message": "User created successfully", "user_id": user.uid})
    except Exception as e:
        print("Signup Error:", str(e))  # Print the error message
        return jsonify({"error": str(e)}), 400

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    print("Received Login Data:", data)  # Debugging print
    try:
        user = auth.get_user_by_email(data["email"])
        session["user_id"] = user.uid  # Store user ID in session
        return jsonify({"user_id": user.uid})
    except Exception as e:
        print("Login Error:", str(e))  # Print the error message
        return jsonify({"error": "Invalid credentials"}), 400

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.pop("user_id", None)  # Remove user session
    return jsonify({"message": "Logged out successfully"}), 200

@auth_bp.route('/get-user', methods=['GET'])
def get_user_details():
    """Fetch user details from Firestore."""
    user_id = request.args.get("user_id")

    if not user_id:
        return jsonify({"error": "Missing user_id parameter"}), 400

    user_data = get_user(user_id)

    if user_data:
        return jsonify({"username": user_data.get("username", "Unknown")})
    else:
        return jsonify({"error": "User not found"}), 404
