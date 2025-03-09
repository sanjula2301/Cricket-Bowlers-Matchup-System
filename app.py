from flask import Flask, request, jsonify
import pandas as pd
from model import predict_new_bowler, calculate_bowling_kpis, normalize_and_log_transform  # Ensure correct import

app = Flask(__name__)

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

if __name__ == '__main__':
    app.run(debug=True)
