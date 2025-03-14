from flask import Flask,render_template, request, jsonify
import pandas as pd
import uuid
import datetime
import firebase_admin
from firebase_admin import credentials, firestore, auth
from model import predict_new_bowler, calculate_bowling_kpis, normalize_and_log_transform
from flask_cors import CORS

app = Flask(__name__, template_folder="templates")
CORS(app)

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



@app.route('/store_prediction', methods=['POST'])
def store_prediction():
    data = request.json
    user_id = data["user_id"]
    bowler_name = data["bowler_name"]
    phase = data["phase"]
    predicted_cluster = data["predicted_cluster"]
    dppi_score = data["dppi_score"]
    feature_importance = data.get("feature_importance", [])  # Add feature importance data

    # **Step 1: Remove Duplicates from Feature Importance Data**
    unique_feature_importance = []
    seen_features = set()
    for feature in feature_importance:
        if feature["Feature"] not in seen_features:
            unique_feature_importance.append(feature)
            seen_features.add(feature["Feature"])

    # **Step 2: Check for an Existing Session Created Today**
    today = datetime.datetime.utcnow().date()  # Get current UTC date
    user_sessions = db.collection("users").document(user_id).collection("session_data").stream()

    existing_session_id = None
    for session in user_sessions:
        session_data = session.to_dict()
        session_date = session_data.get("created_at", None)

        if session_date:
            session_date = session_date.date()  # Convert to date only
            if session_date == today:
                existing_session_id = session.id
                break  # Stop searching, we found a session for today

    # **Step 3: If No Session Exists, Create a New One**
    if not existing_session_id:
        session_id = str(uuid.uuid4())  # Generate a unique Session ID
        session_ref = db.collection("users").document(user_id).collection("session_data").document(session_id)
        session_ref.set({"created_at": datetime.datetime.utcnow()})  # Create the new session
        print(f"🆕 New session created: {session_id}")
    else:
        session_id = existing_session_id  # Use the existing session ID
        print(f"🔄 Using existing session: {session_id}")

    # **Step 4: Check if Bowler Already Exists in This Session**
    session_ref = db.collection("users").document(user_id).collection("session_data").document(session_id)
    bowler_entries = session_ref.collection("bowler_entries").where("bowler_name", "==", bowler_name).stream()

    existing_bowler_id = None
    for entry in bowler_entries:
        existing_bowler_id = entry.id
        break  # Stop after finding the first matching entry

    # **Step 5: Update or Add Bowler Entry**
    bowler_entry = {
        "bowler_name": bowler_name,
        "phase": phase,
        "predicted_cluster": predicted_cluster,
        "dppi_score": dppi_score,
        "feature_importance": unique_feature_importance,  # Use unique feature importance data
        "created_at": datetime.datetime.utcnow()
    }

    if existing_bowler_id:
        # ✅ Update Existing Bowler Entry
        session_ref.collection("bowler_entries").document(existing_bowler_id).update(bowler_entry)
        print(f"🔄 Updated existing bowler entry: {bowler_name} in session {session_id}")
        message = "Bowler data updated successfully"
    else:
        # ✅ Add New Bowler Entry
        session_ref.collection("bowler_entries").add(bowler_entry)
        print(f"✅ Bowler Entry Stored in Session {session_id}: {bowler_entry}")
        message = "Bowler data stored successfully"

    return jsonify({"message": message, "session_id": session_id})


@app.route('/get_predictions', methods=['GET'])
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

            print(f"Bowler Entries in Session {session_id}: {bowler_list}")

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


@app.route('/get_user_performance', methods=['GET'])
def get_user_performance():
    user_id = request.args.get("user_id")

    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    # 🚀 **Fix: Strip spaces and newline characters**
    user_id = user_id.strip()

    # Check if user exists
    user_ref = db.collection("users").document(user_id).get()
    if not user_ref.exists:
        return jsonify({"error": "User not found"}), 404

    session_docs = db.collection("users").document(user_id).collection("session_data").stream()

    dppi_totals = {"Powerplay": 0, "MiddleOvers": 0, "DeathOvers": 0}
    bowler_scores = {}  # Dictionary to store bowler-wise DPPI scores
    highest_dppi_bowler = None
    highest_dppi_score = 0
    found_data = False  # Flag to check if we have bowler data

    for session in session_docs:
        bowler_entries = session.reference.collection("bowler_entries").stream()
        for entry in bowler_entries:
            entry_data = entry.to_dict()
            
            # Ensure the required keys exist before processing
            if "phase" not in entry_data or "dppi_score" not in entry_data or "bowler_name" not in entry_data:
                continue

            phase = entry_data["phase"]
            bowler_name = entry_data["bowler_name"]
            dppi_score = entry_data["dppi_score"]

            # **Step 1: Add to phase-wise DPPI totals**
            if phase in dppi_totals:
                dppi_totals[phase] += dppi_score
                found_data = True

            # **Step 2: Aggregate DPPI scores per bowler**
            if bowler_name in bowler_scores:
                bowler_scores[bowler_name] += dppi_score
            else:
                bowler_scores[bowler_name] = dppi_score

            # **Step 3: Track Highest DPPI Score Bowler**
            if dppi_score > highest_dppi_score:
                highest_dppi_score = dppi_score
                highest_dppi_bowler = bowler_name

    # **Step 4: Rank Bowlers by DPPI Score**
    ranked_bowlers = sorted(bowler_scores.items(), key=lambda x: x[1], reverse=True)

    # **Step 5: Format Results for API Response**
    ranked_bowler_list = [{"bowler_name": bowler, "total_dppi_score": score} for bowler, score in ranked_bowlers]

    if not found_data:
        return jsonify({"message": "No DPPI data found for this user"}), 200

    return jsonify({
        "powerplay_total_dppi": dppi_totals["Powerplay"],
        "middle_overs_total_dppi": dppi_totals["MiddleOvers"],
        "death_overs_total_dppi": dppi_totals["DeathOvers"],
        "highest_dppi_bowler": highest_dppi_bowler,
        "highest_dppi_score": highest_dppi_score,
        "ranked_bowlers": ranked_bowler_list  
    })

@app.route('/get_single_bowler_performance', methods=['GET'])
def get_bowler_performance():
    user_id = request.args.get("user_id")
    bowler_name = request.args.get("bowler_name")

    if not user_id or not bowler_name:
        return jsonify({"error": "User ID and Bowler Name are required"}), 400

    user_id = user_id.strip()
    bowler_name = bowler_name.strip()

    # Check if user exists
    user_ref = db.collection("users").document(user_id).get()
    if not user_ref.exists:
        return jsonify({"error": "User not found"}), 404

    session_docs = db.collection("users").document(user_id).collection("session_data").stream()

    bowler_dppi_total = 0
    bowler_phase_dppi = {"Powerplay": 0, "MiddleOvers": 0, "DeathOvers": 0}
    found_data = False

    for session in session_docs:
        bowler_entries = session.reference.collection("bowler_entries").stream()
        for entry in bowler_entries:
            entry_data = entry.to_dict()

            if entry_data.get("bowler_name") == bowler_name:
                phase = entry_data["phase"]
                dppi_score = entry_data["dppi_score"]

                # Add to bowler's total DPPI
                bowler_dppi_total += dppi_score
                bowler_phase_dppi[phase] += dppi_score
                found_data = True

    if not found_data:
        return jsonify({"message": f"No DPPI data found for bowler {bowler_name}"}), 200

    return jsonify({
        "bowler_name": bowler_name,
        "total_dppi_score": bowler_dppi_total,
        "powerplay_dppi": bowler_phase_dppi["Powerplay"],
        "middle_overs_dppi": bowler_phase_dppi["MiddleOvers"],
        "death_overs_dppi": bowler_phase_dppi["DeathOvers"]
    })

@app.route('/get_user_rankings', methods=['GET'])
def get_user_rankings():
    user_id = request.args.get("user_id")

    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    user_id = user_id.strip()

    # Check if user exists
    user_ref = db.collection("users").document(user_id).get()
    if not user_ref.exists:
        return jsonify({"error": "User not found"}), 404

    session_docs = db.collection("users").document(user_id).collection("session_data").stream()

    bowler_scores = {}  # Dictionary to store total DPPI scores per bowler
    found_data = False

    for session in session_docs:
        bowler_entries = session.reference.collection("bowler_entries").stream()
        for entry in bowler_entries:
            entry_data = entry.to_dict()

            if "bowler_name" not in entry_data or "dppi_score" not in entry_data:
                continue

            bowler_name = entry_data["bowler_name"]
            dppi_score = entry_data["dppi_score"]

            if bowler_name in bowler_scores:
                bowler_scores[bowler_name] += dppi_score
            else:
                bowler_scores[bowler_name] = dppi_score

            found_data = True

    if not found_data:
        return jsonify({"message": "No DPPI data found for this user"}), 200

    # Rank bowlers by total DPPI score
    ranked_bowlers = sorted(bowler_scores.items(), key=lambda x: x[1], reverse=True)
    ranked_bowler_list = [{"bowler_name": bowler, "total_dppi_score": score} for bowler, score in ranked_bowlers]

    return jsonify({
        "ranked_bowlers": ranked_bowler_list
    })

if __name__ == '__main__':
    app.run(debug=True)

