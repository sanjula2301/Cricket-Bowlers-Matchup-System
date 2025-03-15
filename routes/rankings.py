from flask import Blueprint, request, jsonify
from services.firebase_service import get_user

rankings_bp = Blueprint("rankings", __name__)

@rankings_bp.route('/get_rankings', methods=['GET'])
def get_rankings():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "User ID required"}), 400

    user_data = get_user(user_id)
    if not user_data:
        return jsonify({"error": "User not found"}), 404

    bowlers = user_data.get("bowlers", {})
    rankings = sorted(bowlers.items(), key=lambda x: x[1], reverse=True)

    return jsonify({"rankings": rankings})
