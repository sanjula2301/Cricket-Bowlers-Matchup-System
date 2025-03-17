from flask import Blueprint, request, jsonify,render_template
from services.firebase_service import db

overall_bp = Blueprint("overall_performance", __name__)

# ✅ Fetch Overall DPPI Scores for All Bowlers
@overall_bp.route('/get_overall_dppi', methods=['GET'])
def get_overall_dppi():
    """Fetches total DPPI scores across all match phases for a user."""
    user_id = request.args.get("user_id")
    
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    try:
        sessions = db.collection("users").document(user_id).collection("session_data").stream()
        bowler_scores = {}

        for session in sessions:
            bowler_entries = session.reference.collection("bowler_entries").stream()
            for entry in bowler_entries:
                entry_data = entry.to_dict()
                bowler_name = entry_data.get("bowler_name", "")
                dppi_score = float(entry_data.get("dppi_score", 0))

                if bowler_name in bowler_scores:
                    bowler_scores[bowler_name] += dppi_score
                else:
                    bowler_scores[bowler_name] = dppi_score

        sorted_scores = sorted(bowler_scores.items(), key=lambda x: x[1], reverse=True)

        return jsonify([{"name": bowler, "total_dppi": score} for bowler, score in sorted_scores])

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Fetch Overall Performance Page
@overall_bp.route('/overall_performance')
def overall_performance():
    """Renders the overall performance page."""
    return jsonify({"message": "Overall performance page"}), 200
