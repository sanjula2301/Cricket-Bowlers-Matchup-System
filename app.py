from flask import Flask, request, jsonify
import pandas as pd
import uuid
import datetime
import firebase_admin
from firebase_admin import credentials, firestore, auth
from model import predict_new_bowler, calculate_bowling_kpis, normalize_and_log_transform

app = Flask(__name__)

# Load Firebase credentials
cred = credentials.Certificate("C:/Users/sanju/OneDrive/Documents/iit lectures/Final Year 1st Sem/Flask/final-year-project-1f05b-firebase-adminsdk-fbsvc-fa21fb3ad9.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Paths for datasets and feature importance files
dataset_paths = {
    "Powerplay": "C:/Users/sanju/OneDrive/Documents/iit lectures/Final Year 1st Sem/Flask/Cluster Results and Other data files/WeightedDataSetPowerplay_Clusters.csv",
    "MiddleOvers": "C:/Users/sanju/OneDrive/Documents/iit lectures/Final Year 1st Sem/Flask/Cluster Results and Other data files/WeightedDataSetMiddleovers_Clusters.csv",
    "DeathOvers": "C:/Users/sanju/OneDrive/Documents/iit lectures/Final Year 1st Sem/Flask/Cluster Results and Other data files/WeightedDataSetDeath_Clusters.csv"
}

feature_importance_paths = {
    "Powerplay": "C:/Users/sanju/OneDrive/Documents/iit lectures/Final Year 1st Sem/Flask/Cluster Results and Other data files/Powerplay_Feature_Importance.csv",
    "MiddleOvers": "C:/Users/sanju/OneDrive/Documents/iit lectures/Final Year 1st Sem/Flask/Cluster Results and Other data files/MiddleOvers_Feature_Importance.csv",
    "DeathOvers": "C:/Users/sanju/OneDrive/Documents/iit lectures/Final Year 1st Sem/Flask/Cluster Results and Other data files/DeathOvers_Feature_Importance.csv"
}

# Load and process datasets at startup
training_data = {}
feature_importance_data = {}

for phase, path in dataset_paths.items():
    try:
        df = pd.read_csv(path)
        df_transformed = calculate_bowling_kpis(df)
        df_transformed = normalize_and_log_transform(df_transformed)
        training_data[phase] = df_transformed

        # Load corresponding feature importance file
        feature_importance_data[phase] = pd.read_csv(feature_importance_paths[phase])
    except FileNotFoundError as e:
        print(f"Error: {e}. Ensure files exist at specified paths.")


@app.route('/')
def home():
    return "Bowler Performance Prediction API Running!"


# ========================== 1️⃣ USER AUTHENTICATION ENDPOINTS ==========================

# **1. User Signup**
@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    try:
        user = auth.create_user(
            email=data["email"],
            password=data["password"],
            display_name=data["username"]
        )
        db.collection("users").document(user.uid).set({
            "username": data["username"],
            "email": data["email"],
            "created_at": datetime.datetime.utcnow(),
            "total_dppi_score": 0
        })
        return jsonify({"message": "User created successfully", "user_id": user.uid})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# **2. User Login (Returns User ID)**
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    try:
        user = auth.get_user_by_email(data["email"])
        return jsonify({"user_id": user.uid})
    except Exception as e:
        return jsonify({"error": "Invalid credentials"}), 400


# **3. Fetch User Details**
@app.route('/get-user', methods=['GET'])
def get_user():
    user_id = request.args.get("user_id")
    user_ref = db.collection("users").document(user_id).get()

    if not user_ref.exists:
        return jsonify({"error": "User not found"}), 404

    return jsonify(user_ref.to_dict())


# ========================== 2️⃣ BOWLER PREDICTION ENDPOINTS ==========================

# **4. Bowler Prediction**
@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    if not data or "phase" not in data:
        return jsonify({"error": "Please provide match phase (Powerplay, MiddleOvers, DeathOvers) and player stats"}), 400

    phase = data["phase"]
    if phase not in training_data:
        return jsonify({"error": "Invalid match phase. Choose from Powerplay, MiddleOvers, DeathOvers"}), 400

    try:
        result = predict_new_bowler(phase, data, training_data[phase], feature_importance_data[phase])
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# **5. Store Bowler Prediction Data**
@app.route('/store_prediction', methods=['POST'])
def store_prediction():
    data = request.json
    user_id = data["user_id"]
    bowler_name = data["bowler_name"]
    phase = data["phase"]
    predicted_cluster = data["predicted_cluster"]
    dppi_score = data["dppi_score"]

    session_id = str(uuid.uuid4())  # Generate Session ID

    bowler_entry = {
        "bowler_name": bowler_name,
        "phase": phase,
        "predicted_cluster": predicted_cluster,
        "dppi_score": dppi_score,
        "created_at": datetime.datetime.utcnow()
    }

    # Store Data in Firestore
    session_ref = db.collection("users").document(user_id).collection("session_data").document(session_id)
    session_ref.collection("bowler_entries").add(bowler_entry)

    return jsonify({"message": "Bowler data stored successfully", "session_id": session_id})


# **6. Retrieve User's Past Predictions**
@app.route('/get_user_predictions', methods=['GET'])
def get_user_predictions():
    user_id = request.args.get("user_id")
    session_docs = db.collection("users").document(user_id).collection("session_data").stream()

    results = []
    for session in session_docs:
        session_data = session.to_dict()
        session_data["bowler_entries"] = [
            doc.to_dict() for doc in session.reference.collection("bowler_entries").stream()
        ]
        results.append(session_data)

    return jsonify(results)



# **7. Retrieve Aggregated DPPI Score**
@app.route('/get_user_performance', methods=['GET'])
def get_user_performance():
    user_id = request.args.get("user_id")
    session_docs = db.collection("users").document(user_id).collection("session_data").stream()

    dppi_totals = {"Powerplay": 0, "MiddleOvers": 0, "DeathOvers": 0}
    highest_dppi_bowler = None
    highest_dppi_score = 0

    for session in session_docs:
        bowler_entries = session.reference.collection("bowler_entries").stream()
        for entry in bowler_entries:
            entry_data = entry.to_dict()
            dppi_totals[entry_data["phase"]] += entry_data["dppi_score"]

            if entry_data["dppi_score"] > highest_dppi_score:
                highest_dppi_score = entry_data["dppi_score"]
                highest_dppi_bowler = entry_data["bowler_name"]

    return jsonify({
        "powerplay_total_dppi": dppi_totals["Powerplay"],
        "middle_overs_total_dppi": dppi_totals["MiddleOvers"],
        "death_overs_total_dppi": dppi_totals["DeathOvers"],
        "highest_dppi_bowler": highest_dppi_bowler,
        "highest_dppi_score": highest_dppi_score
    })


if __name__ == '__main__':
    app.run(debug=True)

