from flask import Blueprint, request, jsonify
from firebase_admin import auth
from services.firebase_service import get_user

auth_bp = Blueprint("auth", __name__)

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.json
    try:
        user = auth.create_user(email=data["email"], password=data["password"], display_name=data["username"])
        return jsonify({"message": "User created successfully", "user_id": user.uid})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    try:
        user = auth.get_user_by_email(data["email"])
        return jsonify({"user_id": user.uid})
    except Exception as e:
        return jsonify({"error": "Invalid credentials"}), 400

@auth_bp.route('/get-user', methods=['GET'])
def get_user_details():
    user_id = request.args.get("user_id")
    user = get_user(user_id)
    return jsonify(user) if user else jsonify({"error": "User not found"}), 404
