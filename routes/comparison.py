from flask import Blueprint, request, jsonify
from services.firebase_service import db

comparison_bp = Blueprint("comparison", __name__)

@comparison_bp.route('/compare_bowlers', methods=['POST'])
def compare():
    data = request.json
    user_id = data.get("user_id")
    bowler1 = data.get("bowler1")
    bowler2 = data.get("bowler2")

    if not user_id or not bowler1 or not bowler2:
        return jsonify({"error": "Missing required fields"}), 400

    # Fetch bowler data from Firestore
    try:
        # Fetch bowler1 data
        bowler1_data = fetch_bowler_data(user_id, bowler1)
        if not bowler1_data:
            return jsonify({"error": f"Data for {bowler1} not found"}), 404

        # Fetch bowler2 data
        bowler2_data = fetch_bowler_data(user_id, bowler2)
        if not bowler2_data:
            return jsonify({"error": f"Data for {bowler2} not found"}), 404

        # Compare bowlers
        winner = bowler1 if bowler1_data["total_dppi_score"] > bowler2_data["total_dppi_score"] else bowler2
        return jsonify({
            "winner": winner,
            "bowler1": bowler1_data,
            "bowler2": bowler2_data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@comparison_bp.route('/get_single_bowler_performance', methods=['GET'])
def get_single_bowler_performance():
    user_id = request.args.get("user_id")
    bowler_name = request.args.get("bowler_name")

    if not user_id or not bowler_name:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        bowler_data = fetch_bowler_data(user_id, bowler_name)
        if not bowler_data:
            return jsonify({"error": f"Data for {bowler_name} not found"}), 404
        return jsonify(bowler_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def fetch_bowler_data(user_id, bowler_name):
    """Fetch bowler data from Firestore."""
    sessions = db.collection("users").document(user_id).collection("session_data").stream()
    bowler_data = {
        "total_dppi_score": 0,
        "powerplay_dppi": 0,
        "middle_overs_dppi": 0,
        "death_overs_dppi": 0
    }

    # Track unique sessions to avoid duplicate entries
    processed_sessions = set()

    for session in sessions:
        session_id = session.id
        if session_id in processed_sessions:
            continue  # Skip already processed sessions
        processed_sessions.add(session_id)

        # Fetch bowler entries for the current session
        bowler_entries = session.reference.collection("bowler_entries").where("bowler_name", "==", bowler_name).stream()
        for entry in bowler_entries:
            entry_data = entry.to_dict()
            bowler_data["total_dppi_score"] += entry_data.get("dppi_score", 0)
            if entry_data.get("phase") == "Powerplay":
                bowler_data["powerplay_dppi"] += entry_data.get("dppi_score", 0)
            elif entry_data.get("phase") == "MiddleOvers":
                bowler_data["middle_overs_dppi"] += entry_data.get("dppi_score", 0)
            elif entry_data.get("phase") == "DeathOvers":
                bowler_data["death_overs_dppi"] += entry_data.get("dppi_score", 0)

    return bowler_data



@comparison_bp.route('/get_bowlers_by_phase', methods=['GET'])
def get_bowlers_by_phase():
    user_id = request.args.get("user_id")
    phase = request.args.get("phase")

    if not user_id or not phase:
        return jsonify({"error": "Missing user_id or phase"}), 400

    try:
        sessions = db.collection("users").document(user_id).collection("session_data").stream()
        bowlers = set()

        for session in sessions:
            bowler_entries = session.reference.collection("bowler_entries").where("phase", "==", phase).stream()
            for entry in bowler_entries:
                entry_data = entry.to_dict()
                bowlers.add(entry_data.get("bowler_name", ""))

        return jsonify([{"name": bowler} for bowler in bowlers])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@comparison_bp.route('/get_overall_dppi', methods=['GET'])
def get_overall_dppi():
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
