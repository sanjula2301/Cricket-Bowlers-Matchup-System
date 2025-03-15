from flask import Blueprint, request, jsonify
from services.prediction_service import predict_bowler
from services.firebase_service import db
import datetime
import uuid

predictions_bp = Blueprint("predictions", __name__)

@predictions_bp.route('/predict', methods=['POST'])
def predict():
    data = request.json
    phase = data.get("phase")
    
    if not phase:
        return jsonify({"error": "Missing phase"}), 400
    
    result = predict_bowler(phase, data)
    return jsonify(result)

@predictions_bp.route('/store_prediction', methods=['POST'])
def store_bowler_prediction():
    """Stores bowler prediction data in Firestore."""
    data = request.json
    print(" Incoming Data for Store Prediction:", data)  #  Debugging Log

    # Validate and enforce data types
    user_id = str(data.get("user_id", "")).strip()
    bowler_name = str(data.get("bowler_name", "")).strip()
    phase = str(data.get("phase", "")).strip()
    predicted_cluster = int(data.get("predicted_cluster", -1))
    dppi_score = float(data.get("dppi_score", -1))
    feature_importance = data.get("feature_importance", [])

    if not user_id or not bowler_name or not phase or predicted_cluster == -1 or dppi_score == -1:
        print(" Missing required fields!")
        return jsonify({"error": "Missing required fields"}), 400

    # Remove duplicate features
    unique_feature_importance = []
    seen_features = set()
    for feature in feature_importance:
        if isinstance(feature, dict) and "Feature" in feature:
            if feature["Feature"] not in seen_features:
                unique_feature_importance.append(feature)
                seen_features.add(feature["Feature"])

    # Get today's session
    today = datetime.datetime.utcnow().date()
    user_sessions = db.collection("users").document(user_id).collection("session_data").stream()

    existing_session_id = None
    for session in user_sessions:
        session_data = session.to_dict()
        session_date = session_data.get("created_at", None)
        if session_date and session_date.date() == today:
            existing_session_id = session.id
            break

    # Create new session if needed
    if not existing_session_id:
        session_id = str(uuid.uuid4())
        session_ref = db.collection("users").document(user_id).collection("session_data").document(session_id)
        session_ref.set({"created_at": datetime.datetime.utcnow()})
        print(f"New session created: {session_id}")
    else:
        session_id = existing_session_id
        session_ref = db.collection("users").document(user_id).collection("session_data").document(session_id)
        print(f"Using existing session: {session_id}")

    #  Check if bowler already exists
    bowler_entries = session_ref.collection("bowler_entries").where("bowler_name", "==", bowler_name).stream()
    existing_bowler_id = None
    for entry in bowler_entries:
        existing_bowler_id = entry.id
        break

    # Store bowler entry
    bowler_entry = {
        "bowler_name": bowler_name,
        "phase": phase,
        "predicted_cluster": predicted_cluster,
        "dppi_score": dppi_score,
        "feature_importance": unique_feature_importance,
        "created_at": datetime.datetime.utcnow()
    }

    if existing_bowler_id:
        # Update existing entry
        session_ref.collection("bowler_entries").document(existing_bowler_id).update(bowler_entry)
        print(f"🔄 Updated bowler entry: {bowler_name} in session {session_id}")
        message = "Bowler data updated successfully"
    else:
        # Add new bowler entry
        bowler_ref = session_ref.collection("bowler_entries").document()  # Generates a unique ID
        bowler_ref.set(bowler_entry)
        print(f"New bowler entry stored: {bowler_name} in session {session_id}")
        message = "Bowler data stored successfully"

    return jsonify({"message": message, "session_id": session_id})

@predictions_bp.route('/get_predictions', methods=['GET'])
def get_predictions():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id parameter is required"}), 400

    # Sanitize the user_id by stripping whitespace and newline characters
    user_id = user_id.strip()

    print(f"Fetching predictions for user: {user_id}")

    try:
        # Check if the user exists in Firestore
        user_ref = db.collection("users").document(user_id).get()
        if not user_ref.exists:
            return jsonify({"error": "User not found"}), 404

        session_docs = db.collection("users").document(user_id).collection("session_data").stream()
        
        results = []
        session_count = 0

        for session in session_docs:
            session_id = session.id
            session_data = session.to_dict()
            session_data["session_id"] = session_id  # Store session ID

            print(f"Session Found: {session_id}, Data: {session_data}")

            # Fetch bowler entries inside this session
            bowler_entries = session.reference.collection("bowler_entries").stream()
            bowler_list = [entry.to_dict() for entry in bowler_entries]

            # print(f"Bowler Entries in Session {session_id}: {bowler_list}")

            if bowler_list:
                session_data["bowler_entries"] = bowler_list
                results.append(session_data)

            session_count += 1

        if session_count == 0:
            print("No session data found for this user.")
            return jsonify({"message": "No predictions found for this user"}), 200

        return jsonify(results)

    except Exception as e:
        print(f"Error fetching predictions: {e}")
        return jsonify({"error": "An error occurred while fetching predictions"}), 500